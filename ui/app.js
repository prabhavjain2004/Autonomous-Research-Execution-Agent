/**
 * Autonomous Research Agent - Web UI Client
 * 
 * This JavaScript application manages the WebSocket connection to the backend,
 * handles real-time updates, and provides interactive UI functionality.
 * 
 * Requirements: 10.1-10.12
 */

class ResearchAgentUI {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;
        this.currentSessionId = null;
        this.currentResult = null;
        this.logs = [];
        this.currentLogFilter = 'all';
        
        this.init();
    }

    /**
     * Initialize the UI and establish WebSocket connection
     */
    init() {
        this.setupEventListeners();
        this.connect();
    }

    /**
     * Setup event listeners for UI elements
     */
    setupEventListeners() {
        // Start research button
        document.getElementById('startButton').addEventListener('click', () => {
            this.startResearch();
        });

        // Enter key in textarea
        document.getElementById('researchGoal').addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                this.startResearch();
            }
        });

        // Log level filter
        document.getElementById('logLevelFilter').addEventListener('change', (e) => {
            this.currentLogFilter = e.target.value;
            this.renderLogs();
        });

        // Clear logs button
        document.getElementById('clearLogsButton').addEventListener('click', () => {
            this.logs = [];
            this.renderLogs();
        });

        // Export buttons
        document.getElementById('exportJsonButton').addEventListener('click', () => {
            this.exportResults('json');
        });

        document.getElementById('exportMarkdownButton').addEventListener('click', () => {
            this.exportResults('markdown');
        });

        // Tab buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Refresh history button
        document.getElementById('refreshHistoryButton').addEventListener('click', () => {
            this.loadSessionHistory();
        });
    }

    /**
     * Establish WebSocket connection
     */
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
                this.loadSessionHistory();
            };

            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus(false);
                this.attemptReconnect();
            };
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.updateConnectionStatus(false);
            this.attemptReconnect();
        }
    }

    /**
     * Attempt to reconnect to WebSocket
     */
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
            setTimeout(() => this.connect(), this.reconnectDelay);
        } else {
            console.error('Max reconnection attempts reached');
            this.addLog({
                level: 'ERROR',
                message: 'Failed to connect to server. Please refresh the page.',
                timestamp: new Date().toISOString()
            });
        }
    }

    /**
     * Update connection status indicator
     */
    updateConnectionStatus(connected) {
        const statusIndicator = document.querySelector('.status-indicator');
        const statusText = document.querySelector('.status-text');

        if (connected) {
            statusIndicator.classList.remove('disconnected');
            statusIndicator.classList.add('connected');
            statusText.textContent = 'Connected';
        } else {
            statusIndicator.classList.remove('connected');
            statusIndicator.classList.add('disconnected');
            statusText.textContent = 'Disconnected';
        }
    }

    /**
     * Handle incoming WebSocket messages
     */
    handleMessage(message) {
        console.log('Received message:', message.type, message.data);

        switch (message.type) {
            case 'connected':
                this.addLog({
                    level: 'INFO',
                    message: message.data.message,
                    timestamp: message.timestamp
                });
                break;

            case 'research_started':
                this.currentSessionId = message.data.session_id;
                this.updateSessionId(message.data.session_id);
                this.addLog({
                    level: 'INFO',
                    message: `Research started: ${message.data.goal}`,
                    timestamp: message.timestamp
                });
                this.disableStartButton(true);
                break;

            case 'state_update':
                this.updateState(message.data);
                break;

            case 'log':
                this.addLog(message.data);
                break;

            case 'confidence':
                this.updateConfidence(message.data);
                break;

            case 'result':
                this.displayResult(message.data);
                this.disableStartButton(false);
                break;

            case 'error':
                this.handleError(message.data);
                this.disableStartButton(false);
                break;

            case 'sessions':
                this.displaySessionHistory(message.data.sessions);
                break;

            case 'session_history':
                this.displaySessionDetails(message.data);
                break;

            case 'execution_state':
                if (message.data.status === 'running') {
                    this.currentSessionId = message.data.session_id;
                    this.updateSessionId(message.data.session_id);
                    this.disableStartButton(true);
                }
                break;

            default:
                console.log('Unknown message type:', message.type);
        }
    }

    /**
     * Start a new research task
     */
    startResearch() {
        const goal = document.getElementById('researchGoal').value.trim();

        if (!goal) {
            alert('Please enter a research goal');
            return;
        }

        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            alert('Not connected to server. Please wait...');
            return;
        }

        // Clear previous results
        document.getElementById('resultsSection').style.display = 'none';
        this.currentResult = null;

        // Reset confidence scores
        this.resetConfidenceScores();

        // Send start research message
        this.ws.send(JSON.stringify({
            type: 'start_research',
            goal: goal
        }));
    }

    /**
     * Update current state display
     */
    updateState(data) {
        document.getElementById('currentState').textContent = data.state || '-';
        document.getElementById('activeAgent').textContent = data.agent || '-';
        document.getElementById('currentAction').textContent = data.action || '-';

        this.addLog({
            level: 'INFO',
            message: `State: ${data.state} | Agent: ${data.agent || 'None'} | Action: ${data.action || 'None'}`,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Update session ID display
     */
    updateSessionId(sessionId) {
        document.getElementById('sessionId').textContent = sessionId;
    }

    /**
     * Update confidence score for an agent
     */
    updateConfidence(data) {
        const agentName = data.agent.toLowerCase().replace(' agent', '');
        const score = data.score;
        const percentage = Math.round(score * 100);

        const barElement = document.getElementById(`confidence${this.capitalize(agentName)}`);
        const valueElement = document.getElementById(`confidence${this.capitalize(agentName)}Value`);

        if (barElement && valueElement) {
            barElement.style.width = `${percentage}%`;
            valueElement.textContent = `${percentage}%`;

            // Update bar color based on score
            barElement.classList.remove('low', 'medium');
            if (score < 0.6) {
                barElement.classList.add('low');
            } else if (score < 0.8) {
                barElement.classList.add('medium');
            }
        }

        this.addLog({
            level: 'INFO',
            message: `${data.agent} confidence: ${percentage}%`,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Reset all confidence scores
     */
    resetConfidenceScores() {
        ['Research', 'Analyst', 'Strategy'].forEach(agent => {
            const barElement = document.getElementById(`confidence${agent}`);
            const valueElement = document.getElementById(`confidence${agent}Value`);
            if (barElement && valueElement) {
                barElement.style.width = '0%';
                valueElement.textContent = '-';
                barElement.classList.remove('low', 'medium');
            }
        });
    }

    /**
     * Add a log entry
     */
    addLog(logData) {
        this.logs.push({
            timestamp: logData.timestamp || new Date().toISOString(),
            level: logData.level || 'INFO',
            message: logData.message || '',
            event_type: logData.event_type
        });

        // Keep only last 500 logs
        if (this.logs.length > 500) {
            this.logs = this.logs.slice(-500);
        }

        this.renderLogs();
    }

    /**
     * Render logs with current filter
     */
    renderLogs() {
        const container = document.getElementById('logsContainer');
        const filteredLogs = this.currentLogFilter === 'all' 
            ? this.logs 
            : this.logs.filter(log => log.level === this.currentLogFilter);

        if (filteredLogs.length === 0) {
            container.innerHTML = '<div style="color: #94a3b8; text-align: center; padding: 20px;">No logs to display</div>';
            return;
        }

        container.innerHTML = filteredLogs.map(log => {
            const timestamp = new Date(log.timestamp).toLocaleTimeString();
            return `
                <div class="log-entry">
                    <span class="log-timestamp">${timestamp}</span>
                    <span class="log-level ${log.level}">${log.level}</span>
                    <span class="log-message">${this.escapeHtml(log.message)}</span>
                </div>
            `;
        }).join('');

        // Auto-scroll to bottom
        container.scrollTop = container.scrollHeight;
    }

    /**
     * Display research results
     */
    displayResult(result) {
        this.currentResult = result;
        document.getElementById('resultsSection').style.display = 'block';

        // Display formatted view
        this.displayFormattedResult(result);

        // Display JSON view
        document.getElementById('jsonResults').textContent = JSON.stringify(result, null, 2);

        this.addLog({
            level: 'INFO',
            message: 'Research completed successfully',
            timestamp: new Date().toISOString()
        });

        // Refresh history
        this.loadSessionHistory();
    }

    /**
     * Display formatted result view
     */
    displayFormattedResult(result) {
        const container = document.getElementById('formattedResults');

        let html = `
            <div class="result-meta">
                <div class="result-meta-item">
                    <strong>Session ID:</strong>
                    <span>${result.session_id || 'N/A'}</span>
                </div>
                <div class="result-meta-item">
                    <strong>Goal:</strong>
                    <span>${this.escapeHtml(result.goal || 'N/A')}</span>
                </div>
                <div class="result-meta-item">
                    <strong>Timestamp:</strong>
                    <span>${new Date(result.timestamp).toLocaleString()}</span>
                </div>
                <div class="result-meta-item">
                    <strong>Overall Confidence:</strong>
                    <span>${Math.round((result.overall_confidence || 0) * 100)}%</span>
                </div>
            </div>
        `;

        // Insights
        if (result.insights && result.insights.length > 0) {
            html += '<h3>📊 Key Insights</h3><ul>';
            result.insights.forEach(insight => {
                html += `<li>${this.escapeHtml(insight)}</li>`;
            });
            html += '</ul>';
        }

        // Recommendations
        if (result.recommendations && result.recommendations.length > 0) {
            html += '<h3>💡 Strategic Recommendations</h3><ul>';
            result.recommendations.forEach(rec => {
                // Handle both string and object recommendations
                if (typeof rec === 'string') {
                    html += `<li>${this.escapeHtml(rec)}</li>`;
                } else if (typeof rec === 'object' && rec !== null) {
                    // If it's an object, display its properties
                    const recText = rec.recommendation || rec.title || rec.description || JSON.stringify(rec);
                    html += `<li>${this.escapeHtml(recText)}</li>`;
                }
            });
            html += '</ul>';
        }

        // Sources
        if (result.sources && result.sources.length > 0) {
            html += '<h3>🔗 Sources</h3><ul>';
            result.sources.forEach(source => {
                html += `<li><a href="${source.url}" target="_blank">${this.escapeHtml(source.title || source.url)}</a></li>`;
            });
            html += '</ul>';
        }

        // Agents Involved
        if (result.agents_involved && result.agents_involved.length > 0) {
            html += '<h3>🤖 Agents Involved</h3><ul>';
            result.agents_involved.forEach(agent => {
                html += `<li>${this.escapeHtml(agent)}</li>`;
            });
            html += '</ul>';
        }

        container.innerHTML = html;
    }

    /**
     * Handle error messages
     */
    handleError(data) {
        this.addLog({
            level: 'ERROR',
            message: `Error: ${data.error}`,
            timestamp: new Date().toISOString()
        });

        alert(`Error: ${data.error}`);
    }

    /**
     * Load session history
     */
    loadSessionHistory() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'get_sessions',
                limit: 50
            }));
        }
    }

    /**
     * Display session history
     */
    displaySessionHistory(sessions) {
        const container = document.getElementById('historyContainer');

        if (!sessions || sessions.length === 0) {
            container.innerHTML = '<p class="empty-state">No previous sessions</p>';
            return;
        }

        container.innerHTML = sessions.map(session => {
            const date = new Date(session.created_at).toLocaleString();
            return `
                <div class="history-item" onclick="ui.loadSessionDetails('${session.session_id}')">
                    <div class="history-item-header">
                        <div class="history-item-goal">${this.escapeHtml(session.goal || 'Unknown goal')}</div>
                        <div class="history-item-status ${session.status}">${session.status}</div>
                    </div>
                    <div class="history-item-meta">
                        ${date} • Session ID: ${session.session_id}
                    </div>
                </div>
            `;
        }).join('');
    }

    /**
     * Load details for a specific session
     */
    loadSessionDetails(sessionId) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'get_session_history',
                session_id: sessionId
            }));
        }
    }

    /**
     * Display session details
     */
    displaySessionDetails(history) {
        if (!history) {
            alert('Session history not found');
            return;
        }

        // Display the final result if available
        if (history.final_result) {
            this.displayResult(history.final_result);
        } else {
            alert('No results available for this session');
        }
    }

    /**
     * Export results in specified format
     */
    exportResults(format) {
        if (!this.currentResult) {
            alert('No results to export');
            return;
        }

        let content, filename, mimeType;

        if (format === 'json') {
            content = JSON.stringify(this.currentResult, null, 2);
            filename = `research_${this.currentResult.session_id}.json`;
            mimeType = 'application/json';
        } else if (format === 'markdown') {
            content = this.generateMarkdown(this.currentResult);
            filename = `research_${this.currentResult.session_id}.md`;
            mimeType = 'text/markdown';
        }

        this.downloadFile(content, filename, mimeType);
    }

    /**
     * Generate Markdown from result
     */
    generateMarkdown(result) {
        let md = `# Research Report\n\n`;
        md += `**Session ID:** ${result.session_id}\n\n`;
        md += `**Goal:** ${result.goal}\n\n`;
        md += `**Date:** ${new Date(result.timestamp).toLocaleString()}\n\n`;
        md += `**Overall Confidence:** ${Math.round((result.overall_confidence || 0) * 100)}%\n\n`;
        md += `---\n\n`;

        if (result.insights && result.insights.length > 0) {
            md += `## Key Insights\n\n`;
            result.insights.forEach(insight => {
                md += `- ${insight}\n`;
            });
            md += `\n`;
        }

        if (result.recommendations && result.recommendations.length > 0) {
            md += `## Strategic Recommendations\n\n`;
            result.recommendations.forEach(rec => {
                // Handle both string and object recommendations
                if (typeof rec === 'string') {
                    md += `- ${rec}\n`;
                } else if (typeof rec === 'object' && rec !== null) {
                    const recText = rec.recommendation || rec.title || rec.description || JSON.stringify(rec);
                    md += `- ${recText}\n`;
                }
            });
            md += `\n`;
        }

        if (result.sources && result.sources.length > 0) {
            md += `## Sources\n\n`;
            result.sources.forEach(source => {
                md += `- [${source.title || source.url}](${source.url})\n`;
            });
            md += `\n`;
        }

        if (result.agents_involved && result.agents_involved.length > 0) {
            md += `## Agents Involved\n\n`;
            result.agents_involved.forEach(agent => {
                md += `- ${agent}\n`;
            });
            md += `\n`;
        }

        return md;
    }

    /**
     * Download file
     */
    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Switch between tabs
     */
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
            if (button.dataset.tab === tabName) {
                button.classList.add('active');
            }
        });

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });

        if (tabName === 'formatted') {
            document.getElementById('formattedView').classList.add('active');
        } else if (tabName === 'json') {
            document.getElementById('jsonView').classList.add('active');
        }
    }

    /**
     * Disable/enable start button
     */
    disableStartButton(disabled) {
        const button = document.getElementById('startButton');
        button.disabled = disabled;
        button.textContent = disabled ? '⏳ Research in Progress...' : '🚀 Start Research';
    }

    /**
     * Capitalize first letter
     */
    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the UI when DOM is ready
let ui;
document.addEventListener('DOMContentLoaded', () => {
    ui = new ResearchAgentUI();
});
