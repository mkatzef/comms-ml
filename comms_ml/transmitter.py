"""
The basic unit representing a device in the comms_ml simulator.
"""

import numpy as np
import random
import codecs
import os
from scapy.all import wrpcap, Ether, IP, UDP, TCP, Raw

from .traffic_models import get_traffic_model
from .sim_common import *


class Transmitter:
    """
    The transmitter class.
    Stores node configuration data as well as the time and data for the very
    next packet, as used in the simulator.

    **Note**: Only one traffic source per device is currently honoured. Adding
    more than one traffic source can result in concurrent transmissions.
    """
    def __init__(self, config, traffic_descs, sim_time_s=None, rate_Bps=1e6, message_cache=None):
        self.config = config

        # TODO: add support for multiple traffics
        if len(traffic_descs) > 1:
            print("NOTE: only first traffic for each node will be used")
        elif len(traffic_descs) == 0:
            self.tx_start_time = np.inf
            self.is_active = False
            return
        self.traffic_config = traffic_descs[0]
        model_desc = self.traffic_config['model']
        try:
            traffic = get_traffic_model(sim_time_s=sim_time_s, **model_desc)
        except NameError as ne:
            print("Encountered:", ne, "trying eval...")
            traffic = eval(model_desc)
            print("Succeeded")

        self.packet_source = eval(self.traffic_config['packet_source'])

        self.rate_Bps = rate_Bps
        self.message_cache = message_cache or []

        self.tx_start_time = None
        self.tx_duration = None
        self.msg_len_bits = None
        self.traffic_source = traffic or TrafficSourceBursty()
        self.prepare_next_message(0)

        self.is_active = False
        self.prev_occupancy = None

    def is_active(self, sim_time):
        return self.is_active

    def plot(self):
        pos = self.config['pos'][:2]
        s = plt.scatter(*pos)
        color = s.get_facecolors()[0]

        if self.prev_occupancy is not None:
            self.prev_occupancy.remove()
        occupancy = matplotlib.patches.Circle(pos, radius=10, color=color, alpha=0.3, fill=self.is_active)
        self.prev_occupancy = plt.gca().add_patch(occupancy)

    def get_tx_start_time(self):
        return self.tx_start_time

    def start(self, sim_time, cache_message=False):
        """ Returns next end time. """
        self.is_active = True
        end_time = sim_time + self.tx_duration

        if cache_message:
            msg = self.packet_source(sim_time, self.msg_len_bits, self.config, self.traffic_config)
            self.message_cache.append(msg)
        return end_time

    def end(self, sim_time):
        """ Returns next start time. """
        self.is_active = False
        self.prepare_next_message(sim_time)
        return self.tx_start_time

    def prepare_next_message(self, sim_time):
        tx_start_time, msg_len_bits = self.traffic_source.prepare_next_message(sim_time)
        self.tx_start_time = tx_start_time
        self.tx_duration = msg_len_bits / self.rate_Bps
        self.msg_len_bits = max(8, msg_len_bits)


def get_udp_packet(rec_time, msg_len_bits, node_cfg, traffic_cfg):
    """
    Example packet formatter for UDP packets with a given configuration
    """
    payload = ('%%0%dx' % (msg_len_bits//4)) % random.getrandbits(msg_len_bits)
    payload = codecs.decode(payload.encode(), 'hex')

    dmac, dip, dport, sport = traffic_cfg['dst']
    pkt =   Ether(src=node_cfg['hw_addr'], dst=dmac)/ \
            IP(src=node_cfg['ip_addr'], dst=dip)/ \
            UDP(sport=sport, dport=dport)/ \
            Raw(load=payload)
    pkt.time = rec_time
    return pkt
