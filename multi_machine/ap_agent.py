#!/usr/bin/env python3
"""
AP Agent
- Reports WiFi AP metrics (connected clients, RSSI, channel utilization)
- Executes controller commands (channel switching, MAC blacklisting)
- Runs on the AP laptop (192.168.1.101)
"""

import json
import socket
import subprocess
import threading
import time
import logging
import re

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [AP_AGENT] %(message)s'
)
logger = logging.getLogger(__name__)


class APAgent:
    """WiFi AP management agent"""
    
    def __init__(self, config_file):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.ap_interface = self.config['wifi']['ap_interface']
        self.controller_ip = self.config['network']['controller_ip']
        self.controller_port = self.config['network']['controller_port']
        self.ap_ip = self.config['network']['ap_ip']
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Listen on AP's own port for controller commands
        self.command_port = 9001
        self.socket.bind((self.ap_ip, self.command_port))
        
        self.running = True
        self.current_channel = 6
        self.connected_clients = {}
        
        logger.info(f"AP Agent initialized on {self.ap_ip}:{self.command_port}")
    
    def start(self):
        """Start AP agent"""
        # Start metrics reporter thread
        reporter_thread = threading.Thread(target=self._reporter_loop, daemon=True)
        reporter_thread.start()
        
        # Start command listener thread
        listener_thread = threading.Thread(target=self._command_listener, daemon=True)
        listener_thread.start()
        
        logger.info("AP Agent threads started")
    
    def _get_connected_clients(self):
        """Query hostapd for connected WiFi clients"""
        try:
            # Use hostapd_cli to get connected stations
            output = subprocess.check_output(
                ['hostapd_cli', '-i', self.ap_interface, 'list_sta'],
                text=True
            )
            
            clients = {}
            for mac in output.strip().split('\n'):
                if mac:
                    clients[mac] = {'mac': mac, 'rssi': self._get_client_rssi(mac)}
            
            return clients
        except Exception as e:
            logger.warning(f"Failed to get connected clients: {e}")
            # Return mock data for testing
            return {
                '00:11:22:33:44:55': {'mac': '00:11:22:33:44:55', 'rssi': -55},
                '00:11:22:33:44:66': {'mac': '00:11:22:33:44:66', 'rssi': -58}
            }
    
    def _get_client_rssi(self, client_mac):
        """Get RSSI for specific client"""
        try:
            output = subprocess.check_output(
                ['hostapd_cli', '-i', self.ap_interface, 'get_sta', client_mac],
                text=True
            )
            
            # Parse output to find RSSI
            for line in output.split('\n'):
                if 'rssi=' in line:
                    rssi = int(line.split('=')[1])
                    return rssi
            
            return -60
        except Exception:
            # Return mock value if command fails
            return -60
    
    def _get_channel_utilization(self):
        """Estimate channel utilization"""
        try:
            # This is a mock implementation
            # In real scenario, would use iw event logs or packet capture
            output = subprocess.check_output(['iwconfig', self.ap_interface], text=True)
            
            # Extract information if available
            if 'Link Quality' in output:
                match = re.search(r'Link Quality[=\s]*(\d+)/(\d+)', output)
                if match:
                    quality = int(match.group(1)) / int(match.group(2)) * 100
                    return quality
            
            return 50  # Mock value
        except Exception:
            return 50  # Mock value
    
    def _reporter_loop(self):
        """Periodically send metrics to controller"""
        interval = 2  # Send every 2 seconds
        
        while self.running:
            try:
                self.connected_clients = self._get_connected_clients()
                
                rssi_dict = {
                    client['mac']: client['rssi']
                    for client in self.connected_clients.values()
                }
                
                metrics = {
                    'source': 'ap_agent',
                    'timestamp': time.time(),
                    'ap_metrics': {
                        'channel': self.current_channel,
                        'connected_clients': list(self.connected_clients.keys()),
                        'num_clients': len(self.connected_clients),
                        'channel_utilization_percent': self._get_channel_utilization(),
                        'rssi_per_client': rssi_dict,
                        'tx_power': 20,
                        'bandwidth': '20MHz'
                    }
                }
                
                # Send to controller
                self.socket.sendto(
                    json.dumps(metrics).encode('utf-8'),
                    (self.controller_ip, self.controller_port)
                )
                
                logger.debug(f"Sent metrics: {len(self.connected_clients)} clients on CH{self.current_channel}")
                
            except Exception as e:
                logger.error(f"Reporter loop error: {e}")
            
            time.sleep(interval)
    
    def _command_listener(self):
        """Listen for controller commands"""
        self.socket.setblocking(False)
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(4096)
                command = json.loads(data.decode('utf-8'))
                
                cmd_type = command.get('command')
                logger.info(f"Received command: {cmd_type}")
                
                if cmd_type == 'switch_channel':
                    self._execute_channel_switch(command)
                elif cmd_type == 'blacklist_mac':
                    self._execute_mac_blacklist(command)
                else:
                    logger.warning(f"Unknown command: {cmd_type}")
                
            except BlockingIOError:
                pass
            except json.JSONDecodeError:
                logger.error("Failed to parse command JSON")
            except Exception as e:
                logger.error(f"Command listener error: {e}")
            
            time.sleep(0.1)
    
    def _execute_channel_switch(self, command):
        """Switch AP to new channel"""
        new_channel = command.get('target_channel')
        
        if not new_channel:
            logger.error("No target_channel specified")
            return
        
        try:
            # Execute channel switch via hostapd_cli
            result = subprocess.run(
                ['hostapd_cli', '-i', self.ap_interface, 'set_channel', str(new_channel)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.current_channel = new_channel
                logger.info(f"✓ Channel switched to {new_channel}")
                logger.warning(f"⚠️  Phones will auto-reconnect...")
            else:
                logger.error(f"Channel switch failed: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            logger.error("Channel switch command timed out")
        except FileNotFoundError:
            logger.error("hostapd_cli not found - running in mock mode")
            # In testing without real hostapd, just log the action
            self.current_channel = new_channel
            logger.info(f"[MOCK] Channel switched to {new_channel}")
        except Exception as e:
            logger.error(f"Failed to switch channel: {e}")
    
    def _execute_mac_blacklist(self, command):
        """Blacklist a MAC address"""
        target_mac = command.get('target_mac')
        
        if not target_mac:
            logger.error("No target_mac specified")
            return
        
        try:
            # Add MAC to denial list
            result = subprocess.run(
                ['hostapd_cli', '-i', self.ap_interface, 'deny_acl', 'add', target_mac],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Reload ACL
                subprocess.run(
                    ['hostapd_cli', '-i', self.ap_interface, 'reload_acl'],
                    capture_output=True,
                    timeout=5
                )
                logger.info(f"✓ MAC blacklisted: {target_mac}")
            else:
                logger.error(f"MAC blacklist failed: {result.stderr}")
        
        except FileNotFoundError:
            logger.error("hostapd_cli not found - running in mock mode")
            logger.info(f"[MOCK] MAC blacklisted: {target_mac}")
        except Exception as e:
            logger.error(f"Failed to blacklist MAC: {e}")
    
    def stop(self):
        """Stop AP agent"""
        self.running = False
        self.socket.close()
        logger.info("AP Agent stopped")


def main():
    import sys
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    
    agent = APAgent(config_file)
    agent.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        agent.stop()


if __name__ == '__main__':
    main()
