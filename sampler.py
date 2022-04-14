import numpy as np
import os
from scapy.all import wrpcap

MATLAB = None  # MATLAB engine only populated if waveform generation is required
HW_ADDR_MAP = {}


class PcapRecorder:
    def __init__(self, out_dir, n_store):
        self.n_store = n_store
        self.packets = []
        self.name_template = os.path.join(out_dir, "seq%04d.pcap")
        self.seqno = 0

    def append(self, pkt):
        self.packets.append(pkt)
        if len(self.packets) >= self.n_store:
            self.save_and_reset()

    def save_and_reset(self):
        outfile = self.name_template % self.seqno
        wrpcap(outfile, self.packets)

        self.packets = []
        self.seqno += 1


def get_pkt_property(record, property_name):
    if property_name == "~phy":
        return record[1]
    try:
        return record[0].__getattribute__(property_name)
    except AttributeError:
        return None


class FeatureCollector:
    def __init__(self, property_name, agg_method, property_map=None):
        """
        """
        self.property_name = property_name
        self.agg_method = agg_method
        if property_map is None:
            property_map = lambda x: x  # Leave the input value unchanged
        self.property_map = property_map

    def __call__(self, records, ret=None):
        if ret is None:
            ret = []

        new_data = [get_pkt_property(record, self.property_name) for record in records]
        new_data_mapped = [v for v in map(self.property_map, new_data) if v is not None]
        new_feature = self.agg_method(new_data_mapped)
        ret.append(new_feature)
        return records, ret


class SampleCollector:
    def __init__(self, feature_collectors, use_phy=False):
        self.fcs = feature_collectors
        self.use_phy = use_phy

    def __call__(self, packets):
        """
        Converts a list of packets into the format expected by feature
        collectors.
        Returns the converted packets (as (packet, phy_signal) tuples) and the
        features that were collected
        """
        records = packets_to_records(packets, self.use_phy)

        ret = []
        for fc in self.fcs:
            _, ret = fc(records, ret)
        return records, ret


def packets_to_records(packets, use_phy):
    records = []
    for i, pkt in enumerate(packets):
        if use_phy:
            paired_data = generate_waveform(pkt)
        else:
            paired_data = None
        records.append((pkt, paired_data))
    return records


def get_node_tx_record(node):
    args = {
        'ChannelBandwidth': 'CBW160', # 160 MHz channel bandwidth
        'NumTransmitAntennas': 1.0,   # 1 transmit antenna
        'NumSpaceTimeStreams': 1.0,   # 1 space-time stream
        'MCS': 1.0,                   # Modulation: QPSK Rate: 1/2
        'idleTime': 20e-6,            # 20 microseconds idle period after packet
        'oversamplingFactor': 1.5,    # Oversample waveform 1.5x nominal baseband rate
        'FrameFormat': 'VHT',         # MAC frame format
        'postProcFunc': '@(x, a) x'   # Post processing MATLAB function. Note: this args dict is passed as the second param
    }
    args.update(node.config['tx_config'])
    hw_addr = node.config['hw_addr']
    return {hw_addr: args}

def get_node_tx_desc(pkt):
    """
    Retrieves the tx description for the node that sent the given packet.
    This data is obtained using the packet's source mac address.
    """
    return HW_ADDR_MAP[pkt.src]

def init_waveform_gen(seed, nodes):
    import matlab.engine
    global MATLAB
    MATLAB = matlab.engine.start_matlab()
    MATLAB.rng(seed)

    for node in nodes:
        HW_ADDR_MAP.update(get_node_tx_record(node))  # Record node details mapping traffic to Tx properties


def generate_waveform(pkt):
    args = get_node_tx_desc(pkt)
    return _generate_waveform(pkt.build(), args)


def _generate_waveform(msdu, args):
    """
    Helper function that generates a physical signal waveform using MATLAB
    """
    args['MSDU'] = msdu
    return np.array(MATLAB.generateWaveform(args)).squeeze()
