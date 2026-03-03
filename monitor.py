"""monitor.py

Monitoring layer: polls AP telemetry and stores time-series metrics.
"""
from typing import Dict, List
import time


class Monitor:
    def __init__(self):
        # time series storage
        self.timestamps: List[float] = []
        self.channel_utilization: List[Dict[int, float]] = []  # per channel utilization
        self.packet_loss: List[Dict[int, float]] = []
        self.throughput_per_client: List[Dict[str, float]] = []
        self.interference_index: List[float] = []
        self.events: List[Dict] = []

    def record(self, t: float, ap_telemetries: Dict[str, Dict], interference_index: float):
        """Record telemetry data from APs.

        ap_telemetries: map ap_name -> telemetry dict
        interference_index: computed scalar for the step
        """
        self.timestamps.append(t)

        # map channel -> sum(utilization)
        util_map = {}
        loss_map = {}
        tp_map = {}
        for ap_name, tel in ap_telemetries.items():
            ch = tel['channel']
            util_map.setdefault(ch, 0.0)
            util_map[ch] += tel.get('channel_utilization', 0.0)
            loss_map.setdefault(ch, 0.0)
            loss_map[ch] += tel.get('packet_loss', 0.0)

            # per client throughputs included
            for cname, val in tel.get('per_client_throughput', {}).items():
                tp_map[cname] = val

        self.channel_utilization.append(util_map)
        self.packet_loss.append(loss_map)
        self.throughput_per_client.append(tp_map)
        self.interference_index.append(interference_index)

    def log_event(self, t: float, message: str):
        self.events.append({'time': t, 'message': message})
