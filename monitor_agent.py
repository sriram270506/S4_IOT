#!/usr/bin/env python3
"""
Monitor & Jammer Agent - Laptop 3
Monitors network traffic and generates jammer packets
"""

import socket
import json
import time
import random
import threading

class MonitorAgent:
    def __init__(self, controller_ip='192.168.1.100', controller_port=9000):
        self.controller_ip = controller_ip
        self.controller_port = controller_port
        
        self.current_phase = 'baseline'
        self.jammer_active = False
        self.packet_count = 0
        self.packet_rate = 0
        
        print("\n" + "="*70)
        print("MONITOR & JAMMER AGENT - LAPTOP 3")
        print("="*70)
        print(f"Controller: {self.controller_ip}:{self.controller_port}")
        print("="*70)
    
    def simulate_network_traffic(self):
        """Simulate network traffic and jammer packets"""
        while True:
            try:
                if self.current_phase == 'baseline':
                    # Normal traffic: ~200-500 packets/sec
                    self.packet_rate = random.randint(200, 500)
                
                elif self.current_phase == 'attack' and self.jammer_active:
                    # Jammer active: ~8000-10000 packets/sec
                    self.packet_rate = random.randint(8000, 10000)
                    print(f"[Monitor] 🚨 JAMMER ACTIVE: {self.packet_rate} pps")
                
                elif self.current_phase == 'recovery':
                    # Recovery: normal traffic
                    self.packet_rate = random.randint(200, 500)
                
                self.packet_count += self.packet_rate
                
                # Send metrics to controller
                self.send_metrics()
                
                time.sleep(2)
            except Exception as e:
                print(f"[Monitor] Error: {e}")
                time.sleep(2)
    
    def send_metrics(self):
        """Send monitor metrics to controller"""
        try:
            message = json.dumps({
                'type': 'monitor_metrics',
                'timestamp': time.time(),
                'data': {
                    'packet_rate': self.packet_rate,
                    'packet_count': self.packet_count,
                    'phase': self.current_phase,
                    'jammer_active': self.jammer_active
                }
            })
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(message.encode(), (self.controller_ip, self.controller_port))
            sock.close()
            
            print(f"[Monitor] {self.packet_rate} pps | Phase: {self.current_phase}")
            
        except Exception as e:
            print(f"[Monitor] Send error: {e}")
    
    def simulate_phases(self):
        """Simulate experiment phases"""
        time.sleep(2)  # Wait for connections
        
        # Phase 1: Baseline (10 seconds)
        print("\n[Monitor] Starting Phase 1: BASELINE (10s)")
        self.current_phase = 'baseline'
        self.jammer_active = False
        time.sleep(10)
        
        # Phase 2: Attack (10 seconds)
        print("\n[Monitor] Starting Phase 2: ATTACK with JAMMER (10s)")
        self.current_phase = 'attack'
        self.jammer_active = True
        time.sleep(10)
        
        # Phase 3: Recovery (15 seconds)
        print("\n[Monitor] Starting Phase 3: RECOVERY - Jammer isolated (15s)")
        self.current_phase = 'recovery'
        self.jammer_active = False
        time.sleep(15)
        
        print("\n[Monitor] Experiment complete!")
    
    def run(self):
        """Start monitor agent"""
        threading.Thread(target=self.simulate_network_traffic, daemon=True).start()
        threading.Thread(target=self.simulate_phases, daemon=True).start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[Monitor] Shutting down...")

if __name__ == '__main__':
    monitor = MonitorAgent()
    monitor.run()
