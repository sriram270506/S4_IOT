#!/usr/bin/env python3
"""
AP Agent - Laptop 2
Simulates WiFi AP, generates network metrics
"""

import socket
import json
import time
import random
import threading

class APAgent:
    def __init__(self, controller_ip='192.168.1.100', controller_port=9000):
        self.controller_ip = controller_ip
        self.controller_port = controller_port
        
        self.current_channel = 6
        self.current_phase = 'baseline'
        self.jammer_active = False
        
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket.bind(('192.168.1.101', 9001))
        
        print("\n" + "="*70)
        print("AP AGENT - LAPTOP 2")
        print("="*70)
        print(f"Listening on 192.168.1.101:9001")
        print(f"Controller: {self.controller_ip}:{self.controller_port}")
        print("="*70)
    
    def get_metrics(self):
        """Generate realistic network metrics based on phase"""
        
        if self.current_phase == 'baseline':
            throughput = 8.5 + random.uniform(-1, 1)
            rssi = -45 + random.randint(-2, 2)
            loss = random.uniform(0, 0.5)
            
        elif self.current_phase == 'attack':
            if self.jammer_active:
                throughput = 0.8 + random.uniform(-0.3, 0.3)
                rssi = -65 + random.randint(-5, 5)
                loss = random.uniform(75, 85)
            else:
                throughput = 8.5 + random.uniform(-1, 1)
                rssi = -45 + random.randint(-2, 2)
                loss = random.uniform(0, 0.5)
        
        elif self.current_phase == 'recovery':
            throughput = 8.5 + random.uniform(-1, 1)
            rssi = -45 + random.randint(-2, 2)
            loss = random.uniform(0, 0.5)
        
        else:
            throughput = 0
            rssi = -100
            loss = 100
        
        return {
            'throughput': round(max(0, throughput), 2),
            'rssi': rssi,
            'loss': round(max(0, loss), 1),
            'channel': self.current_channel,
            'phase': self.current_phase
        }
    
    def send_metrics(self):
        """Send metrics to controller"""
        while True:
            try:
                metrics = self.get_metrics()
                
                message = json.dumps({
                    'type': 'ap_metrics',
                    'timestamp': time.time(),
                    'data': metrics
                })
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(message.encode(), (self.controller_ip, self.controller_port))
                sock.close()
                
                print(f"[AP] Ch:{self.current_channel} | {metrics['throughput']:.2f}Mbps | RSSI:{metrics['rssi']}dBm | Phase:{self.current_phase}")
                
                time.sleep(2)
            except Exception as e:
                print(f"[AP] Send error: {e}")
                time.sleep(2)
    
    def listen_for_commands(self):
        """Listen for controller commands"""
        while True:
            try:
                data, addr = self.listen_socket.recvfrom(4096)
                message = json.loads(data.decode())
                
                if message.get('type') == 'controller_action':
                    action = message.get('action', {})
                    
                    if action.get('action') == 'switch_channel':
                        new_channel = action.get('new_channel', 6)
                        print(f"\n[AP] 📡 Channel switch command received: {self.current_channel} → {new_channel}")
                        
                        # Simulate channel switch
                        time.sleep(2)
                        self.current_channel = new_channel
                        print(f"[AP] ✓ Channel switched to {new_channel}")
                        
            except Exception as e:
                pass
    
    def simulate_phases(self):
        """Simulate experiment phases"""
        time.sleep(2)  # Wait for connections
        
        # Phase 1: Baseline (10 seconds)
        print("\n[AP] Starting Phase 1: BASELINE (10s)")
        self.current_phase = 'baseline'
        self.jammer_active = False
        time.sleep(10)
        
        # Phase 2: Attack (10 seconds)
        print("\n[AP] Starting Phase 2: ATTACK (10s)")
        self.current_phase = 'attack'
        self.jammer_active = True
        time.sleep(10)
        
        # Phase 3: Recovery (15 seconds)
        print("\n[AP] Starting Phase 3: RECOVERY (15s)")
        self.current_phase = 'recovery'
        self.jammer_active = False
        time.sleep(15)
        
        print("\n[AP] Experiment complete!")
    
    def run(self):
        """Start AP agent"""
        threading.Thread(target=self.send_metrics, daemon=True).start()
        threading.Thread(target=self.listen_for_commands, daemon=True).start()
        threading.Thread(target=self.simulate_phases, daemon=True).start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[AP] Shutting down...")

if __name__ == '__main__':
    ap = APAgent()
    ap.run()
