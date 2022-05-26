Quick Start
===========

Overview
--------
Simulation and feature collection is performed by ``comms-ml`` based on the two configuration files:
  #. ``simconfig.json``
  #. ``samplingconfig.json``

The paths to these two files are the only required arguments to the simulator, which may be called using:
``python3 launch.py [-h] [--silent] sim_config sampling_config``

Example
-------
The ``./configs/`` directory contains several example network configurations based on the following two files::

  configs/
  ├── simconfig.json
  └── samplingconfig.json

The above two files act as an example of the options made available by the simulator. To run the simulator using the above:
  #. Open a terminal and navigate to this repository's directory.
  #. Run ``python3 launch.py configs/simconfig.json configs/samplingconfig.json``
The rest of the simulation options (*including output directories*) are defined in the configuration files themselves.

The simulator will:
  #. Prompt you to continue if any files would be overwritten
  #. Write PCAP files for the duration of the simulation (e.g., to ``./out/pcaps``)
  #. Write features from the simulation (including generating physical signals using MATLAB if requested by configuration files)

The output ``.pcap`` files may be analyzed in standard tools such as Wireshark.
The output ``.npy`` samples can be loaded in python using ``numpy.load('samples.npy', allow_pickle=True)``
