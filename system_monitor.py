import psutil
import platform
from flask import Flask, render_template_string, jsonify
import threading
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>System Monitor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.7.0/chart.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            padding: 20px;
            background-color: #1a1b26;
            color: #a9b1d6;
        }
        h1, h2 {
            color: #c0caf5;
            text-align: center;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .card {
            background: #24283b;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .card h3 {
            margin-top: 0;
            font-size: 18px;
            color: #7aa2f7;
        }
        .card p {
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
        }
        .card .subtitle {
            font-size: 14px;
            color: #565f89;
        }
        .cpu { border-left: 4px solid #ff9e64; }
        .memory { border-left: 4px solid #7dcfff; }
        .disk { border-left: 4px solid #9ece6a; }
        .network { border-left: 4px solid #bb9af7; }
        #deviceInfo {
            background-color: #24283b;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .info-item {
            display: flex;
            align-items: center;
            padding: 10px;
            background-color: #1a1b26;
            border-radius: 6px;
        }
        .info-icon {
            font-size: 24px;
            margin-right: 10px;
            color: #7aa2f7;
        }
        .info-content {
            display: flex;
            flex-direction: column;
        }
        .info-label {
            font-size: 14px;
            color: #565f89;
        }
        .info-value {
            font-size: 16px;
            font-weight: bold;
            color: #c0caf5;
        }
        #updateTime {
            text-align: center;
            font-style: italic;
            margin-top: 20px;
            color: #565f89;
        }
    </style>
</head>
<body>
    <h1>System Monitor</h1>
    
    <div id="deviceInfo">
        <h2>Server Specifications</h2>
        <div class="info-grid">
            <div class="info-item">
                <span class="info-icon">🖥️</span>
                <div class="info-content">
                    <span class="info-label">Operating System</span>
                    <span class="info-value">{{ system }} {{ release }}</span>
                </div>
            </div>
            <div class="info-item">
                <span class="info-icon">🔢</span>
                <div class="info-content">
                    <span class="info-label">CPU</span>
                    <span class="info-value">{{ processor }}</span>
                </div>
            </div>
            <div class="info-item">
                <span class="info-icon">💾</span>
                <div class="info-content">
                    <span class="info-label">Total Memory</span>
                    <span class="info-value">{{ memory.total }} GB</span>
                </div>
            </div>
            <div class="info-item">
                <span class="info-icon">💽</span>
                <div class="info-content">
                    <span class="info-label">Disk Space</span>
                    <span class="info-value">{{ disk.total }} GB</span>
                </div>
            </div>
            <div class="info-item">
                <span class="info-icon">🏠</span>
                <div class="info-content">
                    <span class="info-label">Hostname</span>
                    <span class="info-value">{{ node_name }}</span>
                </div>
            </div>
            <div class="info-item">
                <span class="info-icon">🔌</span>
                <div class="info-content">
                    <span class="info-label">Network</span>
                    <span class="info-value">{{ network_info }}</span>
                </div>
            </div>
        </div>
    </div>
    
    <div class="grid">
        <div class="card cpu">
            <h3>CPU</h3>
            <p id="cpuUsage">{{ cpu_usage }}%</p>
            <div class="subtitle" id="cpuLoad">Load {{ cpu_load }}</div>
            <canvas id="cpuChart"></canvas>
        </div>
        <div class="card memory">
            <h3>Memory</h3>
            <p id="memoryUsage">{{ memory.percent }}%</p>
            <div class="subtitle" id="memoryDetails">{{ memory.used }} GB / {{ memory.total }} GB</div>
        </div>
        <div class="card disk">
            <h3>Disk</h3>
            <p id="diskUsage">{{ disk.percent }}%</p>
            <div class="subtitle" id="diskDetails">{{ disk.used }} GB / {{ disk.total }} GB</div>
        </div>
        <div class="card network">
            <h3>Network</h3>
            <p id="networkUsage">↓ {{ network.bytes_recv }} MB ↑ {{ network.bytes_sent }} MB</p>
        </div>
    </div>
    
    <p id="updateTime">Last updated: <span id="lastUpdateTime"></span></p>

    <script>
        function updateData() {
            fetch('/data')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('cpuUsage').textContent = data.cpu_usage + '%';
                    document.getElementById('cpuLoad').textContent = 'Load ' + data.cpu_load;
                    document.getElementById('memoryUsage').textContent = data.memory.percent + '%';
                    document.getElementById('memoryDetails').textContent = data.memory.used + ' GB / ' + data.memory.total + ' GB';
                    document.getElementById('diskUsage').textContent = data.disk.percent + '%';
                    document.getElementById('diskDetails').textContent = data.disk.used + ' GB / ' + data.disk.total + ' GB';
                    document.getElementById('networkUsage').textContent = '↓ ' + data.network.bytes_recv + ' MB ↑ ' + data.network.bytes_sent + ' MB';
                    document.getElementById('lastUpdateTime').textContent = new Date().toLocaleTimeString();
                    
                    // Update CPU chart
                    cpuChart.data.labels.push(new Date().toLocaleTimeString());
                    cpuChart.data.datasets[0].data.push(data.cpu_usage);
                    if (cpuChart.data.labels.length > 10) {
                        cpuChart.data.labels.shift();
                        cpuChart.data.datasets[0].data.shift();
                    }
                    cpuChart.update();
                })
                .catch(error => console.error('Error:', error));
        }

        setInterval(updateData, 2000);  // Update every 2 seconds

        // Initialize CPU usage chart
        var ctx = document.getElementById('cpuChart').getContext('2d');
        var cpuChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU Usage',
                    data: [],
                    borderColor: 'rgb(255, 158, 100)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    try:
        return render_template_string(HTML_TEMPLATE, **get_system_info())
    except Exception as e:
        app.logger.error(f"Error in index route: {str(e)}")
        return "An error occurred while rendering the page", 500

@app.route('/data')
def data():
    try:
        return jsonify(get_system_info())
    except Exception as e:
        app.logger.error(f"Error in data route: {str(e)}")
        return jsonify({"error": "An error occurred while fetching data"}), 500

def get_system_info():
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        cpu_load = ", ".join([f"{x:.2f}" for x in psutil.getloadavg()])
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        return {
            'system': platform.system(),
            'node_name': platform.node(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'cpu_usage': cpu_usage,
            'cpu_load': cpu_load,
            'memory': {
                'percent': memory.percent,
                'used': round(memory.used / (1024 * 1024 * 1024), 1),
                'total': round(memory.total / (1024 * 1024 * 1024), 1)
            },
            'disk': {
                'percent': disk.percent,
                'used': round(disk.used / (1024 * 1024 * 1024), 1),
                'total': round(disk.total / (1024 * 1024 * 1024), 1)
            },
            'network': {
                'bytes_recv': round(network.bytes_recv / (1024 * 1024), 2),
                'bytes_sent': round(network.bytes_sent / (1024 * 1024), 2)
            },
            'network_info': 'N/A'  # Simplified for now
        }
    except Exception as e:
        app.logger.error(f"Error in get_system_info: {str(e)}")
        raise

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)