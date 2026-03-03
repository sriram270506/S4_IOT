"""measurement.py

Real-time measurement and metrics collection from Mininet testbed.
Collects throughput, packet loss, latency, and jammer detection stats.
"""

import json
import time
import re
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Measurement:
    """Collects and stores network metrics."""

    def __init__(self):
        self.throughput_history = {}  # {timestamp: {client: mbps}}
        self.packet_loss_history = {}  # {timestamp: {client: loss_pct}}
        self.latency_history = {}
        self.jammer_detection_events = []
        self.controller_actions = []
        self.start_time = time.time()

    def record_iperf_result(self, client_name: str, iperf_json: str):
        """Parse iperf3 JSON output and record throughput."""
        try:
            data = json.loads(iperf_json)
            # Extract sender throughput (bits per second)
            sender = data.get('end', {}).get('sum_sent', {})
            throughput_mbps = sender.get('bits_per_second', 0) / 1e6
            packet_loss = data.get('end', {}).get('sum_sent', {}).get('retransmits', 0)

            t = time.time() - self.start_time
            if t not in self.throughput_history:
                self.throughput_history[t] = {}
            self.throughput_history[t][client_name] = throughput_mbps

            logger.info(f"[Measurement] {client_name}: {throughput_mbps:.2f} Mbps")
            return throughput_mbps
        except Exception as e:
            logger.error(f"Failed to parse iperf result: {e}")
            return 0.0

    def record_jammer_detection(self, jammer_mac: str, detection_method: str):
        """Record when jammer is detected."""
        t = time.time() - self.start_time
        event = {
            'time': t,
            'jammer_mac': jammer_mac,
            'method': detection_method
        }
        self.jammer_detection_events.append(event)
        logger.info(f"[Measurement] Jammer detected: {jammer_mac} via {detection_method}")

    def record_controller_action(self, action: str, details: Dict = None):
        """Record when controller makes a decision."""
        t = time.time() - self.start_time
        event = {
            'time': t,
            'action': action,
            'details': details or {}
        }
        self.controller_actions.append(event)
        logger.info(f"[Controller Action] {action}: {details}")

    def get_summary(self) -> Dict:
        """Return summary of all measurements."""
        avg_throughput = {}
        for tp_map in self.throughput_history.values():
            for client, mbps in tp_map.items():
                if client not in avg_throughput:
                    avg_throughput[client] = []
                avg_throughput[client].append(mbps)

        avg_throughput = {
            client: sum(vals) / len(vals) if vals else 0.0
            for client, vals in avg_throughput.items()
        }

        return {
            'avg_throughput': avg_throughput,
            'jammer_detections': self.jammer_detection_events,
            'controller_actions': self.controller_actions,
            'total_runtime': time.time() - self.start_time
        }

    def print_report(self):
        """Print a formatted measurement report."""
        summary = self.get_summary()
        print("\n" + "="*60)
        print("MEASUREMENT REPORT")
        print("="*60)
        print(f"Total runtime: {summary['total_runtime']:.1f} seconds\n")

        print("Average Throughput per Client:")
        for client, mbps in summary['avg_throughput'].items():
            print(f"  {client}: {mbps:.2f} Mbps")

        print(f"\nJammer Detection Events: {len(summary['jammer_detections'])}")
        for event in summary['jammer_detections']:
            print(f"  t={event['time']:.1f}s - {event['jammer_mac']} ({event['method']})")

        print(f"\nController Actions: {len(summary['controller_actions'])}")
        for event in summary['controller_actions']:
            print(f"  t={event['time']:.1f}s - {event['action']}")
            for k, v in event['details'].items():
                print(f"      {k}: {v}")

        print("="*60 + "\n")

    def export_json(self, filename: str = 'measurements.json'):
        """Export all measurements to JSON file."""
        data = {
            'throughput_history': self.throughput_history,
            'packet_loss_history': self.packet_loss_history,
            'jammer_detection_events': self.jammer_detection_events,
            'controller_actions': self.controller_actions,
            'summary': self.get_summary()
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Measurements exported to {filename}")
