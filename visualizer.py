"""visualizer.py

Real-time visualization using matplotlib animation.
"""
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from typing import List


class Visualizer:
    def __init__(self, monitor, controller, aps: List[object], clients: List[object], jammer):
        self.monitor = monitor
        self.controller = controller
        self.aps = aps
        self.clients = clients
        self.jammer = jammer

        # plotting state
        self.fig, (self.ax_tp, self.ax_ch, self.ax_int) = plt.subplots(3, 1, figsize=(10, 8))
        plt.tight_layout(pad=3.0)

        # lines for throughput per AP
        self.ap_lines = {ap.name: self.ax_tp.plot([], [], label=ap.name)[0] for ap in self.aps}
        self.ax_tp.set_title('Throughput over time (Mbps)')
        self.ax_tp.set_xlabel('Time (s)')
        self.ax_tp.set_ylabel('Throughput (Mbps)')
        self.ax_tp.legend()

        # channel usage bar chart
        self.ax_ch.set_title('Channel usage (AP counts)')
        self.ax_ch.set_xlabel('Channel')
        self.ax_ch.set_ylabel('Number of APs')

        # interference plot
        self.int_line, = self.ax_int.plot([], [], color='r')
        self.ax_int.set_title('Interference index over time')
        self.ax_int.set_xlabel('Time (s)')
        self.ax_int.set_ylabel('Interference index')

        # event markers stored to avoid redrawing duplicates
        self._event_times = set()

    def _get_history(self):
        times = list(range(len(self.monitor.timestamps)))
        # per-AP throughputs
        ap_hist = {ap.name: [] for ap in self.aps}
        for tp_map in self.monitor.throughput_per_client:
            # sum per ap by checking which clients belong to which ap
            ap_sums = {ap.name: 0.0 for ap in self.aps}
            # tp_map: client name -> throughput
            for c in self.clients:
                # find client's ap at this time by reading controller.history? Simpler: use latest assignments
                # This routine approximates aggregation by mapping client->ap via current ap assignment
                ap_name = c.ap.name if c.ap else None
                if ap_name and c.name in tp_map:
                    ap_sums[ap_name] += tp_map[c.name]

            for ap in self.aps:
                ap_hist[ap.name].append(ap_sums.get(ap.name, 0.0))

        return times, ap_hist

    def _update(self, frame):
        times, ap_hist = self._get_history()

        if times:
            tmax = max(times)
        else:
            tmax = 1

        # update throughput lines
        for ap in self.aps:
            y = ap_hist[ap.name]
            self.ap_lines[ap.name].set_data(times, y)

        self.ax_tp.set_xlim(max(0, tmax - 60), tmax + 1)
        # autoscale y
        all_vals = []
        for v in ap_hist.values():
            all_vals.extend(v)
        ymax = max(max(all_vals) * 1.2 if all_vals else 10, 10)
        self.ax_tp.set_ylim(0, ymax)

        # update channel usage (current)
        channels = [ap.channel for ap in self.aps]
        unique_ch = sorted(set(channels))
        counts = [channels.count(ch) for ch in unique_ch]
        self.ax_ch.clear()
        self.ax_ch.bar([str(ch) for ch in unique_ch], counts, color='tab:blue')
        self.ax_ch.set_title('Channel usage (AP counts)')
        # indicate jammer
        if self.jammer.active:
            jam_ch = str(self.jammer.target_channel)
            # highlight bar if present
            for idx, ch in enumerate([str(c) for c in unique_ch]):
                if ch == jam_ch:
                    self.ax_ch.patches[idx].set_color('tab:red')

        # interference
        xs = list(range(len(self.monitor.interference_index)))
        ys = self.monitor.interference_index
        self.int_line.set_data(xs, ys)
        if xs:
            self.ax_int.set_xlim(max(0, xs[-1] - 60), xs[-1] + 1)
        self.ax_int.set_ylim(0, max(3, max(ys) + 1 if ys else 3))

        # add event markers (controller events) as vertical lines
        for ev in self.monitor.events:
            # event time is float; convert to int index using timestamp list if possible
            try:
                idx = int(ev['time'])
            except Exception:
                continue
            if idx in self._event_times:
                continue
            if idx <= (xs[-1] if xs else 0):
                self.ax_tp.axvline(idx, color='k', linestyle='--', alpha=0.7)
                self.ax_int.axvline(idx, color='k', linestyle='--', alpha=0.7)
                self.ax_ch.axvline(idx, color='k', linestyle='--', alpha=0.7)
                self._event_times.add(idx)

        return list(self.ap_lines.values()) + [self.int_line]

    def run(self, interval_ms: int = 1000):
        ani = animation.FuncAnimation(self.fig, self._update, interval=interval_ms)
        plt.show()
