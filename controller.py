"""controller.py

SDN Controller implementation for simulation.
"""
from typing import Dict, List
import time
import logging


class Controller:
    def __init__(self, aps: List[object], monitor: object, channels: List[int] = [1, 6, 11]):
        self.aps = {ap.name: ap for ap in aps}
        self.monitor = monitor
        self.channels = channels
        self.last_poll = None

        # thresholds
        self.utilization_threshold = 0.75
        self.jammer_spike_threshold = 0.7
        self.throughput_drop_fraction = 0.4  # relative drop to trigger action

        # simple internal store
        self.history = []

        # logger
        logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    def poll(self, t: float, jammer_info: Dict = None):
        """Poll telemetry from APs and decide actions if needed."""
        ap_tels = {name: ap.telemetry.copy() for name, ap in self.aps.items()}

        # compute simple interference index: sum of channels with >1 AP
        channels = {}
        for name, tel in ap_tels.items():
            ch = tel['channel']
            channels.setdefault(ch, 0)
            channels[ch] += 1

        interference_index = sum(1 for c, cnt in channels.items() if cnt > 1)

        # jam detection heuristics: if jammer_info indicates high effectiveness on channel
        jammer_detected = False
        if jammer_info and jammer_info.get('active'):
            # if any AP on same channel experiences large drop, treat as detected
            jam_ch = jammer_info.get('channel')
            eff = jammer_info.get('effectiveness', 0.0)
            if eff >= 0.55:
                # check if APs on jam_ch have unexpectedly high utilization
                for name, tel in ap_tels.items():
                    if tel['channel'] == jam_ch and tel['channel_utilization'] > self.jammer_spike_threshold:
                        jammer_detected = True
                        break

        # Channel congestion detection
        congested_channels = [ch for ch, cnt in channels.items() if cnt > 1]

        # Throughput degradation detection: if any AP throughput low relative to capacity
        degraded_aps = []
        for name, tel in ap_tels.items():
            if tel['throughput_mbps'] < (0.5 * self.aps[name].base_bandwidth):
                degraded_aps.append(name)

        # Log findings
        if congested_channels:
            logging.info(f"[Controller] High interference detected on Channel(s) {congested_channels}")
            self.monitor.log_event(t, f"High interference on {congested_channels}")

        if jammer_detected:
            logging.info("[Controller] Jammer signature detected")
            self.monitor.log_event(t, "Jammer detected")

        # Actions
        # If jammer detected: try to isolate affected AP(s) by moving them to a channel without the jammer
        if jammer_detected:
            jam_ch = jammer_info['channel']
            # find APs on jam_ch
            for name, tel in ap_tels.items():
                if tel['channel'] == jam_ch:
                    # pick a channel that is not jam_ch and ideally not used by many APs
                    target = self._pick_least_used_channel(exclude=[jam_ch])
                    logging.info(f"[Controller] Reassigning {name} → Channel {target}")
                    self.monitor.log_event(t, f"Reassign {name} -> {target}")
                    self.aps[name].set_channel(target)
                    # only move one AP at a time for smoother transition
                    break

        # If general congestion (APs sharing channel): move one of them
        elif congested_channels:
            # pick an AP from the most congested channel
            ch = congested_channels[0]
            aps_on_ch = [name for name, tel in ap_tels.items() if tel['channel'] == ch]
            # select lowest-impact AP to move (fewest clients)
            aps_on_ch_sorted = sorted(aps_on_ch, key=lambda n: self.aps[n].telemetry.get('num_clients', 0))
            to_move = aps_on_ch_sorted[-1] if aps_on_ch_sorted else aps_on_ch[0]
            target = self._pick_least_used_channel(exclude=[ch])
            logging.info(f"[Controller] Reassigning {to_move} → Channel {target}")
            self.monitor.log_event(t, f"Reassign {to_move} -> {target}")
            self.aps[to_move].set_channel(target)

        # Archive
        self.history.append({'time': t, 'telemetry': ap_tels, 'interference_index': interference_index, 'jammer_detected': jammer_detected})

        # hand telemetry back to monitor
        self.monitor.record(t, ap_tels, interference_index)

    def _pick_least_used_channel(self, exclude: List[int] = None) -> int:
        exclude = exclude or []
        # count usage
        counts = {ch: 0 for ch in self.channels}
        for ap in self.aps.values():
            if ap.channel in counts:
                counts[ap.channel] += 1

        # prefer channels not in exclude
        candidates = [ch for ch in self.channels if ch not in exclude]
        # Prefer channel 11 when available (widely used non-overlapping channel in 2.4GHz)
        if 11 in candidates:
            return 11
        # otherwise sort by usage
        candidates.sort(key=lambda c: counts.get(c, 0))
        return candidates[0]
 