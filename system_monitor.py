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
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/4.0.2/marked.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.5.1/highlight.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.5.1/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.7.0/chart.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        body {
            font-family: 'Poppins', Arial, sans-serif;
            line-height: 1.6;
            background-color: #1a1b26;
            color: #a9b1d6;
            display: flex;
            flex-direction: column;
            height: 100vh;
            margin: 0;
        }
        .container {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        .chat-container {
            flex: 3;
            display: flex;
            flex-direction: column;
            padding: 20px;
        }
        .monitor-container {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
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
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }
        .message-bubble {
            max-width: 80%;
            word-wrap: break-word;
            margin-bottom: 10px;
            padding: 10px 15px;
            border-radius: 20px;
            font-size: 14px;
        }
        .user-message {
            align-self: flex-end;
            background-color: #7aa2f7;
            color: #ffffff;
            border-bottom-right-radius: 0;
        }
        .ai-message {
            align-self: flex-start;
            background-color: #414868;
            color: #c0caf5;
            border-bottom-left-radius: 0;
        }
        .chat-input {
            display: flex;
            padding: 20px;
            background-color: #24283b;
            border-top: 1px solid #414868;
        }
        .chat-input input {
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 20px;
            background-color: #414868;
            color: #c0caf5;
            margin-right: 10px;
        }
        .chat-input button {
            padding: 10px 20px;
            border: none;
            border-radius: 20px;
            background-color: #7aa2f7;
            color: #ffffff;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .chat-input button:hover {
            background-color: #5d8df3;
        }
        .typing-indicator {
            display: inline-block;
            width: 30px;
            height: 10px;
        }
        .typing-indicator::after {
            content: '...';
            animation: typing 1s steps(4, end) infinite;
        }
        @keyframes typing {
            0%, 20% { content: '.'; }
            40%, 60% { content: '..'; }
            80%, 100% { content: '...'; }
        }
        .theme-toggle, .settings-toggle {
            position: absolute;
            top: 20px;
            background-color: #414868;
            border: none;
            border-radius: 50%;
            padding: 10px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .theme-toggle:hover, .settings-toggle:hover {
            background-color: #565f89;
        }
        .theme-toggle {
            right: 20px;
        }
        .settings-toggle {
            right: 70px;
        }
        @media (max-width: 768px) {
            .container {
                flex-direction: column;
            }
            .chat-container, .monitor-container {
                flex: none;
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <h1 class="text-4xl font-bold my-6">System Monitor and Chat</h1>
    
    <div class="container">
        <div class="chat-container">
            <div class="relative">
                <button id="themeToggle" class="theme-toggle">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                    </svg>
                </button>
                <button id="settingsToggle" class="settings-toggle">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                </button>
            </div>
            <div id="chatMessages" class="chat-messages"></div>
            <div class="chat-input">
                <input type="text" id="userInput" placeholder="Type your message...">
                <button id="sendButton">Send</button>
            </div>
        </div>
        
        <div class="monitor-container">
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
        </div>
    </div>

    <!-- Settings Dialog -->
    <div id="settingsDialog" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center hidden">
        <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-xl w-full max-w-md">
            <h2 class="text-2xl font-bold mb-4 text-gray-800 dark:text-gray-200">Settings</h2>
            <div class="mb-4">
                <label for="apiUrl" class="block text-sm font-medium text-gray-700 dark:text-gray-300">API URL:</label>
                <input type="text" id="apiUrl" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600">
            </div>
            <div class="mb-4">
                <label for="systemPrompt" class="block text-sm font-medium text-gray-700 dark:text-gray-300">System Prompt:</label>
                <textarea id="systemPrompt" rows="4" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600"></textarea>
            </div>
            <div class="flex justify-end space-x-2">
                <button id="cancelSettings" class="px-4 py-2 bg-gray-300 text-gray-800 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-opacity-50 transition-colors duration-200">Cancel</button>
                <button id="saveSettings" class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-opacity-50 transition-colors duration-200">Save</button>
            </div>
        </div>
    </div>

    <script>

    // Chat Functionality
       let apiUrl = localStorage.getItem('apiUrl') || 'https://ai-smol.5nlcr7.easypanel.host/v1/chat/completions';
        const chatMessages = document.getElementById('chatMessages');
        const userInput = document.getElementById('userInput');
        const sendButton = document.getElementById('sendButton');
        const themeToggle = document.getElementById('themeToggle');
        const settingsToggle = document.getElementById('settingsToggle');
        const settingsDialog = document.getElementById('settingsDialog');
        const apiUrlInput = document.getElementById('apiUrl');
        const systemPromptInput = document.getElementById('systemPrompt');
        const saveSettingsButton = document.getElementById('saveSettings');
        const cancelSettingsButton = document.getElementById('cancelSettings');

        let conversation = [];
        let darkMode = false;

        // Load saved settings
        apiUrlInput.value = apiUrl;
        systemPromptInput.value = localStorage.getItem('systemPrompt') || '';

        themeToggle.addEventListener('click', toggleDarkMode);
        settingsToggle.addEventListener('click', toggleSettingsDialog);
        saveSettingsButton.addEventListener('click', saveSettings);
        cancelSettingsButton.addEventListener('click', toggleSettingsDialog);




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

       

        function toggleDarkMode() {
            darkMode = !darkMode;
            document.documentElement.classList.toggle('dark', darkMode);
        }

        function toggleSettingsDialog() {
            settingsDialog.classList.toggle('hidden');
        }

        function saveSettings() {
            apiUrl = apiUrlInput.value;
            localStorage.setItem('apiUrl', apiUrl);
            localStorage.setItem('systemPrompt', systemPromptInput.value);
            toggleSettingsDialog();
        }

       function addMessage(role, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message-bubble ${role === 'user' ? 'user-message' : 'ai-message'}`;
            messageDiv.innerHTML = `<span class="message-content"></span>`;
            chatMessages.appendChild(messageDiv);
            return messageDiv.querySelector('.message-content');
        }


        async function streamResponse(messages) {
            const messageContent = addMessage('assistant', '');
            let fullContent = '';

            try {
                const response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        model: 'gpt-3.5-turbo',
                        messages: messages,
                        stream: true,
                    }),
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();

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
                                    fullContent += content;
                                    messageContent.innerHTML = marked.parse(fullContent);
                                    highlightCode();
                                }
                            } catch (error) {
                                console.error('Error parsing JSON:', error);
                            }
                        }
                    }
                }
            } catch (error) {
                console.error('Error:', error);
                messageContent.innerHTML = `<span class="text-red-500">Error: ${error.message}</span>`;
            }

            chatMessages.scrollTop = chatMessages.scrollHeight;
            return fullContent;
        }

        function highlightCode() {
            document.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightBlock(block);
            });
        }

        async function sendMessage() {
            const userMessage = userInput.value.trim();
            if (!userMessage) return;

            const userMessageContent = addMessage('user', userMessage);
            userMessageContent.textContent = userMessage;
            userInput.value = '';
            sendButton.disabled = true;
            sendButton.innerHTML = '<span class="typing-indicator"></span>';

            conversation.push({ role: 'user', content: userMessage });

            const messages = [];
            const systemPrompt = localStorage.getItem('systemPrompt');
            if (systemPrompt) {
                messages.push({ role: 'system', content: systemPrompt });
            }
            messages.push(...conversation);

            const assistantResponse = await streamResponse(messages);
            conversation.push({ role: 'assistant', content: assistantResponse });

            sendButton.disabled = false;
            sendButton.innerHTML = 'Send';
        }

        sendButton.addEventListener('click', sendMessage);
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
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