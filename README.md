# Comms ML
Simulates Wi-Fi devices to generate realistic network traces and *their underlying wireless signals* for machine learning applications.

## Requirements
Requires:  
* python3 with numpy, scipy, matplotlib, scapy  
* MATLAB R2019a or later  
* MATLAB's Wireless Toolbox  
* [MATLAB Engine API for Python](https://au.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html)  

## Usage
**NOTE**: Documentation coming soon! Below is a quick summary.  

Simulation and feature collection is performed by `comms-ml.py` based on the two configuration files:  
1. `simconfig.json`  
2. `samplingconfig.json`  
The above two files act as an example of the options made available by the simulator, which is run using the command:  
`python3 comms-ml.py`  
