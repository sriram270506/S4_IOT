#!/usr/bin/env python3
"""
SDN Controller Server
- Listens for metrics from AP and Monitor agents
- Implements jammer detection algorithm
- Makes decisions (MAC blacklist, channel switch)
- Provides metrics to Flask dashboard
"""

import json
import socket
import threading
import time
from datetime import datetime
from collections import deque
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [CONTROLLER] %(message)s'
)
logger = logging.getLogger(__name__)


class JammerDetectionEngine:
    """Detects jammer based on packet rate, RSSI, and throughput"""
    
    def __init__(self, config):
        self.config = config['detection']
        self.baseline_rssi = -55
        self.baseline_throughput = 9.0
        self.baseline_established = False
        
    def establish_baseline(self, rssi, throughput):
        """Establish baseline metrics during first 5 seconds"""
        self.baseline_rssi = rssi
        self.baseline_throughput = throughput
        self.baseline_established = True
        logger.info(f"Baseline established: RSSI={rssi}dBm, Throughput={throughput:.2f}Mbps")
    
    def detect_jammer(self, pkt_rate, rssi, throughput):
        """
        Multi-factor jammer detection
        Returns: (detected: bool, confidence: float, reason: str)
        """
        if not self.baseline_established:
            return False, 0, "baseline_not_established"
        
        score = 0
        reasons = []
        
        # Factor 1: High packet rate
        if pkt_rate > self.config['packet_rate_threshold_pps']:
            score += 40
            reasons.append(f"high_pkt_rate({pkt_rate}pps)")
        
        # Factor 2: RSSI degradation
        rssi_drop = self.baseline_rssi - rssi
        if rssi_drop > self.config['rssi_degradation_threshold_dbm']:
            score += 30
            reasons.append(f"rssi_drop({rssi_drop}dBm)")
        
        # Factor 3: Throughput loss
        if self.baseline_throughput > 0:
            throughput_loss = (self.baseline_throughput - throughput) / self.baseline_throughput
            if throughput_loss > (self.config['throughput_loss_threshold_percent'] / 100.0):
                score += 30
                reasons.append(f"throughput_loss({throughput_loss*100:.1f}%)")
        
        detected = score >= self.config['detection_confidence_threshold']
        reason_str = " + ".join(reasons) if reasons else "no_anomalies"
        
        return detected, score, reason_str


class ControllerServer:
    """Main SDN controller server"""
    
    def __init__(self, config_file):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.detector = JammerDetectionEngine(self.config)
        self.server_socket = None
        self.running = True
        
        # Metrics storage
        self.latest_ap_metrics = {}
        self.latest_monitor_metrics = {}
        self.metrics_history = deque(maxlen=1000)
        self.controller_actions = []
        
        # State tracking
        self.jammer_detected = False
        self.jammer_mac = None
        self.current_channel = 6
        self.channels_switched = False
        self.ap_address = None
        self.monitor_address = None
        
        logger.info("Controller initialized")
    
    def start(self):
        """Start UDP server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        controller_ip = self.config['network']['controller_ip']
        controller_port = self.config['network']['controller_port']
        
        self.server_socket.bind((controller_ip, controller_port))
        logger.info(f"Controller listening on {controller_ip}:{controller_port}")
        
        # Start listener thread
        listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
        listener_thread.start()
        
        # Start detection/action thread
        action_thread = threading.Thread(target=self._detection_loop, daemon=True)
        action_thread.start()
        
        logger.info("Controller threads started")
    
    def _listener_loop(self):
        """Listen for incoming metrics from agents"""
        while self.running:
            try:
                data, addr = self.server_socket.recvfrom(4096)
                message = json.loads(data.decode('utf-8'))
                
                source = message.get('source')
                if source == 'ap_agent':
                    self.ap_address = addr
                    self.latest_ap_metrics = message.get('ap_metrics', {})
                    logger.debug(f"AP metrics received: CH={self.latest_ap_metrics.get('channel')}")
                
                elif source == 'monitor_agent':
                    self.monitor_address = addr
                    self.latest_monitor_metrics = message.get('monitor_metrics', {})
                    logger.debug(f"Monitor metrics received: PKT_RATE={self.latest_monitor_metrics.get('jammer_packet_rate_pps')}pps")
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from {addr}")
            except Exception as e:
                logger.error(f"Listener error: {e}")
            
            time.sleep(0.01)
    
    def _detection_loop(self):
        """Periodic jammer detection and response"""
        check_interval = self.config['detection']['detection_check_interval_seconds']
        start_time = time.time()
        baseline_duration = 5  # Establish baseline for first 5 seconds
        
        while self.running:
            elapsed = time.time() - start_time
            
            # Skip if no metrics yet
            if not self.latest_ap_metrics or not self.latest_monitor_metrics:
                time.sleep(check_interval)
                continue
            
            # Extract current metrics
            rssi_list = list(self.latest_ap_metrics.get('rssi_per_client', {}).values())
            avg_rssi = sum(rssi_list) / len(rssi_list) if rssi_list else -55
            
            pkt_rate = self.latest_monitor_metrics.get('jammer_packet_rate_pps', 0)
            
            # Calculate throughput (mock for now, will be from iperf3)
            throughput = self.latest_monitor_metrics.get('local_throughput_mbps', 9.0)
            
            # Establish baseline if not already done
            if not self.detector.baseline_established and elapsed < baseline_duration:
                self.detector.establish_baseline(avg_rssi, 9.0)
            
            # Perform detection
            if self.detector.baseline_established and not self.jammer_detected:
                detected, confidence, reason = self.detector.detect_jammer(pkt_rate, avg_rssi, throughput)
                
                if detected and elapsed > baseline_duration:
                    logger.warning(f"⚠️  JAMMER DETECTED! Confidence: {confidence:.1f}% ({reason})")
                    self._on_jammer_detected()
            
            # Handle recovery if jammer is isolated
            if self.jammer_detected and self.jammer_mac:
                if not self.channels_switched and elapsed > baseline_duration + 2.5:
                    logger.info("Initiating channel switch...")
                    self._switch_channel()
            
            time.sleep(check_interval)
    
    def _on_jammer_detected(self):
        """Handle jammer detection"""
        self.jammer_detected = True
        self.jammer_mac = self.latest_monitor_metrics.get('my_mac', 'unknown')
        
        action = {
            'timestamp': time.time(),
            'action': 'jammer_detected',
            'confidence': 85.5,
            'suspect_mac': self.jammer_mac,
            'channel': self.current_channel
        }
        self.controller_actions.append(action)
        logger.info(f"Action logged: {action['action']}")
        
        # Immediately blacklist MAC
        self._blacklist_mac()
    
    def _blacklist_mac(self):
        """Blacklist jammer MAC on AP"""
        if not self.jammer_mac or not self.ap_address:
            logger.error("Cannot blacklist: missing MAC or AP address")
            return
        
        # Send command to AP via UDP
        command = {
            'command': 'blacklist_mac',
            'target_mac': self.jammer_mac,
            'reason': 'jammer_flooding'
        }
        
        try:
            self.server_socket.sendto(
                json.dumps(command).encode('utf-8'),
                self.ap_address
            )
            
            action = {
                'timestamp': time.time(),
                'action': 'mac_blacklisted',
                'target_mac': self.jammer_mac,
                'result': 'sent'
            }
            self.controller_actions.append(action)
            logger.info(f"✓ MAC blacklist command sent: {self.jammer_mac}")
            
        except Exception as e:
            logger.error(f"Failed to send blacklist command: {e}")
    
    def _switch_channel(self):
        """Switch AP to different channel"""
        if not self.ap_address:
            logger.error("Cannot switch channel: missing AP address")
            return
        
        new_channel = self.config['wifi']['ap_channel_switch']
        
        command = {
            'command': 'switch_channel',
            'target_channel': new_channel,
            'reason': 'jammer_on_current_channel'
        }
        
        try:
            self.server_socket.sendto(
                json.dumps(command).encode('utf-8'),
                self.ap_address
            )
            
            self.channels_switched = True
            self.current_channel = new_channel
            
            action = {
                'timestamp': time.time(),
                'action': 'channel_switch',
                'from_channel': 6,
                'to_channel': new_channel,
                'result': 'sent'
            }
            self.controller_actions.append(action)
            logger.info(f"✓ Channel switch command sent: 6 → {new_channel}")
            
        except Exception as e:
            logger.error(f"Failed to send channel switch command: {e}")
    
    def get_status(self):
        """Return current controller status"""
        return {
            'timestamp': time.time(),
            'jammer_detected': self.jammer_detected,
            'jammer_mac': self.jammer_mac,
            'current_channel': self.current_channel,
            'ap_metrics': self.latest_ap_metrics,
            'monitor_metrics': self.latest_monitor_metrics,
            'actions_count': len(self.controller_actions),
            'latest_actions': self.controller_actions[-5:] if self.controller_actions else []
        }
    
    def get_metrics_history(self):
        """Return stored metrics for dashboard"""
        return list(self.metrics_history)
    
    def get_actions_log(self):
        """Return all controller actions"""
        return self.controller_actions
    
    def stop(self):
        """Stop the controller"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("Controller stopped")


def main():
    import sys
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    
    controller = ControllerServer(config_file)
    controller.start()
    
    try:
        while True:
            time.sleep(1)
            status = controller.get_status()
            # Periodic logging
            if status['jammer_detected']:
                logger.info(f"Status: JAMMER DETECTED at MAC {status['jammer_mac']}")
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        controller.stop()


if __name__ == '__main__':
    main()
