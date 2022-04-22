# Comms ML
Simulates wireless devices (all demos use 802.11ac) to generate realistic network traces and *their underlying wireless signals* for machine learning applications.

**NOTE**: Documentation coming soon! Below is a quick summary.  

## Installation
Required software:  
* `python3` and packages*:  
  * `numpy`, `scipy`, `matplotlib`, and `scapy`  
* For physical signal generation:  
  * MATLAB R2019a or later  
  * MATLAB's Wireless Toolbox  
  * [MATLAB Engine API for Python](https://au.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html)  

*All required python packages can be installed using `pip install .` inside this repository's root directory.

## Usage
Simulation and feature collection is performed by `comms-ml` based on the two configuration files:  
1. `simconfig.json`  
2. `samplingconfig.json`

The paths to these two files are the only required arguments to the simulator, which may be called using:  
`python3 launch.py [-h] [--silent] sim_config sampling_config`

## Example
The `./configs/` directory contains several example network configurations based on the following two files:  
```
configs/
├── simconfig.json  
└── samplingconfig.json
```  
The above two files act as an example of the options made available by the simulator. To run the simulator using the above:  
1. Open a terminal and navigate to this repository's directory.  
2. Run `python3 launch.py configs/simconfig.json configs/samplingconfig.json`  
The rest of the simulation options (*including output directories*) are defined in the configuration files themselves.

The simulator will:
1. Prompt you to continue if any files would be overwritten
2. Write PCAP files for the duration of the simulation (e.g., to `./out/pcaps`)
3. Write features from the simulation (including generating physical signals using MATLAB if requested by configuration files)

The output `.pcap` files may be analyzed in standard tools such as Wireshark
The output `.npy` samples can be loaded in python using `numpy.load('samples.npy', allow_pickle=True)`
