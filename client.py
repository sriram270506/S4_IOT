"""client.py

Client device simulation.
"""
import random
from typing import Optional


class Client:
    def __init__(self, name: str, mean_demand_mbps: float = 5.0, variance: float = 2.0):
        self.name = name
        self.mean_demand_mbps = mean_demand_mbps
        self.variance = variance
        self.ap: Optional[object] = None

        # per-step runtime
        self.current_demand_mbps = 0.0
        self.observed_throughput_mbps = 0.0

        # history
        self.history = []

    def generate_traffic(self):
        """Generate variable UDP-like bandwidth demand for this timestep."""
        demand = random.gauss(self.mean_demand_mbps, max(0.1, self.variance))
        demand = max(0.0, demand)
        self.current_demand_mbps = demand
        return demand

    def step(self):
        # generate demand
        self.generate_traffic()

        # record observed throughput (set by AP.step)
        self.history.append({
            'demand': self.current_demand_mbps,
            'throughput': self.observed_throughput_mbps,
        })
