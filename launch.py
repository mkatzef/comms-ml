#!/usr/bin/python3
"""
launch.py - launch a wireless network simulation and collect feature vectors,
all as specified through configuration files.

"""
import argparse
import json
import logging
import numpy as np
import sys

import comms_ml.simulator


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("sim_config", type=str, help="set sim config (JSON) path")
    parser.add_argument("sampling_config", type=str, help="set sampling config (JSON) path")
    parser.add_argument("--silent", help="silence runtime messages", action="store_true")

    args = parser.parse_args()

    log_level = logging.INFO
    if args.silent:
        log_level = logging.WARN

    logging.basicConfig(stream=sys.stdout, level=log_level)

    sim_config_file = args.sim_config
    sampling_config_file = args.sampling_config

    # Simulation structure
    with open(sim_config_file, 'r') as sim_infile:
        sim_dict = json.load(sim_infile)

    # Sampling properties
    with open(sampling_config_file, 'r') as sampling_infile:
        sampling_dict = json.load(sampling_infile)

    logging.info("Starting simulation...")
    pcap_dir = comms_ml.simulator.run_sim(sim_dict, init_only=True)  # Writes PCAP files to the returned directory

    logging.info("Collecting samples from traffic...")
    #TODO move to comms_ml.sampler
    samples, samples_filename = comms_ml.simulator.collect_features(pcap_dir, sampling_dict, progress_max_time=sim_dict['general']['sim_time_s'])

    # Write feature file
    logging.info(f"Saving {len(samples)} samples to {samples_filename}")
    np.save(samples_filename, np.array(samples, dtype=object))
