#!/usr/bin/env python3
"""
SDN Controller - Laptop 1
Monitors network metrics, detects jammer, makes decisions
"""

import socket
import json
import time
import threading
from datetime import datetime
from collections import defaultdict

class SDNController:
    def __init__(self, host='192.168.1.100', port=9000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.host, self.port))
        
        self.metrics = defaultdict(lambda: {"throughput": 0, "rssi": -50, "loss": 0})
        self.jammer_detected = False
        self.current_channel = 6
        self.detection_time = None
        self.all_metrics = []
        
        print("\n" + "="*70)
        print("SDN CONTROLLER - LAPTOP 1")
        print("="*70)
        print(f"Listening on {self.host}:{self.port}")
        print("="*70)
        
    def receive_metrics(self):
        """Receive metrics from AP and Monitor agents"""
        while True:
            try:
                data, addr = self.server_socket.recvfrom(4096)
                message = json.loads(data.decode())
                
                agent_type = message.get('type')
                timestamp = message.get('timestamp')
                
                if agent_type == 'ap_metrics':
                    self.metrics['ap'] = message.get('data', {})
                elif agent_type == 'monitor_metrics':
                    self.metrics['monitor'] = message.get('data', {})
                    
                # Store for later analysis
                self.all_metrics.append({
                    'time': timestamp,
                    'agent': agent_type,
                    'data': message.get('data', {})
                })
                
            except Exception as e:
                pass
    
    def analyze_and_decide(self):
        """Analyze metrics and make decisions"""
        while True:
            time.sleep(2)  # Check every 2 seconds
            
            if not self.metrics['ap'] or not self.metrics['monitor']:
                continue
            
            ap_data = self.metrics['ap']
            monitor_data = self.metrics['monitor']
            
            throughput = ap_data.get('throughput', 0)
            rssi = ap_data.get('rssi', -50)
            packet_rate = monitor_data.get('packet_rate', 0)
            
            # Detection logic
            if (packet_rate > 5000 and rssi < -60 and throughput < 2.0):
                if not self.jammer_detected:
                    self.jammer_detected = True
                    self.detection_time = datetime.now()
                    
                    print(f"\n[Controller] 🚨 JAMMER DETECTED!")
                    print(f"  Throughput: {throughput:.2f} Mbps")
                    print(f"  RSSI: {rssi} dBm")
                    print(f"  Packet Rate: {packet_rate} pps")
                    print(f"  Decision: Switch channel 6 → 11")
                    
                    # Send action to AP agent
                    self.send_action('ap_agent', {'action': 'switch_channel', 'new_channel': 11})
                    self.current_channel = 11
    
    def send_action(self, target, action):
        """Send action to AP agent"""
        try:
            message = json.dumps({
                'type': 'controller_action',
                'timestamp': time.time(),
                'action': action
            })
            
            # Send to AP agent on laptop 2
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(message.encode(), ('192.168.1.101', 9001))
            sock.close()
        except:
            pass
    
    def print_status(self):
        """Print controller status"""
        while True:
            time.sleep(5)
            
            if self.metrics['ap']:
                ap = self.metrics['ap']
                mon = self.metrics['monitor']
                
                print(f"\n[Controller Status]")
                print(f"  Channel: {self.current_channel}")
                print(f"  Throughput: {ap.get('throughput', 0):.2f} Mbps")
                print(f"  RSSI: {ap.get('rssi', -50)} dBm")
                print(f"  Packet Rate: {mon.get('packet_rate', 0)} pps")
                print(f"  Jammer: {'DETECTED ⚠️' if self.jammer_detected else 'Not detected'}")
    
    def run(self):
        """Start controller"""
        threading.Thread(target=self.receive_metrics, daemon=True).start()
        threading.Thread(target=self.analyze_and_decide, daemon=True).start()
        threading.Thread(target=self.print_status, daemon=True).start()
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.save_results()
            print("\n[Controller] Shutting down...")
    
    def save_results(self):
        """Save experiment results"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "system": "3-Laptop Distributed SDN",
            "jammer_detected": self.jammer_detected,
            "detection_time": self.detection_time.isoformat() if self.detection_time else None,
            "channel_switched": self.current_channel == 11,
            "metrics_count": len(self.all_metrics)
        }
        
        with open('controller_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"[Controller] Results saved to controller_results.json")

if __name__ == '__main__':
    controller = SDNController()
    controller.run()
