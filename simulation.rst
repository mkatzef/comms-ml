Simulation
==========

Structure
---------

``comms_ml`` includes a finite event-based simulator to generate rudimentary network traffic that is representative of real-world scenarios.
The output of this simulator is a set of PCAP files containing the packets that were exchanged throughout the network for a given simulation duration.
If such a PCAP files is already available (which may occur if activity has been previously recorded), the simulation instead acts as an interface between existing PCAPs and the sampling component.


Parameters
----------

A ``comms_ml`` simulation is defined by a series of parameters inside of a JSON-formatted configuration file.

The required properties of this JSON file are shown in the following example (with some possible values)::

  {
    "general": {
      "rng_seed": 1234,
      "sim_time_s": 1000,
      "output_pcap_dir": "./pcaps/",
      "pcap_max_size": 10000
    },
    "nodes": []
  }

In this example, we see two key components - general information, and a (currently empty) array of nodes.
The general information contains values for the random number generator seed, simulation duration, output directory, and maximum number of packets per PCAP file.


Nodes
-----

The fundamental unit in each `comms_ml` simulation is the node - a communications device (typically using WLAN).
Each node is defined as a JSON object that specifies its communication interfaces and behaviours.

An example node (with all of the simulator-supported options shown) is the following::

  {
    "config": {
      "hw_addr": "aa:aa:aa:aa:aa:aa",
      "ip_addr": "192.168.1.2",
      "pos_xyz": [0, 0, 0],
      "tx_config": {
        "ChannelBandwidth": "CBW160",
        "NumTransmitAntennas": 1.0,
        "NumSpaceTimeStreams": 1.0,
        "MCS": 1.0,
        "idleTime": 20e-6,
        "oversamplingFactor": 1.5,
        "FrameFormat": "VHT",
        "postProcFunc": "@(x, a) x"
      }
    },
    "traffic": [
      {
        "dst": ["bb:bb:bb:bb:bb:bb", "192.168.1.3", 8080, 10234],
        "model": {
          "traffic_type": "hawkes",
          "tx_len_min_bytes": 1,
          "tx_len_max_bytes": 1500,
          "arg_bursty_n": 5,
          "arg_bursty_intra": [0.01, 0.07],
          "arg_bursty_inter": [0.1, 5],
          "arg_hawkes": 0.15,
          "weekend_mult": 0.5
        },
        "packet_source": "get_udp_packet"
      }
    ]
  }

Each node can have 0 or more traffic descriptions that specify the destination for generated packets and the distribution function of packets being generated.

**Note**: the ``tx_config`` property is passed directly to MATLAB if using MATLAB-based physical signal generation. If any custom MATLAB processing is required, additional data may be passed to said processing by adding ``key: value`` pairs to the ``tx_config`` property.
