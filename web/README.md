# Energy Manager Web Interface

A beautiful, modern web interface for the Energy Manager application that provides visualization and management of your energy tracking data.

## Features

- **Dashboard**: Overview with real-time stats, charts, and recent activity
- **Goals Management**: Create, edit, and archive energy goals with cost tracking
- **Daily Journal**: View and log energy events with detailed metadata
- **Trends Analysis**: Analyze patterns over time with comprehensive tables
- **Health Metrics**: Visualize objective health data from wearable devices

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database (First Time)

```bash
python emanager.py init
```

### 3. Start the Web Server

```bash
python web_server.py
```

### 4. Open in Browser

Navigate to: **http://localhost:5000**

## Usage

### Adding Goals

1. Click "Add Goal" button
2. Enter the goal name (e.g., "IELTS Speaking Practice")
3. Set priority level (P1 = High, P2 = Medium, P3 = Low)
4. Set energy cost (negative for consumption, positive for restoration)
5. Click "Add Goal" to save

### Logging Events

1. Click "Log Event" button
2. Fill in:
   - Activity description
   - Duration in minutes
   - Associated goal (optional)
   - Energy state (Consumption, Internal Friction, Growth, Abundance, Routine)
   - Physical/Mental/Emotional scores (1-10)
   - Notes (optional)
3. Click "Log Event" to save

### Importing Health Data

1. Navigate to the Health page
2. Click "Import Data"
3. Follow the prompts to upload CSV files from your Mi Band or other devices

## Architecture

- **Frontend**: Vanilla HTML/CSS/JavaScript with Chart.js for visualizations
- **Backend**: Flask REST API
- **Database**: SQLite (`emanager.db`)

## API Endpoints

- `GET /api/goals` - Get all active goals
- `POST /api/goals` - Create a new goal
- `DELETE /api/goals/<id>` - Archive a goal
- `GET /api/events` - Get events (with ?days parameter)
- `POST /api/events` - Create a new event
- `GET /api/health/today` - Get today's health metrics
- `GET /api/trends` - Get comprehensive daily trends
- `GET /api/stats/energy-states` - Get energy state distribution
- `GET /api/stats/balance` - Get daily energy balance

## Design Philosophy

The web interface follows modern design principles:

- **Dark Mode**: Reduces eye strain for extended use
- **Gradients**: Creates visual depth and premium feel
- **Smooth Animations**: Enhances user experience
- **Responsive Layout**: Works on desktop and mobile devices
- **Color Coding**: Intuitive visual feedback for energy states

## Development

### File Structure

```
EnergyManager/
├── web/
│   ├── index.html    # Main HTML structure
│   ├── styles.css    # Complete styling
│   └── app.js        # Frontend logic and API calls
├── web_server.py     # Flask backend API
├── database.py       # Database operations
├── emanager.py       # CLI interface
└── emanager.db       # SQLite database
```

### Customization

You can customize colors, fonts, and layouts by modifying `web/styles.css`:

- `:root` variables define the color palette
- Modify `--primary`, `--secondary` for main theme colors
- Adjust `--bg-*` variables for background colors
- Change font family in the `body` selector

## Troubleshooting

### Port Already in Use

If port 5000 is already in use, edit `web_server.py` and change:

```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

to a different port number.

### Data Not Showing

1. Ensure you've initialized the database: `python emanager.py init`
2. Check that you have some data logged via CLI or web interface
3. Check browser console for error messages (F12)

### CORS Errors

The application uses `flask-cors` to allow cross-origin requests. Ensure it's installed:

```bash
pip install flask-cors
```

## CLI Interface

The web interface complements the existing CLI. You can still use all CLI commands:

```bash
# Add a goal via CLI
python emanager.py goal add "New Goal" --priority 1 --cost -5

# View daily journal via CLI
python emanager.py journal --days 3

# Generate reports via CLI
python emanager.py report
```

## Future Enhancements

Potential improvements:

- Real-time updates with WebSockets
- Export data to CSV/JSON
- Advanced filtering and search
- Custom date range selection
- Goal categories and tags
- Predictive analytics and recommendations

## License

This project is part of the Personal Energy Manager system.
