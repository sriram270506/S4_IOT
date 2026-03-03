#!/usr/bin/env python3
"""
SDN Dashboard - Real-time visualization
Run on any laptop with: python3 dashboard.py
Then open browser to: http://localhost:5000
"""

from flask import Flask, render_template_string, jsonify
import json
import socket
import threading
import time
from collections import deque
from datetime import datetime

app = Flask(__name__)

# Store metrics from all agents
metrics_history = {
    'throughput': deque(maxlen=100),
    'rssi': deque(maxlen=100),
    'packet_rate': deque(maxlen=100),
    'channel': deque(maxlen=100),
    'phase': deque(maxlen=100),
    'timestamps': deque(maxlen=100)
}

current_state = {
    'throughput': 0,
    'rssi': -50,
    'packet_rate': 0,
    'channel': 6,
    'phase': 'baseline',
    'jammer_detected': False,
    'jammer_isolated': False
}

# Create UDP listener socket
listener_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
listener_socket.bind(('0.0.0.0', 9002))

def listen_for_metrics():
    """Listen for metrics from controller and agents"""
    while True:
        try:
            data, addr = listener_socket.recvfrom(4096)
            message = json.loads(data.decode())
            
            agent_type = message.get('type')
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            if agent_type == 'ap_metrics':
                ap_data = message.get('data', {})
                current_state['throughput'] = ap_data.get('throughput', 0)
                current_state['rssi'] = ap_data.get('rssi', -50)
                current_state['channel'] = ap_data.get('channel', 6)
                current_state['phase'] = ap_data.get('phase', 'baseline')
            
            elif agent_type == 'monitor_metrics':
                mon_data = message.get('data', {})
                current_state['packet_rate'] = mon_data.get('packet_rate', 0)
            
            elif agent_type == 'controller_action':
                action = message.get('action', {})
                if action.get('action') == 'switch_channel':
                    current_state['jammer_detected'] = True
            
            # Add to history
            metrics_history['throughput'].append(current_state['throughput'])
            metrics_history['rssi'].append(current_state['rssi'])
            metrics_history['packet_rate'].append(current_state['packet_rate'])
            metrics_history['channel'].append(current_state['channel'])
            metrics_history['phase'].append(current_state['phase'])
            metrics_history['timestamps'].append(timestamp)
            
        except:
            pass

# HTML Dashboard Template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>SDN WiFi Testbed - Real-time Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f0f0f0; }
        .header { background: #1a1a2e; color: white; padding: 20px; text-align: center; }
        .container { max-width: 1400px; margin: 20px auto; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .metric { font-size: 24px; font-weight: bold; margin: 10px 0; }
        .metric-label { font-size: 12px; color: #666; text-transform: uppercase; }
        .chart-container { position: relative; height: 300px; }
        .status { padding: 10px; border-radius: 4px; margin: 5px 0; }
        .status.healthy { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .status.critical { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }
        .icon { font-size: 20px; margin-right: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 SDN WiFi Testbed - Real-time Monitoring</h1>
        <p>3-Laptop Distributed System with Jammer Detection</p>
    </div>
    
    <div class="container">
        <div class="grid-3">
            <div class="card">
                <div class="metric-label">Throughput</div>
                <div class="metric" id="throughput">0.00 Mbps</div>
                <div class="chart-container">
                    <canvas id="throughputChart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <div class="metric-label">RSSI Signal Strength</div>
                <div class="metric" id="rssi">-50 dBm</div>
                <div class="chart-container">
                    <canvas id="rssiChart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <div class="metric-label">Packet Rate (jammer detection)</div>
                <div class="metric" id="packetrate">0 pps</div>
                <div class="chart-container">
                    <canvas id="packetrateChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>Network Status</h2>
                <div id="status-container"></div>
            </div>
            
            <div class="card">
                <h2>Controller Actions</h2>
                <div id="actions-container"></div>
            </div>
        </div>
    </div>
    
    <script>
        // Chart.js instances
        let throughputChart, rssiChart, packetrateChart;
        
        function initCharts() {
            const ctx1 = document.getElementById('throughputChart').getContext('2d');
            throughputChart = new Chart(ctx1, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'Throughput (Mbps)', data: [], borderColor: '#007bff', tension: 0.1 }] },
                options: { responsive: true, maintainAspectRatio: false, legend: { display: false } }
            });
            
            const ctx2 = document.getElementById('rssiChart').getContext('2d');
            rssiChart = new Chart(ctx2, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'RSSI (dBm)', data: [], borderColor: '#28a745', tension: 0.1 }] },
                options: { responsive: true, maintainAspectRatio: false, legend: { display: false } }
            });
            
            const ctx3 = document.getElementById('packetrateChart').getContext('2d');
            packetrateChart = new Chart(ctx3, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'Packet Rate (pps)', data: [], borderColor: '#dc3545', tension: 0.1 }] },
                options: { responsive: true, maintainAspectRatio: false, legend: { display: false } }
            });
        }
        
        function updateDashboard() {
            fetch('/api/metrics')
                .then(r => r.json())
                .then(data => {
                    // Update current values
                    document.getElementById('throughput').innerText = data.throughput.toFixed(2) + ' Mbps';
                    document.getElementById('rssi').innerText = data.rssi + ' dBm';
                    document.getElementById('packetrate').innerText = data.packet_rate + ' pps';
                    
                    // Update charts
                    throughputChart.data.labels = data.timestamps;
                    throughputChart.data.datasets[0].data = data.throughput_history;
                    throughputChart.update();
                    
                    rssiChart.data.labels = data.timestamps;
                    rssiChart.data.datasets[0].data = data.rssi_history;
                    rssiChart.update();
                    
                    packetrateChart.data.labels = data.timestamps;
                    packetrateChart.data.datasets[0].data = data.packet_rate_history;
                    packetrateChart.update();
                    
                    // Update status
                    let statusHTML = '';
                    if (data.jammer_detected) {
                        statusHTML += '<div class="status critical"><span class="icon">🚨</span>Jammer Detected!</div>';
                    }
                    if (data.phase === 'baseline') {
                        statusHTML += '<div class="status healthy"><span class="icon">✓</span>Phase: BASELINE (Clean Network)</div>';
                    } else if (data.phase === 'attack') {
                        if (data.packet_rate > 5000) {
                            statusHTML += '<div class="status critical"><span class="icon">⚠️</span>Phase: ATTACK (Jammer Active)</div>';
                        }
                    } else if (data.phase === 'recovery') {
                        statusHTML += '<div class="status healthy"><span class="icon">✓</span>Phase: RECOVERY (Channel ' + data.channel + ')</div>';
                    }
                    
                    statusHTML += '<div class="status"><strong>Current Channel:</strong> ' + data.channel + '</div>';
                    statusHTML += '<div class="status"><strong>Throughput:</strong> ' + data.throughput.toFixed(2) + ' Mbps</div>';
                    
                    document.getElementById('status-container').innerHTML = statusHTML;
                    
                    // Actions
                    let actionsHTML = '';
                    if (data.jammer_detected) {
                        actionsHTML = '<div class="status warning"><strong>Controller Action:</strong><br>Switched to Channel ' + data.channel + '</div>';
                        actionsHTML += '<div class="status healthy"><strong>Result:</strong> Jammer Isolated</div>';
                    } else {
                        actionsHTML = '<div class="status healthy"><strong>Status:</strong> Monitoring...</div>';
                    }
                    
                    document.getElementById('actions-container').innerHTML = actionsHTML;
                });
        }
        
        initCharts();
        setInterval(updateDashboard, 1000);
        updateDashboard();
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/metrics')
def get_metrics():
    return jsonify({
        'throughput': current_state['throughput'],
        'rssi': current_state['rssi'],
        'packet_rate': current_state['packet_rate'],
        'channel': current_state['channel'],
        'phase': current_state['phase'],
        'jammer_detected': current_state['jammer_detected'],
        'throughput_history': list(metrics_history['throughput']),
        'rssi_history': list(metrics_history['rssi']),
        'packet_rate_history': list(metrics_history['packet_rate']),
        'timestamps': list(metrics_history['timestamps'])
    })

if __name__ == '__main__':
    # Start metric listener in background
    threading.Thread(target=listen_for_metrics, daemon=True).start()
    
    print("\n" + "="*70)
    print("SDN DASHBOARD")
    print("="*70)
    print("Open browser to: http://localhost:5000")
    print("="*70 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000)
