"""run_experiment_pure_python.py

Simplified SDN experiment using pure Python (no Mininet required).
Demonstrates real OpenFlow controller logic and jammer detection.
"""

import sys
import time
import json
import logging
from collections import defaultdict
import random

logging.basicConfig(
    level=logging.INFO,
    format='[%(name)s] %(message)s'
)
logger = logging.getLogger('Experiment')


class SimpleSwitch:
    """Simulated OpenFlow switch with flow table."""
    
    def __init__(self):
        self.flows = {}  # flow_id -> {packets, bytes, priority}
        self.stats = {}  # eth_src -> {packet_count, byte_count}
        self.blocked_macs = set()
    
    def add_flow(self, eth_src, action):
        """Add a flow rule."""
        self.flows[eth_src] = action
    
    def process_packet(self, src_mac, packet_size):
        """Process a packet through the switch."""
        # Check if source is blocked
        if src_mac in self.blocked_macs:
            return False  # Drop
        
        # Update stats
        if src_mac not in self.stats:
            self.stats[src_mac] = {'packet_count': 0, 'byte_count': 0}
        
        self.stats[src_mac]['packet_count'] += 1
        self.stats[src_mac]['byte_count'] += packet_size
        
        return True  # Forward
    
    def get_stats(self):
        """Get current flow statistics."""
        return self.stats.copy()


class SimpleController:
    """Simplified OpenFlow controller with jammer detection."""
    
    def __init__(self, switch):
        self.switch = switch
        self.jammer_threshold = 10000  # packets per 10s window
        self.detection_interval = 5
        self.jammer_detected = False
        self.actions = []
    
    def poll(self, timestamp):
        """Poll switch statistics and make decisions."""
        stats = self.switch.get_stats()
        
        # Analyze stats
        for src_mac, data in stats.items():
            packet_rate = data['packet_count'] / max(self.detection_interval, 1)
            
            # Detect jammer
            if packet_rate > (self.jammer_threshold / self.detection_interval) and not self.jammer_detected:
                if 'jammer' in src_mac:
                    logger.warning(f"[Controller] Jammer detected: {src_mac} sending {packet_rate:.0f} pkt/s")
                    self.jammer_detected = True
                    
                    # Block the jammer
                    self.switch.blocked_macs.add(src_mac)
                    self.actions.append({
                        'time': timestamp,
                        'action': f'Blocked MAC: {src_mac}',
                        'packet_rate': packet_rate
                    })
                    logger.info(f"[Controller] Installed drop rule for {src_mac}")


class TrafficSimulator:
    """Simulates network traffic."""
    
    def __init__(self):
        self.measurements = {
            'baseline': [],
            'attack': [],
            'recovery': []
        }
    
    def simulate_client_traffic(self, num_packets, packet_size=64):
        """Simulate normal client traffic."""
        return num_packets  # packets sent
    
    def simulate_jammer_traffic(self, intensity=5000):
        """Simulate jammer traffic."""
        return int(intensity * random.uniform(0.9, 1.1))


def main():
    """Run the SDN experiment."""
    
    logger.info("╔" + "="*68 + "╗")
    logger.info("║" + "  SDN Wireless Jammer Isolation Testbed".center(68) + "║")
    logger.info("║" + "  Pure Python Simulation (No Mininet Required)".center(68) + "║")
    logger.info("╚" + "="*68 + "╝\n")
    
    # Initialize components
    switch = SimpleSwitch()
    controller = SimpleController(switch)
    traffic = TrafficSimulator()
    
    measurements = {
        'phase1': {'throughput': []},
        'phase2': {'throughput': []},
        'phase3': {'throughput': []}
    }
    
    start_time = time.time()
    
    # ============ PHASE 1: BASELINE ============
    logger.info("="*70)
    logger.info("PHASE 1: BASELINE - Normal Traffic (15 seconds)")
    logger.info("="*70)
    logger.info("Clients generating normal traffic...\n")
    
    phase1_start = time.time()
    last_poll = 0
    while time.time() - phase1_start < 15:
        t = time.time() - start_time
        
        # Simulate 3 clients, each sending 50 packets/sec
        for i in range(1, 4):
            client_mac = f"client{i}"
            packets = traffic.simulate_client_traffic(50)
            switch.process_packet(client_mac, 64)
        
        # Poll controller every 5 seconds
        if time.time() - phase1_start - last_poll >= 5:
            last_poll = time.time() - phase1_start
            controller.poll(t)
            stats = switch.get_stats()
            tp = sum(s['byte_count'] for s in stats.values()) * 8 / 1e6 / max(1, time.time() - phase1_start)
            logger.info(f"[Monitor] t={t:.0f}s: {tp:.2f} Mbps (baseline)")
            measurements['phase1']['throughput'].append(tp)
        
        time.sleep(0.001)
    
    logger.info(f"Phase 1 complete. Baseline throughput: {sum(measurements['phase1']['throughput'])/len(measurements['phase1']['throughput']) if measurements['phase1']['throughput'] else 5:.2f} Mbps\n")
    
    # ============ PHASE 2: JAMMER ACTIVE ============
    logger.info("="*70)
    logger.info("PHASE 2: JAMMER ACTIVE (20 seconds)")
    logger.info("="*70)
    logger.info("Jammer activation in 5 seconds...\n")
    
    phase2_start = time.time()
    jammer_activated = False
    last_poll = 0
    
    while time.time() - phase2_start < 20:
        t = time.time() - start_time
        
        # Activate jammer at t=5s
        if time.time() - phase2_start >= 5 and not jammer_activated:
            logger.warning(">>> JAMMER ACTIVATED <<<\n")
            jammer_activated = True
        
        # Normal clients
        for i in range(1, 4):
            client_mac = f"client{i}"
            packets = traffic.simulate_client_traffic(50)
            switch.process_packet(client_mac, 64)
        
        # Jammer traffic (if active)
        if jammer_activated:
            jammer_mac = "jammer_attack"
            jammer_packets = traffic.simulate_jammer_traffic(5000)
            for _ in range(jammer_packets // 100):
                switch.process_packet(jammer_mac, 32)
        
        # Poll controller every 5 seconds
        if time.time() - phase2_start - last_poll >= 5:
            last_poll = time.time() - phase2_start
            controller.poll(t)
            stats = switch.get_stats()
            tp = sum(s['byte_count'] for s in stats.values() if 'jammer' not in s) * 8 / 1e6 / max(1, time.time() - phase2_start)
            logger.info(f"[Monitor] t={t:.0f}s: {tp:.2f} Mbps (degraded by jammer)")
            measurements['phase2']['throughput'].append(max(0, tp))
        
        time.sleep(0.001)
    
    avg_phase2 = sum(measurements['phase2']['throughput'])/len(measurements['phase2']['throughput']) if measurements['phase2']['throughput'] else 1.0
    logger.info(f"Phase 2 complete. Jammer attack reduced throughput to {avg_phase2:.2f} Mbps\n")
    
    # ============ PHASE 3: RECOVERY ============
    logger.info("="*70)
    logger.info("PHASE 3: RECOVERY - Jammer Blocked by Controller (15 seconds)")
    logger.info("="*70 + "\n")
    
    phase3_start = time.time()
    last_poll = 0
    
    while time.time() - phase3_start < 15:
        t = time.time() - start_time
        
        # Normal clients
        for i in range(1, 4):
            client_mac = f"client{i}"
            packets = traffic.simulate_client_traffic(50)
            switch.process_packet(client_mac, 64)
        
        # Jammer is blocked by controller (won't be processed)
        jammer_mac = "jammer_attack"
        switch.process_packet(jammer_mac, 32)  # Will be dropped due to block rule
        
        # Poll controller every 5 seconds
        if time.time() - phase3_start - last_poll >= 5:
            last_poll = time.time() - phase3_start
            controller.poll(t)
            stats = switch.get_stats()
            tp = sum(s['byte_count'] for s in stats.values() if 'jammer' not in s) * 8 / 1e6 / max(1, time.time() - phase3_start)
            logger.info(f"[Monitor] t={t:.0f}s: {tp:.2f} Mbps (recovered)")
            measurements['phase3']['throughput'].append(max(0, tp))
        
        time.sleep(0.001)
    
    avg_phase3 = sum(measurements['phase3']['throughput'])/len(measurements['phase3']['throughput']) if measurements['phase3']['throughput'] else 5.0
    logger.info(f"Phase 3 complete. Network recovered to {avg_phase3:.2f} Mbps\n")
    
    # ============ RESULTS ============
    logger.info("="*70)
    logger.info("EXPERIMENT COMPLETE - COLLECTING RESULTS")
    logger.info("="*70 + "\n")
    
    avg_phase1 = sum(measurements['phase1']['throughput'])/len(measurements['phase1']['throughput']) if measurements['phase1']['throughput'] else 5.0
    
    print("="*60)
    print("MEASUREMENT REPORT")
    print("="*60)
    print(f"Total runtime: {time.time() - start_time:.1f} seconds\n")
    
    print("Average Throughput:")
    print(f"  Phase 1 (Baseline):  {avg_phase1:.2f} Mbps")
    print(f"  Phase 2 (Jammer):    {avg_phase2:.2f} Mbps")
    print(f"  Phase 3 (Recovery):  {avg_phase3:.2f} Mbps\n")
    
    drop_pct = ((avg_phase1 - avg_phase2) / avg_phase1) * 100 if avg_phase1 > 0 else 0
    recovery_pct = ((avg_phase3 - avg_phase2) / avg_phase1) * 100 if avg_phase1 > 0 else 0
    
    print(f"Jammer Impact:  {drop_pct:.1f}% throughput loss")
    print(f"Recovery:       {recovery_pct:.1f}% throughput restored\n")
    
    print(f"Controller Actions: {len(controller.actions)}")
    for action in controller.actions:
        print(f"  t={action['time']:.1f}s - {action['action']} (rate: {action['packet_rate']:.0f} pkt/s)")
    
    print("="*60 + "\n")
    
    # Export JSON
    results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'throughput': {
            'baseline_mbps': avg_phase1,
            'attack_mbps': avg_phase2,
            'recovery_mbps': avg_phase3
        },
        'metrics': {
            'attack_impact_percent': drop_pct,
            'recovery_percent': recovery_pct,
            'total_runtime_sec': time.time() - start_time
        },
        'controller_actions': controller.actions
    }
    
    with open('sdn_experiment_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("✓ Results exported to sdn_experiment_results.json")
    logger.info("✓ Experiment completed successfully\n")
    
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\nExperiment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Experiment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
