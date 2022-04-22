"""
simulator.py - produce communcication traces for machine learning applications.

Use this tool to:
* Generate PCAP files based on transmitter activity
"""

import argparse
import json
import logging
import numpy as np
import scipy.io
import matplotlib
import matplotlib.pyplot as plt
import random
import codecs
import heapq
import os
import sys
from scapy.all import wrpcap, rdpcap

from . import sampler
from .sampler import FeatureCollector, SampleCollector, PcapRecorder
from . import aggregators
from .transmitter import Transmitter
from .sim_common import *


def plot_scene(tx_list, bl=(0,0), tr=(100,100)):
    for tx in tx_list:
        tx.plot()

    plt.xlabel("x (m)")
    plt.ylabel("y (m)")
    plt.xlim((bl[0], tr[0]))
    plt.ylim((bl[1], tr[1]))
    plt.gca().axis("equal")


def play_status_changes(status_changes, tx_list):
    """ An animated visual representation """
    n_tx = len(tx_list)
    for i in range(n_tx):
        tx_list[i].is_active = False

    fig = plt.figure()
    fignum = fig.number
    for current_time, dev_index, status in status_changes:
        if not plt.fignum_exists(fignum):
            break
        tx_list[dev_index].is_active = (status == MSG_START)

        plot_scene(tx_list)
        plt.title("Sim time: %.2f s" % current_time)
        plt.pause(0.05)

    plt.show()


class CircularBuffer:
    def __init__(self, bufflen):
        self.bufflen = bufflen
        self.buffer = [0] * bufflen
        self.buffer_pointer = 0

    def add(self, val):
        self.buffer[self.buffer_pointer] = val
        self.buffer_pointer = self.buffer_pointer + 1
        if self.buffer_pointer >= self.bufflen:
            self.buffer_pointer = 0
            return True
        else:
            return False

    def get_buffer_raw(self):
        return self.buffer[:]

    def get_buffer_linear(self):
        """ Returns the inner buffer rotated such that the oldest sample is at
        position 0. """
        return self.buffer[self.buffer_pointer :] + self.buffer[: self.buffer_pointer]


def get_status_change_density(status_changes, increments=[7, 24], min_increment_s=60*60):
    results = []

    sample_buffers = [CircularBuffer(i) for i in increments]
    initialized = False
    n_increments = len(increments)
    def add_increment(increment_val):
        """ Adds the newest increment to the LSB. If this completes the LSB's
        buffer, the sum of this buffer is added to the next most significant bit """
        inc_ind = n_increments - 1
        val = increment_val
        while sample_buffers[inc_ind].add(val):
            if inc_ind == 0:
                return True  # Initialized
            val = sum(sample_buffers[inc_ind].get_buffer_raw())
            inc_ind -= 1
        return False

    min_increment_sample = 0
    min_increment_end = min_increment_s
    for change_time, _, status in status_changes:
        if status == MSG_STOP:
            continue

        if change_time >= min_increment_end:
            while change_time >= min_increment_end:
                initialized = add_increment(min_increment_sample) or initialized
                min_increment_sample = 0
                min_increment_end += min_increment_s

                if initialized:
                    # record as a sample
                    sample = []
                    for buf in sample_buffers:
                        sample += buf.get_buffer_linear()
                    results.append(sample)
        min_increment_sample += 1
    return results


def plot_status_timeline(status_changes, n_tx):
    """ A static visual representation """
    dev_change_times = [[0] for _ in range(n_tx)]
    dev_levels = [[0] for _ in range(n_tx)]

    max_sim_time = 0
    min_sim_time = status_changes[0][0]
    for change_time, dev_index, status in status_changes:
        dev_change_times[dev_index] += [change_time, change_time]  # Plot step as two y vals at same x
        dev_levels[dev_index] += [status != MSG_START, status == MSG_START]  # Treat MSG_START as high

        if change_time > max_sim_time:
            max_sim_time = change_time

    for i in range(n_tx):
        plt.subplot(n_tx, 1, i+1)
        plt.plot(dev_change_times[i] + [max_sim_time], dev_levels[i] + [dev_levels[i][-1]])
        plt.xlim([min_sim_time, max_sim_time])
        plt.ylabel("Tx %d" % i)

        if i == 0:
            plt.title("Transmitter activity")

    plt.xlabel("Sim time (s)")


def get_features(status_changes, n_tx, timescale_s=0.1, n_channels=None, tx_map=None):
    """ Generates feature vectors from activity trace.
    Initially made to collect average IAT for each channel.
    tx_map (optional) is {tx_index : channel_index}
    """
    if n_channels is None:
        n_channels = n_tx
        assert tx_map is None, "tx_map specifies custom tx:channel but n_channels not specified."

    if tx_map is None:
        tx_map = dict((i, i) for i in range(n_tx))

    channel_last_on_time = np.zeros((n_channels,))
    n_active_tx = np.zeros((n_channels,))  # number of transmitters active

    sample_list = []
    sample = np.zeros((n_channels,))
    count_list = []
    counts = np.zeros((n_channels,))
    last_sample_time = status_changes[0][0]

    for change_time, dev_index, status in status_changes:
        channel_index = tx_map[dev_index]

        if status == MSG_START:
            counts[channel_index] += 1
            if n_active_tx[channel_index] == 0:  # was inactive
                duration_inactive = change_time - max(last_sample_time, channel_last_on_time[channel_index])
                sample[channel_index] += duration_inactive
            n_active_tx[channel_index] += 1
        else:
            n_active_tx[channel_index] -= 1
            if n_active_tx[channel_index] == 0:
                channel_last_on_time[channel_index] = change_time

        if change_time - last_sample_time >= timescale_s:
            next_sample_time = last_sample_time + timescale_s
            # if inactive at time of sample, add remainder to inactive count
            for ci in range(n_channels):
                if n_active_tx[ci] == 0:
                    sample[ci] += min(timescale_s, next_sample_time - channel_last_on_time[ci])

            sample_list.append(np.maximum(0, timescale_s - sample))
            count_list.append(counts)
            last_sample_time = next_sample_time
            sample = np.zeros((n_channels,))
            counts = np.zeros((n_channels,))

    return sample_list, count_list


def plot_samples(exp_dir="./data"):
    for exp_name in sorted(next(os.walk(exp_dir))[2]):
        if exp_name.startswith("exp"):
            filename = os.path.join(exp_dir, exp_name)
            samples = np.load(filename, allow_pickle=True)
            plt.figure()
            plt.plot(samples[0])
            plt.show()


def create_nodes(node_descs, sim_time_s=None, message_cache=None):
    nodes = []
    for nd in node_descs:
        config = nd["config"]
        traffic_descs = nd["traffic"]

        new_node = Transmitter(
            config,
            traffic_descs=traffic_descs,
            message_cache=message_cache,
            sim_time_s=sim_time_s
        )
        nodes.append(new_node)
    return nodes


def get_sample_collector(feature_descs, use_phy=False):
    feature_collectors = []
    for fd in feature_descs:
        property_name = fd["property"]
        agg_function = eval(fd["agg_function"])
        mf = fd["map_function"]
        property_map = eval(mf) if mf is not None else lambda x: x
        fc = FeatureCollector(property_name, agg_function, property_map)
        feature_collectors.append(fc)
    return SampleCollector(feature_collectors, use_phy=use_phy)


def _run(max_sim_time, tx_list, verbose=False, save_final=True):
    """ Simulation core event loop """
    event_queue = []  # time: (device, action)
    def q_push(priority, item):
        heapq.heappush(event_queue, (priority, item))
    def q_pop():
        return heapq.heappop(event_queue)

    for i, tx in enumerate(tx_list):
        q_push(tx.get_tx_start_time(), (i, MSG_START))

    status_change_lists = []  # (time, device, status)
    status_change_cache = []  # (time, device, status)

    current_time = 0
    print_counter = 0
    while current_time < max_sim_time and len(event_queue) > 0:
        current_time, (dev_index, action) = q_pop()
        # Each sample has a corresponding status_change_list and message list in each transmitter
        assert action in [MSG_START, MSG_STOP], "Unrecognized action: " + str(action)

        status_change_cache.append((current_time, dev_index, action))

        if action == MSG_START:
            end_time = tx_list[dev_index].start(current_time, cache_message=True)
            q_push(end_time, (dev_index, MSG_STOP))
        elif action == MSG_STOP:
            start_time = tx_list[dev_index].end(current_time)
            if start_time is not None:
                q_push(start_time, (dev_index, MSG_START))
        else:
            raise Exception("Action value: {}".format(action))
        if verbose:
            print_counter += 1
            if print_counter >= 1000:
                print_counter = 0
                print(" Progress: %3d%%" % round(100 * current_time / max_sim_time), end="\r")
    if save_final:
        status_change_lists.append(status_change_cache)
    if verbose:
        print("\nDone")
    return status_change_lists


def run_sim(sim_dict):
    global SEED, NODES
    sim_general = sim_dict["general"]

    SEED = sim_general["rng_seed"]
    np.random.seed(SEED)
    random.seed(SEED)

    # Create pcap dir
    pcap_dir = sim_general["output_pcap_dir"]
    if os.path.exists(pcap_dir):
        input("PCAP dir already exists, press ENTER to CONTINUE...")
    else:
        os.makedirs(pcap_dir)

    pcap_max_size = sim_general["pcap_max_size"]
    message_cache = PcapRecorder(out_dir=pcap_dir, n_store=pcap_max_size)
    sim_time_s = sim_general["sim_time_s"]
    NODES = create_nodes(sim_dict["nodes"], sim_time_s=sim_time_s, message_cache=message_cache)

    status_changes = _run(sim_time_s, NODES, verbose=True)  # Saves pcaps as needed, return value unused
    message_cache.save_and_reset()
    return pcap_dir


def packets_from_dir(pcap_dir):
    pcap_names = list(sorted(next(os.walk(pcap_dir))[2]))
    for pn in pcap_names:
        packets = rdpcap(os.path.join(pcap_dir, pn))
        for packet in packets:
            yield packet


def collect_features(pcap_dir, sampling_dict):
    sampling_general = sampling_dict["general"]
    use_phy = sampling_general["use_phy"]
    if use_phy:
        sampler.init_waveform_gen(SEED, NODES)

    sample_duration_s = sampling_general["sample_duration_s"]
    sample_interval_s = sampling_general["sample_interval_s"]
    rec_pos_xyz = np.array(sampling_general["pos_xyz"])
    output_filename = sampling_general["output_name"]
    sample_collector = get_sample_collector(sampling_dict["features"], use_phy)

    # Step through pcaps, load all into memory as needed
    # Step through times, break up based on sampling interval and duration
    #  Sampling window:
    #   If sample_interval_s is given:
    #    first_sample_time + [i * sample_interval_s, i * sample_interval_s + sample_duration_s]
    #   Otherwise:
    #    first_sample_time + [i * sample_duration_s, (i+1) * sample_duration_s]
    # Pass batches of packets to the sample collector
    # Record sample collector's output for each batch
    sample_start_time = None
    sample_end_time = None
    current_sample_packets = []
    samples = []
    npkt = 0
    for packet in packets_from_dir(pcap_dir):
        pkt_time = packet.time

        # First loop
        if sample_start_time is None:
            sample_start_time = pkt_time
            sample_end_time = sample_start_time + sample_duration_s

        # Previous sample has been finalized
        if pkt_time >= sample_end_time:
            if len(current_sample_packets) > 0:
                _, new_sample = sample_collector(current_sample_packets)
                npkt += len(current_sample_packets)
                samples.append(new_sample)
                current_sample_packets = []

            # Set the new sampling window
            if sample_interval_s is not None:
                sample_start_time = sample_start_time + sample_interval_s
            else:
                sample_start_time = sample_end_time
            sample_end_time = sample_start_time + sample_duration_s

        # Record this packet if it's in the sampling window
        if sample_start_time <= pkt_time < sample_end_time:
            current_sample_packets.append(packet)
    print("Sampled a total of", npkt, "packets")
    return samples, output_filename
