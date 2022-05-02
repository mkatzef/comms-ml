from .MHP import MHP as MultidimHawkesProcess
import numpy as np


class TrafficSource:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def get_message_times(self, horizon):
        return []


class TrafficSourceBursty(TrafficSource):
    def __init__(self, burst_counter=1, tx_len_min_bytes=10, tx_len_max_bytes=10,
        intra_burst_interval=(0.01, 0.07), inter_burst_interval=(0.1, 60)):

        super().__init__()
        self.tx_len_min_bytes = tx_len_min_bytes
        self.tx_len_max_bytes = tx_len_max_bytes

        self.intra_burst_interval = intra_burst_interval
        self.inter_burst_interval = inter_burst_interval
        self.default_burst_counter = burst_counter + 1
        self.burst_count = 1

    def prepare_next_message(self, sim_time):
        """ Generates a random time at which the next message will start based
        on the current time in the simulation. """
        self.burst_count -= 1
        if self.burst_count > 0:
            tx_interval = np.random.uniform(*self.intra_burst_interval)
        else:
            tx_interval = np.random.uniform(*self.inter_burst_interval)
            self.burst_count = np.random.randint(1, self.default_burst_counter)

        tx_start_time = sim_time + tx_interval
        msg_len_bits = np.random.randint(self.tx_len_min_bytes, self.tx_len_max_bytes + 1) * 8

        return tx_start_time, msg_len_bits


def get_day_second_from_time(sim_time):
    """ Time difference in days and seconds from sim start.
    Note: wraps at weeks. """
    second_of_week = sim_time % seconds_per_week
    day_of_week = int(second_of_week / seconds_per_day)
    second_of_day = second_of_week % seconds_per_day

    return day_of_week, second_of_day


def get_hp_params(day_index, second, weekends=0.5):
    day_mults = [1, 1, 1, 1, 1, weekends, weekends]  # Mon-Sun
    day_mult = day_mults[day_index]
    intensity = 0.001 + 0.02 + 0.02 * day_mult * (1 + np.sin((2 / seconds_per_day * second - 1) * np.pi))
    return intensity


class TrafficSourceHawkes(TrafficSource):
    # Hawkes builds a queue of packet arrivals and pops from that for traffic
    # Uses max time (popped, current) so a bottleneck will still process messages in order
    def __init__(self, tx_len_min_bytes=10, tx_len_max_bytes=10, total_time_s=2, intensity=0.05):
        super().__init__()
        self.tx_len_min_bytes = tx_len_min_bytes
        self.tx_len_max_bytes = tx_len_max_bytes

        self.msg_times = MultidimHawkesProcess(mu=[intensity]).generate_seq(total_time_s)[:, 0]
        self.msg_pointer = 0
        self.total_time_s = total_time_s

    def prepare_next_message(self, sim_time):
        """ Generates a random time at which the next message will start based
        on the current time in the simulation. """
        if self.msg_pointer >= len(self.msg_times):
            return self.total_time_s, 0  # TODO: Sentinel, as we have depleted this traffic source

        tx_start_time = max(sim_time, self.msg_times[self.msg_pointer])
        self.msg_pointer += 1
        msg_len_bits = np.random.randint(self.tx_len_min_bytes, self.tx_len_max_bytes + 1) * 8

        return tx_start_time, msg_len_bits


class TrafficSourceBenchmark(TrafficSource):
    def __init__(self, tx_len_max_bytes=10, interval_s=0.5, index=0):
        super().__init__()
        self.tx_len_max_bytes = tx_len_max_bytes
        self.msg_times = [(index+i+1)*interval_s for i in range(int(60/interval_s))]
        self.msg_pointer = 0

    def prepare_next_message(self, sim_time):
        tx_start_time = max(sim_time, self.msg_times[self.msg_pointer])
        self.msg_pointer += 1
        msg_len_bits = self.tx_len_max_bytes * 8
        return tx_start_time, msg_len_bits


class TrafficSourceHawkesPeriodic(TrafficSource):
    # Hawkes builds a queue of packet arrivals and pops from that for traffic
    # Uses max time (popped, current) so a bottleneck will still process messages in order
    def __init__(self, tx_len_min_bytes=10, tx_len_max_bytes=10, total_time_s=2, weekend_mult=0.5):
        super().__init__()
        self.tx_len_min_bytes = tx_len_min_bytes
        self.tx_len_max_bytes = tx_len_max_bytes

        self.msg_times = []
        self.msg_pointer = 0
        self.weekends = weekend_mult

    def prepare_message_sequence(self, sim_time, horizon):
        """ Generates at least 1 message based on the current time and multiples
        of the given horizon """
        self.msg_times = []
        self.msg_pointer = 0
        times = []
        init_time = sim_time
        while len(times) == 0:
            # update params based on current time
            intensity = get_hp_params(*get_day_second_from_time(init_time), weekends=self.weekends)
            times = init_time + MultidimHawkesProcess(mu=[intensity]).generate_seq(horizon)[:, 0]
            init_time += horizon
        self.msg_times = times

    def prepare_next_message(self, sim_time):
        """ Generates a random time at which the next message will start based
        on the current time in the simulation. """
        if self.msg_pointer >= len(self.msg_times):
            self.prepare_message_sequence(sim_time, 60 * 10)  # cache 10-minute intervals

        tx_start_time = max(sim_time, self.msg_times[self.msg_pointer])
        self.msg_pointer += 1
        msg_len_bits = np.random.randint(self.tx_len_min_bytes, self.tx_len_max_bytes + 1) * 8

        return tx_start_time, msg_len_bits


def get_traffic_model(
    traffic_type,
    tx_len_min_bytes=1,
    tx_len_max_bytes=1500,
    sim_time_s=None,
    arg_bursty_n=5,
    arg_bursty_intra=(0.01, 0.07),
    arg_bursty_inter=(0.1, 60),
    arg_hawkes=0.05,
    weekend_mult=0.5):

    if traffic_type == "bursty":
        new_traffic = TrafficSourceBursty(
            burst_counter=arg_bursty_n,
            tx_len_min_bytes=tx_len_min_bytes,
            tx_len_max_bytes=tx_len_max_bytes,
            intra_burst_interval=arg_bursty_intra,
            inter_burst_interval=arg_bursty_inter
        )
    elif traffic_type == "hawkes":
        new_traffic = TrafficSourceHawkes(
            tx_len_min_bytes=tx_len_min_bytes,
            tx_len_max_bytes=tx_len_max_bytes,
            total_time_s=sim_time_s,
            intensity=arg_hawkes
        )
    elif traffic_type == "hawkes_periodic":
        new_traffic = TrafficSourceHawkesPeriodic(
            tx_len_min_bytes=tx_len_min_bytes,
            tx_len_max_bytes=tx_len_max_bytes,
            total_time_s=sim_time_s,
            weekend_mult=weekend_mult
        )
    else:
        raise NameError("Unrecognized traffic type")

    return new_traffic
