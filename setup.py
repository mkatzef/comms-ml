from setuptools import setup

DEPENDENCIES = [
	'matplotlib',
	'numpy',
	'scapy',
	'scipy'
]

setup(
   name='comms_ml',
   version='0.1',
   description='Wireless network simulator for ML',
   author='Marc Katzef',
   author_email='mkatzef@student.unimelb.edu.au',
   packages=['comms_ml'],
   install_requires=DEPENDENCIES #external packages as dependencies
)
