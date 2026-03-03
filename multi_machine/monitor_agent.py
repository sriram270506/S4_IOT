#!/usr/bin/env python3
"""
Monitor/Jammer Agent
- Sends network metrics to controller (ping, throughput)
- Generates pseudo-jammer traffic (UDP flood)
- Runs on the Monitor laptop (192.168.1.102)
"""

import json
import socket
import threading
import time
import subprocess
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [MONITOR] %(message)s'
)
logger = logging.getLogger(__name__)


class MonitorAgent:
    """Network monitoring and pseudo-jamming agent"""
    
    def __init__(self, config_file):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.controller_ip = self.config['network']['controller_ip']
        self.controller_port = self.config['network']['controller_port']
        self.monitor_ip = self.config['network']['monitor_ip']
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Get MAC address of this laptop
        self.my_mac = self._get_mac_address()
        
        self.running = True
        self.jammer_active = False
        self.jammer_thread = None
        
        logger.info(f"Monitor Agent initialized (MAC: {self.my_mac})")
    
    def _get_mac_address(self):
        """Get MAC address of primary network interface"""
        try:
            # Try common interface names
            for iface in ['eth0', 'wlan0', 'en0', 'en1']:
                try:
                    output = subprocess.check_output(
                        ['ifconfig', iface],
                        text=True,
                        stderr=subprocess.DEVNULL
                    )
                    
                    # Parse MAC from output
                    for line in output.split('\n'):
                        if 'ether' in line or 'HWaddr' in line:
                            parts = line.split()
                            for part in parts:
                                if ':' in part and len(part) == 17:
                                    return part.lower()
                except:
                    continue
            
            # Fallback: use a mock MAC
            return 'aa:bb:cc:dd:ee:ff'
        
        except Exception as e:
            logger.warning(f"Failed to get MAC: {e}, using mock")
            return 'aa:bb:cc:dd:ee:ff'
    
    def start(self):
        """Start monitor agent"""
        # Start metrics reporter thread
        reporter_thread = threading.Thread(target=self._reporter_loop, daemon=True)
        reporter_thread.start()
        
        logger.info("Monitor Agent started")
    
    def _measure_ping_latency(self, target='8.8.8.8'):
        """Measure ping latency to target"""
        try:
            output = subprocess.check_output(
                ['ping', '-c', '1', '-W', '1000', target],
                text=True,
                stderr=subprocess.DEVNULL
            )
            
            # Parse ping output
            for line in output.split('\n'):
                if 'time=' in line:
                    # Extract time value
                    import re
                    match = re.search(r'time=(\d+\.?\d*)', line)
                    if match:
                        return float(match.group(1))
            
            return 999.0  # Timeout
        
        except Exception as e:
            logger.debug(f"Ping failed: {e}")
            return 999.0
    
    def _measure_local_throughput(self):
        """Mock measure of local throughput"""
        # In real scenario, would measure actual UDP throughput
        # For now, return 0 when jammer is active, 9.0 when idle
        if self.jammer_active:
            return 0.0
        else:
            return 9.0
    
    def _get_jammer_packet_rate(self):
        """Get current jammer packet rate"""
        if self.jammer_active:
            return self.config['jammer']['packet_rate_pps']
        else:
            return 0
    
    def _scan_channels(self):
        """Scan WiFi channels for interference"""
        try:
            output = subprocess.check_output(
                ['iw', 'dev', 'wlan0', 'scan'],
                text=True,
                stderr=subprocess.DEVNULL
            )
            
            # Simple mock implementation
            return {
                'channel_6': {'noise': -90, 'interference': 20 if self.jammer_active else 5},
                'channel_11': {'noise': -92, 'interference': 5}
            }
        
        except Exception:
            # Return mock data
            return {
                'channel_6': {'noise': -90, 'interference': 80 if self.jammer_active else 10},
                'channel_11': {'noise': -92, 'interference': 5}
            }
    
    def _reporter_loop(self):
        """Periodically send metrics to controller"""
        interval = 1.0  # Send every 1 second
        
        while self.running:
            try:
                ping_latency = self._measure_ping_latency()
                throughput = self._measure_local_throughput()
                pkt_rate = self._get_jammer_packet_rate()
                
                metrics = {
                    'source': 'monitor_agent',
                    'timestamp': time.time(),
                    'monitor_metrics': {
                        'my_mac': self.my_mac,
                        'ping_latency_ms': ping_latency,
                        'ping_target': '8.8.8.8',
                        'local_throughput_mbps': throughput,
                        'jammer_active': self.jammer_active,
                        'jammer_packet_rate_pps': pkt_rate,
                        'channel_scans': self._scan_channels()
                    }
                }
                
                # Send to controller
                self.socket.sendto(
                    json.dumps(metrics).encode('utf-8'),
                    (self.controller_ip, self.controller_port)
                )
                
                if self.jammer_active:
                    logger.debug(f"Sent jammer metrics: {pkt_rate}pps, latency={ping_latency:.1f}ms")
                else:
                    logger.debug(f"Sent baseline metrics: latency={ping_latency:.1f}ms")
                
            except Exception as e:
                logger.error(f"Reporter loop error: {e}")
            
            time.sleep(interval)
    
    def activate_jammer(self):
        """Activate UDP packet flood (pseudo-jamming)"""
        if self.jammer_active:
            logger.warning("Jammer already active")
            return
        
        logger.warning("🚨 ACTIVATING JAMMER 🚨")
        self.jammer_active = True
        
        # Start jammer thread
        self.jammer_thread = threading.Thread(target=self._jammer_loop, daemon=True)
        self.jammer_thread.start()
    
    def deactivate_jammer(self):
        """Stop UDP packet flood"""
        logger.info("Deactivating jammer...")
        self.jammer_active = False
        
        if self.jammer_thread:
            self.jammer_thread.join(timeout=2)
            self.jammer_thread = None
        
        logger.info("Jammer stopped")
    
    def _jammer_loop(self):
        """Send UDP packets at high rate"""
        jammer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        jammer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        packet_size = self.config['jammer']['packet_size_bytes']
        target_rate = self.config['jammer']['packet_rate_pps']
        interval_per_packet = 1.0 / target_rate  # seconds per packet
        
        # Create dummy payload
        payload = b'X' * packet_size
        
        logger.info(f"Jammer thread started: {target_rate}pps, {packet_size}B packets")
        
        try:
            while self.jammer_active:
                try:
                    # Send to broadcast address (causes interference)
                    jammer_socket.sendto(payload, ('255.255.255.255', 12345))
                    
                    # Sleep to maintain target rate
                    time.sleep(interval_per_packet)
                
                except Exception as e:
                    logger.debug(f"Jammer send error: {e}")
                    time.sleep(0.001)
        
        except Exception as e:
            logger.error(f"Jammer thread error: {e}")
        
        finally:
            jammer_socket.close()
            logger.info("Jammer socket closed")
    
    def stop(self):
        """Stop monitor agent"""
        if self.jammer_active:
            self.deactivate_jammer()
        
        self.running = False
        self.socket.close()
        logger.info("Monitor Agent stopped")


def main():
    import sys
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    
    agent = MonitorAgent(config_file)
    agent.start()
    
    try:
        # For testing: activate jammer at 10 seconds
        for i in range(100):
            time.sleep(1)
            if i == 10:
                agent.activate_jammer()
            elif i == 20:
                agent.deactivate_jammer()
    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        agent.stop()


if __name__ == '__main__':
    main()
