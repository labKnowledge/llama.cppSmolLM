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
    <title>System Monitor and Chat</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.7.0/chart.min.js"></script>
</head>
<body>
    <h1 class="text-4xl font-bold my-6">System Monitor and Chat</h1>
    
    <div class="container">
        <div class="chat-container">
            <AIChatInterface></AIChatInterface>
        </div>
        
        <div class="monitor-container">
            <system-monitor></system-monitor>
        </div>
    </div>

   

    <script>
        class AIChatInterface extends HTMLElement {
            constructor() {
                super();
                this.attachShadow({ mode: 'open' });
            }

            connectedCallback() {
                this.render();
                this.setupEventListeners();
                this.loadSettings();
            }

            render() {
                this.shadowRoot.innerHTML = `
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
                    
                    :host {
                    display: block;
                    font-family: 'Poppins', sans-serif;
                    height: 100vh;
                    }

                    .container {
                    height: 100%;
                    display: flex;
                    flex-direction: column;
                    padding: 1rem;
                    }

                    .chat-container {
                    flex-grow: 1;
                    overflow-y: auto;
                    margin-bottom: 1rem;
                    }

                    .message-bubble {
                    max-width: 80%;
                    word-wrap: break-word;
                    padding: 0.5rem 1rem;
                    margin-bottom: 0.5rem;
                    border-radius: 1rem;
                    }

                    .user-message {
                    background-color: #DCF8C6;
                    margin-left: auto;
                    }

                    .ai-message {
                    background-color: #E9E9EB;
                    }

                    .input-container {
                    display: flex;
                    gap: 0.5rem;
                    }

                    input {
                    flex-grow: 1;
                    padding: 0.5rem;
                    border: 1px solid #ccc;
                    border-radius: 0.25rem;
                    }

                    button {
                    padding: 0.5rem 1rem;
                    background-color: #4F46E5;
                    color: white;
                    border: none;
                    border-radius: 0.25rem;
                    cursor: pointer;
                    }

                    button:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                    }

                    .theme-toggle, .settings-toggle {
                    position: absolute;
                    top: 1rem;
                    width: 2rem;
                    height: 2rem;
                    background: none;
                    border: none;
                    cursor: pointer;
                    }

                    .theme-toggle {
                    right: 1rem;
                    }

                    .settings-toggle {
                    right: 3.5rem;
                    }

                    .settings-dialog {
                    display: none;
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0, 0, 0, 0.5);
                    justify-content: center;
                    align-items: center;
                    }

                    .settings-content {
                    background-color: white;
                    padding: 1rem;
                    border-radius: 0.5rem;
                    width: 80%;
                    max-width: 500px;
                    }

                    .settings-content h2 {
                    margin-top: 0;
                    }

                    .settings-content label {
                    display: block;
                    margin-bottom: 0.5rem;
                    }

                    .settings-content input,
                    .settings-content textarea {
                    width: 100%;
                    margin-bottom: 1rem;
                    padding: 0.5rem;
                    }

                    .settings-buttons {
                    display: flex;
                    justify-content: flex-end;
                    gap: 0.5rem;
                    }

                    @media (min-width: 768px) {
                    .container {
                        max-width: 80%;
                        margin: 0 auto;
                        padding: 2rem;
                    }
                    }
                </style>

                <div class="container">
                    <h1>AI Chat Interface</h1>
                    <button class="theme-toggle">🌓</button>
                    <button class="settings-toggle">⚙️</button>
                    <div class="chat-container"></div>
                    <div class="input-container">
                    <input type="text" placeholder="Type your message...">
                    <button>Send</button>
                    </div>
                </div>

                <div class="settings-dialog">
                    <div class="settings-content">
                    <h2>Settings</h2>
                    <label>
                        API URL:
                        <input type="text" id="apiUrl">
                    </label>
                    <label>
                        System Prompt:
                        <textarea id="systemPrompt" rows="4"></textarea>
                    </label>
                    <div class="settings-buttons">
                        <button id="cancelSettings">Cancel</button>
                        <button id="saveSettings">Save</button>
                    </div>
                    </div>
                </div>
                `;
            }

            setupEventListeners() {
                const input = this.shadowRoot.querySelector('input');
                const sendButton = this.shadowRoot.querySelector('button:not(.theme-toggle):not(.settings-toggle)');
                const themeToggle = this.shadowRoot.querySelector('.theme-toggle');
                const settingsToggle = this.shadowRoot.querySelector('.settings-toggle');
                const settingsDialog = this.shadowRoot.querySelector('.settings-dialog');
                const saveSettingsButton = this.shadowRoot.querySelector('#saveSettings');
                const cancelSettingsButton = this.shadowRoot.querySelector('#cancelSettings');

                input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
                });

                sendButton.addEventListener('click', () => this.sendMessage());
                themeToggle.addEventListener('click', () => this.toggleTheme());
                settingsToggle.addEventListener('click', () => this.toggleSettings());
                saveSettingsButton.addEventListener('click', () => this.saveSettings());
                cancelSettingsButton.addEventListener('click', () => this.toggleSettings());
            }

            loadSettings() {
                const apiUrlInput = this.shadowRoot.querySelector('#apiUrl');
                const systemPromptInput = this.shadowRoot.querySelector('#systemPrompt');

                apiUrlInput.value = localStorage.getItem('apiUrl') || 'https://ai-smol.5nlcr7.easypanel.host/v1/chat/completions';
                systemPromptInput.value = localStorage.getItem('systemPrompt') || '';
            }

            toggleTheme() {
                document.body.classList.toggle('dark');
            }

            toggleSettings() {
                const settingsDialog = this.shadowRoot.querySelector('.settings-dialog');
                settingsDialog.style.display = settingsDialog.style.display === 'flex' ? 'none' : 'flex';
            }

            saveSettings() {
                const apiUrlInput = this.shadowRoot.querySelector('#apiUrl');
                const systemPromptInput = this.shadowRoot.querySelector('#systemPrompt');

                localStorage.setItem('apiUrl', apiUrlInput.value);
                localStorage.setItem('systemPrompt', systemPromptInput.value);
                this.toggleSettings();
            }

            async sendMessage() {
                const input = this.shadowRoot.querySelector('input');
                const sendButton = this.shadowRoot.querySelector('button:not(.theme-toggle):not(.settings-toggle)');
                const chatContainer = this.shadowRoot.querySelector('.chat-container');

                const userMessage = input.value.trim();
                if (!userMessage) return;

                this.addMessage('user', userMessage);
                input.value = '';
                sendButton.disabled = true;

                const apiUrl = localStorage.getItem('apiUrl') || 'https://ai-smol.5nlcr7.easypanel.host/v1/chat/completions';
                const systemPrompt = localStorage.getItem('systemPrompt') || '';

                try {
                const response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                    model: 'gpt-3.5-turbo',
                    messages: [
                        { role: 'system', content: systemPrompt },
                        { role: 'user', content: userMessage }
                    ],
                    stream: true,
                    }),
                });

                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let aiMessage = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    const lines = chunk.split('\n');

                    for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') continue;
                        try {
                        const parsed = JSON.parse(data);
                        const content = parsed.choices[0].delta.content;
                        if (content) {
                            aiMessage += content;
                            this.updateAIMessage(aiMessage);
                        }
                        } catch (error) {
                        console.error('Error parsing JSON:', error);
                        }
                    }
                    }
                }
                } catch (error) {
                console.error('Error:', error);
                this.addMessage('ai', `Error: ${error.message}`);
                }

                sendButton.disabled = false;
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            addMessage(role, content) {
                const chatContainer = this.shadowRoot.querySelector('.chat-container');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message-bubble ${role}-message`;
                messageDiv.textContent = content;
                chatContainer.appendChild(messageDiv);
            }

            updateAIMessage(content) {
                const chatContainer = this.shadowRoot.querySelector('.chat-container');
                let aiMessage = chatContainer.querySelector('.ai-message:last-child');
                if (!aiMessage) {
                aiMessage = document.createElement('div');
                aiMessage.className = 'message-bubble ai-message';
                chatContainer.appendChild(aiMessage);
                }
                aiMessage.textContent = content;
            }
        }

        customElements.define('ai-chat-interface', AIChatInterface);

        // Define the SystemMonitor web component
        class SystemMonitor extends HTMLElement {
        constructor() {
            super();
            this.attachShadow({ mode: 'open' });
        }

        connectedCallback() {
            this.render();
            this.setupEventListeners();
        }

        render() {
            this.shadowRoot.innerHTML = `
            <style>
                :host {
                display: block;
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
            
            <h1>System Monitor</h1>
            
            <div id="deviceInfo">
                <h2>Server Specifications</h2>
                <div class="info-grid">
                <div class="info-item">
                    <span class="info-icon">🖥️</span>
                    <div class="info-content">
                    <span class="info-label">Operating System</span>
                    <span class="info-value" id="os"></span>
                    </div>
                </div>
                <div class="info-item">
                    <span class="info-icon">🔢</span>
                    <div class="info-content">
                    <span class="info-label">CPU</span>
                    <span class="info-value" id="cpu"></span>
                    </div>
                </div>
                <div class="info-item">
                    <span class="info-icon">💾</span>
                    <div class="info-content">
                    <span class="info-label">Total Memory</span>
                    <span class="info-value" id="totalMemory"></span>
                    </div>
                </div>
                <div class="info-item">
                    <span class="info-icon">💽</span>
                    <div class="info-content">
                    <span class="info-label">Disk Space</span>
                    <span class="info-value" id="diskSpace"></span>
                    </div>
                </div>
                <div class="info-item">
                    <span class="info-icon">🏠</span>
                    <div class="info-content">
                    <span class="info-label">Hostname</span>
                    <span class="info-value" id="hostname"></span>
                    </div>
                </div>
                <div class="info-item">
                    <span class="info-icon">🔌</span>
                    <div class="info-content">
                    <span class="info-label">Network</span>
                    <span class="info-value" id="network"></span>
                    </div>
                </div>
                </div>
            </div>
            
            <div class="grid">
                <div class="card cpu">
                <h3>CPU</h3>
                <p id="cpuUsage"></p>
                <div class="subtitle" id="cpuLoad"></div>
                <canvas id="cpuChart"></canvas>
                </div>
                <div class="card memory">
                <h3>Memory</h3>
                <p id="memoryUsage"></p>
                <div class="subtitle" id="memoryDetails"></div>
                </div>
                <div class="card disk">
                <h3>Disk</h3>
                <p id="diskUsage"></p>
                <div class="subtitle" id="diskDetails"></div>
                </div>
                <div class="card network">
                <h3>Network</h3>
                <p id="networkUsage"></p>
                </div>
            </div>
            
            <p id="updateTime">Last updated: <span id="lastUpdateTime"></span></p>
            `;
        }

        setupEventListeners() {
            this.updateData();
            setInterval(() => this.updateData(), 2000);
        }

        updateData() {
            fetch('/data')
            .then(response => response.json())
            .then(data => {
                this.updateSystemInfo(data);
                this.updateUsageInfo(data);
                this.updateCharts(data);
            })
            .catch(error => console.error('Error:', error));
        }

        updateSystemInfo(data) {
            this.shadowRoot.getElementById('os').textContent = `${data.system} ${data.release}`;
            this.shadowRoot.getElementById('cpu').textContent = data.processor;
            this.shadowRoot.getElementById('totalMemory').textContent = `${data.memory.total} GB`;
            this.shadowRoot.getElementById('diskSpace').textContent = `${data.disk.total} GB`;
            this.shadowRoot.getElementById('hostname').textContent = data.node_name;
            this.shadowRoot.getElementById('network').textContent = data.network_info;
        }

        updateUsageInfo(data) {
            this.shadowRoot.getElementById('cpuUsage').textContent = `${data.cpu_usage}%`;
            this.shadowRoot.getElementById('cpuLoad').textContent = `Load ${data.cpu_load}`;
            this.shadowRoot.getElementById('memoryUsage').textContent = `${data.memory.percent}%`;
            this.shadowRoot.getElementById('memoryDetails').textContent = `${data.memory.used} GB / ${data.memory.total} GB`;
            this.shadowRoot.getElementById('diskUsage').textContent = `${data.disk.percent}%`;
            this.shadowRoot.getElementById('diskDetails').textContent = `${data.disk.used} GB / ${data.disk.total} GB`;
            this.shadowRoot.getElementById('networkUsage').textContent = `↓ ${data.network.bytes_recv} MB ↑ ${data.network.bytes_sent} MB`;
            this.shadowRoot.getElementById('lastUpdateTime').textContent = new Date().toLocaleTimeString();
        }

            updateCharts(data) {
                // Update CPU chart
                const currentTime = new Date().toLocaleTimeString();
                
                this.chartData.labels.push(currentTime);
                this.chartData.datasets[0].data.push(data.cpu_usage);

                // Keep only the last 10 data points
                if (this.chartData.labels.length > 10) {
                this.chartData.labels.shift();
                this.chartData.datasets[0].data.shift();
                }

                // Update the chart
                this.cpuChart.update();
            }
        }

        // Register the custom element
        customElements.define('system-monitor', SystemMonitor);
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