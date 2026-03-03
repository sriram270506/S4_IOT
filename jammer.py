"""jammer.py

Pseudo Jammer node that injects high-volume UDP-like traffic on a channel.
"""
import random


class Jammer:
    def __init__(self, name: str = 'Jammer', target_channel: int = 6, active: bool = False):
        self.name = name
        self.target_channel = target_channel
        self.active = active

        # effectivity between 60% and 80% when active
        self.effectiveness = 0.0

    def activate(self, channel: int = None):
        self.active = True
        if channel is not None:
            self.target_channel = channel
        # randomize effectiveness to emulate variable jammer power
        self.effectiveness = random.uniform(0.6, 0.8)

    def deactivate(self):
        self.active = False
        self.effectiveness = 0.0

    def step(self):
        # Jammer could vary effectiveness slightly over time
        if self.active:
            self.effectiveness = max(0.5, min(0.85, self.effectiveness * random.uniform(0.98, 1.02)))
        return {'active': self.active, 'channel': self.target_channel, 'effectiveness': self.effectiveness}
