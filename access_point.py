"""access_point.py

AccessPoint class for SDN simulation.
"""
from typing import List
import random


class AccessPoint:
    def __init__(self, name: str, channel: int, bandwidth_mbps: float = 100.0):
        self.name = name
        self.channel = channel
        self.base_bandwidth = bandwidth_mbps  # Mbps
        self.connected_clients: List[object] = []

        # telemetry
        self.telemetry = {
            'channel': channel,
            'num_clients': 0,
            'throughput_mbps': 0.0,
            'channel_utilization': 0.0,
            'packet_loss': 0.0,
        }

    def connect(self, client):
        self.connected_clients.append(client)
        client.ap = self

    def disconnect(self, client):
        if client in self.connected_clients:
            self.connected_clients.remove(client)
            client.ap = None

    def set_channel(self, channel: int):
        self.channel = channel
        self.telemetry['channel'] = channel

    def compute_effective_bandwidth(self, other_aps_on_same_channel: int, jammer_factor: float = 0.0):
        """Compute effective bandwidth available to this AP.

        other_aps_on_same_channel: number of APs (excluding self) on same channel
        jammer_factor: fractional reduction [0..1] due to jammer
        """
        effective = self.base_bandwidth
        # If another AP shares channel, split bandwidth equally
        if other_aps_on_same_channel >= 1:
            effective = effective / (other_aps_on_same_channel + 1)

        # Jammer reduces available bandwidth further
        if jammer_factor > 0:
            effective = effective * (1 - jammer_factor)

        # tiny noise to simulate variability
        effective = effective * random.uniform(0.98, 1.02)
        return max(effective, 0.0)

    def step(self, other_aps_on_same_channel: int, jammer_factor: float = 0.0):
        """Simulate one time step: allocate bandwidth to connected clients and update telemetry."""
        # Compute effective bandwidth for AP
        effective_bw = self.compute_effective_bandwidth(other_aps_on_same_channel, jammer_factor)

        # Collect client demands
        demands = [c.current_demand_mbps for c in self.connected_clients]
        total_demand = sum(demands) if demands else 0.0

        allocated = {}
        total_throughput = 0.0
        packet_loss = 0.0

        if total_demand <= effective_bw or total_demand == 0:
            # satisfy all demands
            for c in self.connected_clients:
                allocated[c.name] = c.current_demand_mbps
                total_throughput += c.current_demand_mbps
        else:
            # share capacity proportionally to demand
            for c in self.connected_clients:
                share = (c.current_demand_mbps / total_demand) * effective_bw
                allocated[c.name] = share
                total_throughput += share
            packet_loss = (total_demand - total_throughput) / total_demand

        # update telemetry
        self.telemetry.update({
            'channel': self.channel,
            'num_clients': len(self.connected_clients),
            'throughput_mbps': total_throughput,
            'channel_utilization': min(total_throughput / self.base_bandwidth, 1.0) if self.base_bandwidth > 0 else 0.0,
            'packet_loss': packet_loss,
            'per_client_throughput': allocated,
        })

        # inform clients of their achieved throughput (for local stats)
        for c in self.connected_clients:
            c.observed_throughput_mbps = allocated.get(c.name, 0.0)

        return self.telemetry.copy()
