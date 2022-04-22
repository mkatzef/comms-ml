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
    parser.add_argument("--verbosity", help="increase output verbosity")

    args = parser.parse_args()

    comms_ml.simulator.logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    sim_config_file = args.sim_config
    sampling_config_file = args.sampling_config

    # Simulation structure
    with open(sim_config_file, 'r') as sim_infile:
        sim_dict = json.load(sim_infile)

    # Sampling properties
    with open(sampling_config_file, 'r') as sampling_infile:
        sampling_dict = json.load(sampling_infile)

    print("Starting simulation...")
    pcap_dir = comms_ml.simulator.run_sim(sim_dict)  # Writes PCAP files to the returned directory

    print("Collecting samples from traffic...")
    #TODO move to comms_ml.sampler
    samples, samples_filename = comms_ml.simulator.collect_features(pcap_dir, sampling_dict)

    # Write feature file
    print("Saving", len(samples), "samples to", samples_filename)
    np.save(samples_filename, np.array(samples, dtype=object))
