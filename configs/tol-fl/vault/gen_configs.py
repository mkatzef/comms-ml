import json
import random

# json compat
null = None
true = True
false = False

def get_mac():
    return ':'.join('%02x' % random.randint(0, 255) for _ in range(6))


def base_options(rep):
    return {
        "rng_seed": random.randint(1, 2048),
        "sim_time_s": 604800,
        "output_pcap_dir": f"./out{rep}/pcaps/",
        "pcap_max_size": 100000
      }


def base_node(hw_addr, pos=[0,0,0]):
    return {
        "config": {
            "hw_addr": hw_addr,
            "ip_addr": "192.168.1.2",
            "pos_xyz": pos,
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
        "traffic": []
    }


def base_traffic_config(dst_hw, traffic):
    return {
        "dst": [dst_hw, "192.168.1.3", 8080, 10234],
        "model": traffic(),
        "packet_source": "get_udp_packet"
    }


def traffic_bursty_low():
    return {
        "traffic_type": "bursty",
        "tx_len_min_bytes": 1,
        "tx_len_max_bytes": 1500,
        "arg_bursty_n": 5,
        "arg_bursty_intra": [0.01, 0.07],
        "arg_bursty_inter": [1, 120],
        "arg_hawkes": 0.15,
        "weekend_mult": 0.5
    }


def traffic_bursty_high():
    return {
        "traffic_type": "bursty",
        "tx_len_min_bytes": 1,
        "tx_len_max_bytes": 1500,
        "arg_bursty_n": 5,
        "arg_bursty_intra": [0.01, 0.07],
        "arg_bursty_inter": [1, 10],
        "arg_hawkes": 0.15,
        "weekend_mult": 0.5
    }


def traffic_hawkes_low():
    return {
        "traffic_type": "hawkes_periodic",
        "tx_len_min_bytes": 1,
        "tx_len_max_bytes": 1500,
        "arg_bursty_n": 5,
        "arg_bursty_intra": [0.01, 0.07],
        "arg_bursty_inter": [1, 3],
        "arg_hawkes": 0.15,
        "weekend_mult": 0.5
    }


def traffic_hawkes_high():
    return {
        "traffic_type": "hawkes_periodic",
        "tx_len_min_bytes": 1,
        "tx_len_max_bytes": 1500,
        "arg_bursty_n": 5,
        "arg_bursty_intra": [0.01, 0.07],
        "arg_bursty_inter": [1, 3],
        "arg_hawkes": 0.3,
        "weekend_mult": 0.5
    }


def get_sim_cfg(rep, n_bl, n_bh, n_hl, n_hh):
    dev_counts = [n_bl, n_bh, n_hl, n_hh]
    dev_funcs = [
                    traffic_bursty_low,
                    traffic_bursty_high,
                    traffic_hawkes_low,
                    traffic_hawkes_high
                ]
    n_devs = sum(dev_counts)
    dev_macs = [get_mac() for _ in range(n_devs)]
    router_mac = get_mac()

    router = base_node(router_mac)
    device_configs = list(map(base_node, dev_macs)) + [router]

    sim_dict = {
        "general": base_options(rep)
    }

    curr_type = 0
    n_curr = 0
    n_done = 0
    while curr_type < 4:
        if n_curr < dev_counts[curr_type]:
            traffic = base_traffic_config(router_mac, dev_funcs[curr_type])
            device_configs[n_done]['traffic'] = [traffic]
            n_curr += 1
            n_done += 1
        else:
            n_curr = 0
            curr_type += 1

    router['traffic'] = [base_traffic_config(dev_macs[0], traffic_bursty_high)]
    sim_dict['nodes'] = device_configs
    return sim_dict, router_mac


def get_sampling_cfg(router_mac, rep):
    return {
      "general": {
        "sample_duration_s": 1,
        "sample_interval_s": 60,
        "use_phy": true,
        "pos_xyz": [0, 0, 0],
        "output_name": f"./out{rep}/samples.npy"
      },
      "features": [
        {
          "property": "time",
          "map_function": null,
          "agg_function": "aggregators.count()"
        },
        {
          "property": "time",
          "map_function": "aggregators.iat()",
          "agg_function": "np.nanmin"
        },
        {
          "property": "time",
          "map_function": "aggregators.iat()",
          "agg_function": "np.nanmax"
        },
        {
          "property": "time",
          "map_function": "aggregators.iat()",
          "agg_function": "np.nanmean"
        },
        {
          "property": "~pkt",
          "map_function": null,
          "agg_function": "aggregators.count_if(lambda x: TCP in x)"
        },
        {
          "property": "~pkt",
          "map_function": null,
          "agg_function": "aggregators.count_if(lambda x: UDP in x)"
        },
        {
          "property": "wirelen",
          "map_function": null,
          "agg_function": "np.min"
        },
        {
          "property": "wirelen",
          "map_function": null,
          "agg_function": "np.max"
        },
        {
          "property": "wirelen",
          "map_function": null,
          "agg_function": "np.mean"
        },
        {
          "property": "wirelen",
          "map_function": null,
          "agg_function": "aggregators.n_unique()"
        },
        {
          "property": "src",
          "map_function": null,
          "agg_function": "aggregators.n_unique()"
        },
        {
          "property": "dst",
          "map_function": null,
          "agg_function": "aggregators.n_unique()"
        },
        {
          "property": "~phy",
          "map_function": f"aggregators.keep_if(lambda rec: rec[0].src == '{router_mac}')",
          "agg_function": "aggregators.head(200)"
        }
      ]
    }



if __name__ == '__main__':
    configs = {
        1: [10, 0, 0, 0],
        2: [10, 10, 0, 0],
        3: [10, 0, 0, 5],
        4: [0, 0, 2, 3],
    }

    for i in sorted(configs.keys()):
        config, rm = get_sim_cfg(i, *configs[i])
        sampling_config = get_sampling_cfg(rm, i)

        with open(f'sim_cfg{i}.json', 'w') as outfile:
            json.dump(config, outfile, indent=2)

        with open(f'sampling_cfg{i}.json', 'w') as outfile:
            json.dump(sampling_config, outfile, indent=2)
