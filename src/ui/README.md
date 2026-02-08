# Web User Interface

## Overview

The Web UI provides a real-time interface for interacting with the Autonomous Research Agent system. It features live updates, confidence score visualization, log monitoring, and result export capabilities.

## Features

### ✅ Real-Time Monitoring
- Live state updates showing current agent and action
- Real-time log streaming with filtering
- Confidence score visualization with progress bars
- WebSocket-based communication (no page refresh needed)

### ✅ Research Management
- Simple text input for research goals
- One-click research initiation
- Session tracking with unique IDs
- Research status indicators

### ✅ Results Display
- Formatted view with structured sections
- JSON view for raw data inspection
- Tab-based interface for easy switching
- Export to JSON and Markdown formats

### ✅ Session History
- Browse past research sessions
- View session details and results
- Chronological ordering
- Status indicators (completed, error, running)

### ✅ Log Viewer
- Live log streaming
- Filter by log level (DEBUG, INFO, WARNING, ERROR)
- Auto-scroll to latest entries
- Clear logs functionality
- Syntax-highlighted display

## Files

### `index.html`
Main HTML structure with semantic markup and accessibility features:
- Header with connection status
- Input section for research goals
- Status cards for current state
- Confidence score displays
- Live log viewer
- Results section with tabs
- Session history browser

### `styles.css`
Modern, responsive CSS styling:
- CSS custom properties for theming
- Flexbox and Grid layouts
- Smooth animations and transitions
- Mobile-responsive design
- Dark theme for logs
- Professional color scheme

### `app.js`
JavaScript WebSocket client application:
- `ResearchAgentUI` class for managing UI state
- WebSocket connection with auto-reconnect
- Real-time message handling
- Export functionality (JSON, Markdown)
- XSS protection with HTML escaping
- Tab management
- Log filtering

### `websocket_server.py`
FastAPI backend server:
- WebSocket endpoint for real-time communication
- Static file serving
- Health check endpoint
- Connection management
- Message broadcasting

### `WEBSOCKET_API.md`
Complete API documentation for WebSocket protocol

## Running the UI

### Start the Server

```bash
# From project root
python ui/websocket_server.py
```

The server will start on `http://localhost:8000`

### Access the UI

Open your browser and navigate to:
```
http://localhost:8000
```

### Using the UI

1. **Connect**: The UI automatically connects to the WebSocket server
2. **Enter Goal**: Type your research goal in the text area
3. **Start Research**: Click "Start Research" or press Ctrl+Enter
4. **Monitor Progress**: Watch real-time updates in the status section
5. **View Logs**: Monitor agent actions in the live log viewer
6. **Check Confidence**: See confidence scores update as agents complete tasks
7. **View Results**: Results appear automatically when research completes
8. **Export**: Export results as JSON or Markdown
9. **Browse History**: View past research sessions in the history section

## UI Sections

### 1. Header
- Application title and description
- Connection status indicator (green = connected, red = disconnected)

### 2. Research Goal Input
- Large text area for entering research goals
- Start button to initiate research
- Disabled during active research

### 3. Current Status
- **State**: Current agent loop state (IDLE, PLANNING, etc.)
- **Active Agent**: Which agent is currently executing
- **Current Action**: What action is being performed
- **Session ID**: Unique identifier for the current session

### 4. Confidence Scores
- Visual progress bars for each agent
- Color-coded based on confidence level:
  - Red/Orange: Low confidence (< 60%)
  - Orange/Green: Medium confidence (60-80%)
  - Green/Blue: High confidence (> 80%)
- Percentage display

### 5. Live Logs
- Real-time log streaming
- Filter dropdown (All, DEBUG, INFO, WARNING, ERROR)
- Clear logs button
- Color-coded log levels
- Timestamps for each entry
- Auto-scroll to latest

### 6. Research Results
- **Formatted View**: Human-readable display with sections:
  - Metadata (Session ID, Goal, Timestamp, Confidence)
  - Key Insights
  - Strategic Recommendations
  - Sources with links
  - Agents Involved
- **JSON View**: Raw JSON data with syntax highlighting
- Export buttons for JSON and Markdown

### 7. Session History
- List of past research sessions
- Click to view session details
- Status badges (completed, error, running)
- Timestamps and session IDs
- Refresh button to update list

## Keyboard Shortcuts

- **Ctrl+Enter**: Start research (when focused on goal input)

## Browser Compatibility

Tested and working on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Requires:
- WebSocket support
- ES6 JavaScript support
- CSS Grid and Flexbox support

## Responsive Design

The UI is fully responsive and works on:
- Desktop (1400px+)
- Laptop (1024px - 1399px)
- Tablet (768px - 1023px)
- Mobile (< 768px)

Mobile optimizations:
- Single column layout
- Stacked status cards
- Full-width buttons
- Touch-friendly controls

## Security Features

- **XSS Protection**: All user input is escaped before display
- **WebSocket Security**: Supports WSS (WebSocket Secure) for HTTPS
- **No Inline Scripts**: All JavaScript in external file
- **Content Security**: No eval() or dangerous functions

## Customization

### Changing Colors

Edit CSS custom properties in `styles.css`:

```css
:root {
    --primary-color: #2563eb;  /* Main brand color */
    --success-color: #10b981;  /* Success/high confidence */
    --warning-color: #f59e0b;  /* Warning/medium confidence */
    --error-color: #ef4444;    /* Error/low confidence */
}
```

### Adjusting Log Limit

Edit `app.js`:

```javascript
// Keep only last 500 logs
if (this.logs.length > 500) {
    this.logs = this.logs.slice(-500);
}
```

### Changing Reconnect Behavior

Edit `app.js`:

```javascript
this.maxReconnectAttempts = 5;  // Max reconnection attempts
this.reconnectDelay = 2000;     // Delay between attempts (ms)
```

## Troubleshooting

### Connection Issues

**Problem**: "Disconnected" status indicator

**Solutions**:
1. Ensure the server is running: `python ui/websocket_server.py`
2. Check the browser console for errors
3. Verify firewall settings allow WebSocket connections
4. Try refreshing the page

### No Logs Appearing

**Problem**: Logs section is empty

**Solutions**:
1. Check log level filter (set to "All Levels")
2. Verify WebSocket connection is active
3. Check browser console for JavaScript errors

### Results Not Displaying

**Problem**: Results section doesn't appear after research completes

**Solutions**:
1. Check browser console for errors
2. Verify the research completed successfully (check logs)
3. Try refreshing the page and viewing session history

### Export Not Working

**Problem**: Export buttons don't download files

**Solutions**:
1. Check browser's download settings
2. Ensure pop-ups are not blocked
3. Verify there are results to export

## Development

### File Structure

```
ui/
├── index.html          # Main HTML page
├── styles.css          # CSS styling
├── app.js              # JavaScript client
├── websocket_server.py # Backend server
├── WEBSOCKET_API.md    # API documentation
└── README.md           # This file
```

### Adding New Features

1. **New UI Section**: Add HTML in `index.html`, style in `styles.css`
2. **New Message Type**: Handle in `app.js` `handleMessage()` method
3. **New Export Format**: Add to `exportResults()` method in `app.js`

### Testing

The WebSocket server has comprehensive unit tests:

```bash
python -m pytest tests/unit/test_websocket_server.py -v
```

## Requirements Satisfied

This UI implementation satisfies all requirements from Requirement 10:

- ✅ 10.1: Input field for research goals
- ✅ 10.2: Real-time agent state display
- ✅ 10.3: Active agent display
- ✅ 10.4: Current action display
- ✅ 10.5: Live log viewer with filtering
- ✅ 10.6: Confidence score visualization
- ✅ 10.7: Decision history display
- ✅ 10.8: Results in JSON and formatted views
- ✅ 10.9: Session history browser
- ✅ 10.10: Export functionality (JSON, Markdown)
- ✅ 10.11: Real-time updates without refresh
- ✅ 10.12: Lightweight implementation (no heavy frameworks)

## Future Enhancements

Potential improvements for future versions:

- PDF export functionality
- Advanced log search and filtering
- Confidence score trend charts
- Agent execution timeline visualization
- Dark/light theme toggle
- Customizable dashboard layouts
- Real-time collaboration features
- Mobile app version
