#!/usr/bin/env python3
"""
Flask Dashboard for SDN Controller
- Real-time visualization of network metrics
- Live throughput, RSSI, and channel status
- Event log of controller decisions
"""

from flask import Flask, render_template_string, jsonify
import json
import threading
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DashboardServer:
    """Flask-based real-time dashboard"""
    
    def __init__(self, controller, config_file):
        self.controller = controller
        
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.app = Flask(__name__)
        self.metrics_log = []
        self.setup_routes()
        
        logger.info("Dashboard server initialized")
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template_string(self.get_html_template())
        
        @self.app.route('/api/status')
        def api_status():
            return jsonify(self.controller.get_status())
        
        @self.app.route('/api/metrics')
        def api_metrics():
            return jsonify({
                'metrics': self.metrics_log[-100:],  # Last 100 data points
                'count': len(self.metrics_log)
            })
        
        @self.app.route('/api/actions')
        def api_actions():
            return jsonify({
                'actions': self.controller.get_actions_log(),
                'count': len(self.controller.get_actions_log())
            })
    
    def log_metrics(self, ap_metrics, monitor_metrics):
        """Log metrics for dashboard"""
        self.metrics_log.append({
            'timestamp': time.time(),
            'ap_metrics': ap_metrics,
            'monitor_metrics': monitor_metrics
        })
    
    def get_html_template(self):
        """HTML template for dashboard"""
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>SDN Testbed Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .status-bar {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 20px;
        }
        
        .status-item {
            text-align: center;
            padding: 15px;
            background: #f0f0f0;
            border-radius: 8px;
        }
        
        .status-item label {
            display: block;
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
            font-weight: bold;
        }
        
        .status-item .value {
            font-size: 24px;
            font-weight: bold;
            color: #2a5298;
        }
        
        .status-item.alert .value {
            color: #e74c3c;
        }
        
        .charts-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .chart-box {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .chart-box h3 {
            margin-bottom: 15px;
            color: #2a5298;
        }
        
        .events-log {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .events-log h3 {
            margin-bottom: 15px;
            color: #2a5298;
        }
        
        .event-item {
            padding: 10px;
            border-left: 4px solid #2a5298;
            background: #f9f9f9;
            margin-bottom: 10px;
            border-radius: 4px;
            font-size: 14px;
        }
        
        .event-item.detection {
            border-left-color: #e74c3c;
            background: #ffe6e6;
        }
        
        .event-item.response {
            border-left-color: #27ae60;
            background: #e6ffe6;
        }
        
        .event-time {
            font-size: 12px;
            color: #999;
            margin-right: 10px;
        }
        
        .event-text {
            font-weight: 500;
        }
        
        @media (max-width: 1200px) {
            .charts-container {
                grid-template-columns: 1fr;
            }
        }
        
        @media (max-width: 800px) {
            .status-bar {
                grid-template-columns: 1fr 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 SDN Multi-Machine Testbed</h1>
        <p>Real-time Network Monitoring & Jammer Detection</p>
    </div>
    
    <div class="status-bar">
        <div class="status-item" id="status-jammer">
            <label>Jammer Status</label>
            <div class="value">Monitoring</div>
        </div>
        <div class="status-item" id="status-channel">
            <label>Current Channel</label>
            <div class="value">6</div>
        </div>
        <div class="status-item" id="status-clients">
            <label>Connected Clients</label>
            <div class="value">0</div>
        </div>
        <div class="status-item" id="status-actions">
            <label>Controller Actions</label>
            <div class="value">0</div>
        </div>
    </div>
    
    <div class="charts-container">
        <div class="chart-box">
            <h3>📊 Network Throughput (Mbps)</h3>
            <canvas id="throughputChart"></canvas>
        </div>
        <div class="chart-box">
            <h3>📡 RSSI Signal Strength (dBm)</h3>
            <canvas id="rssiChart"></canvas>
        </div>
    </div>
    
    <div class="events-log">
        <h3>📋 Controller Event Log</h3>
        <div id="eventsList"></div>
    </div>
    
    <script>
        // Initialize charts
        let throughputCtx = document.getElementById('throughputChart').getContext('2d');
        let rssiCtx = document.getElementById('rssiChart').getContext('2d');
        
        let throughputChart = new Chart(throughputCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Phone 1',
                        data: [],
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.1,
                        fill: true
                    },
                    {
                        label: 'Phone 2',
                        data: [],
                        borderColor: '#2ecc71',
                        backgroundColor: 'rgba(46, 204, 113, 0.1)',
                        tension: 0.1,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true, max: 10 }
                }
            }
        });
        
        let rssiChart = new Chart(rssiCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Phone 1 RSSI',
                        data: [],
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        tension: 0.1,
                        fill: true
                    },
                    {
                        label: 'Phone 2 RSSI',
                        data: [],
                        borderColor: '#f39c12',
                        backgroundColor: 'rgba(243, 156, 18, 0.1)',
                        tension: 0.1,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: false, min: -100, max: -30 }
                }
            }
        });
        
        // Update dashboard every 2 seconds
        setInterval(updateDashboard, 2000);
        
        function updateDashboard() {
            // Update status
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('status-channel').innerHTML = 
                        `<label>Current Channel</label><div class="value">${data.current_channel}</div>`;
                    document.getElementById('status-clients').innerHTML = 
                        `<label>Connected Clients</label><div class="value">${data.ap_metrics.connected_clients ? data.ap_metrics.connected_clients.length : 0}</div>`;
                    document.getElementById('status-actions').innerHTML = 
                        `<label>Controller Actions</label><div class="value">${data.actions_count}</div>`;
                    
                    if (data.jammer_detected) {
                        document.getElementById('status-jammer').classList.add('alert');
                        document.getElementById('status-jammer').innerHTML = 
                            `<label>⚠️ JAMMER DETECTED</label><div class="value">${data.jammer_mac}</div>`;
                    }
                });
            
            // Update charts with mock data (in real implementation, fetch actual metrics)
            updateCharts();
            
            // Update events log
            fetch('/api/actions')
                .then(r => r.json())
                .then(data => {
                    let eventsList = document.getElementById('eventsList');
                    eventsList.innerHTML = '';
                    
                    // Show last 5 events
                    let actions = data.actions.slice(-5).reverse();
                    actions.forEach(action => {
                        let eventDiv = document.createElement('div');
                        eventDiv.className = 'event-item ' + (action.action === 'jammer_detected' ? 'detection' : 'response');
                        
                        let time = new Date(action.timestamp * 1000).toLocaleTimeString();
                        let text = action.action.replace(/_/g, ' ').toUpperCase();
                        
                        eventDiv.innerHTML = `
                            <span class="event-time">${time}</span>
                            <span class="event-text">${text}</span>
                        `;
                        
                        eventsList.appendChild(eventDiv);
                    });
                });
        }
        
        function updateCharts() {
            // Add mock data points
            let now = new Date().toLocaleTimeString();
            
            // Generate mock throughput
            let phone1_tput = Math.random() * 10;
            let phone2_tput = Math.random() * 10;
            
            if (throughputChart.data.labels.length > 30) {
                throughputChart.data.labels.shift();
                throughputChart.data.datasets[0].data.shift();
                throughputChart.data.datasets[1].data.shift();
            }
            
            throughputChart.data.labels.push(now);
            throughputChart.data.datasets[0].data.push(phone1_tput);
            throughputChart.data.datasets[1].data.push(phone2_tput);
            throughputChart.update();
            
            // Generate mock RSSI
            let rssi1 = -55 - Math.random() * 30;
            let rssi2 = -55 - Math.random() * 30;
            
            if (rssiChart.data.labels.length > 30) {
                rssiChart.data.labels.shift();
                rssiChart.data.datasets[0].data.shift();
                rssiChart.data.datasets[1].data.shift();
            }
            
            rssiChart.data.labels.push(now);
            rssiChart.data.datasets[0].data.push(rssi1);
            rssiChart.data.datasets[1].data.push(rssi2);
            rssiChart.update();
        }
        
        // Initial update
        updateDashboard();
    </script>
</body>
</html>
        '''
    
    def run(self, host='0.0.0.0', port=8080, debug=False):
        """Start Flask server"""
        logger.info(f"Dashboard running on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)


def main():
    # This would be called from orchestrator
    # For now, just show that it works
    print("Dashboard module loaded successfully")


if __name__ == '__main__':
    main()
