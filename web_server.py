# Flask API for Energy Manager Web Interface
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import database
import analysis
from datetime import datetime, timedelta
import os

app = Flask(__name__, static_folder='web')
CORS(app)

# Serve the web interface
@app.route('/')
def index():
    return send_from_directory('web', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('web', path)

# API Routes

@app.route('/api/goals', methods=['GET'])
def get_goals():
    """Get all active goals with statistics"""
    conn = database.create_connection()
    c = conn.cursor()
    
    # Get goals with event counts and total time
    c.execute("""
        SELECT 
            g.goal_id,
            g.goal_name,
            g.priority_level,
            g.energy_cost,
            g.is_active,
            COUNT(e.event_id) as event_count,
            COALESCE(SUM(e.duration_minutes), 0) / 60.0 as total_hours
        FROM goals g
        LEFT JOIN events e ON g.goal_id = e.goal_id
        WHERE g.is_active = 1
        GROUP BY g.goal_id
        ORDER BY g.priority_level, g.goal_name
    """)
    
    goals = []
    for row in c.fetchall():
        goals.append({
            'goal_id': row[0],
            'goal_name': row[1],
            'priority_level': row[2],
            'energy_cost': row[3],
            'is_active': row[4],
            'event_count': row[5],
            'total_hours': round(row[6], 1)
        })
    
    conn.close()
    return jsonify(goals)

@app.route('/api/goals', methods=['POST'])
def create_goal():
    """Create a new goal"""
    data = request.json
    conn = database.create_connection()
    
    try:
        database.add_goal(
            conn,
            data['goal_name'],
            data.get('priority_level', 2),
            data.get('energy_cost', 0)
        )
        conn.close()
        return jsonify({'success': True, 'message': 'Goal created successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/goals/<int:goal_id>', methods=['DELETE'])
def archive_goal(goal_id):
    """Archive a goal"""
    conn = database.create_connection()
    
    try:
        database.archive_goal_by_id(conn, goal_id)
        conn.close()
        return jsonify({'success': True, 'message': 'Goal archived successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/goals/<int:goal_id>', methods=['PUT'])
def update_goal(goal_id):
    """Update a goal"""
    data = request.json
    conn = database.create_connection()
    
    try:
        database.update_goal(
            conn,
            goal_id,
            data.get('goal_name'),
            data.get('energy_cost'),
            data.get('priority_level')
        )
        conn.close()
        return jsonify({'success': True, 'message': 'Goal updated successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/events', methods=['GET'])
def get_events():
    """Get events for specified number of days"""
    days = request.args.get('days', 7, type=int)
    conn = database.create_connection()
    c = conn.cursor()
    
    start_date = (datetime.now() - timedelta(days=days - 1)).date()
    
    c.execute("""
        SELECT 
            e.event_id,
            e.timestamp_start,
            e.activity,
            e.duration_minutes,
            e.key_state,
            e.physical_score,
            e.mental_score,
            e.emotional_score,
            e.notes,
            g.goal_name,
            g.priority_level,
            g.energy_cost
        FROM events e
        LEFT JOIN goals g ON e.goal_id = g.goal_id
        WHERE DATE(e.timestamp_start) >= ?
        ORDER BY e.timestamp_start DESC
    """, (start_date,))
    
    events = []
    for row in c.fetchall():
        events.append({
            'event_id': row[0],
            'timestamp_start': row[1],
            'activity': row[2],
            'duration_minutes': row[3],
            'key_state': row[4],
            'physical_score': row[5],
            'mental_score': row[6],
            'emotional_score': row[7],
            'notes': row[8],
            'goal_name': row[9],
            'priority_level': row[10],
            'energy_cost': row[11]
        })
    
    conn.close()
    return jsonify(events)

@app.route('/api/events/today', methods=['GET'])
def get_today_events():
    """Get events for a specific date (defaults to today or offset)"""
    conn = database.create_connection()
    c = conn.cursor()
    
    # Check for specific date first (YYYY-MM-DD)
    date_str = request.args.get('date')
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    else:
        # Fallback to offset_days (default 0 for today)
        offset_days = request.args.get('offset_days', 0, type=int)
        target_date = (datetime.now() - timedelta(days=offset_days)).date()
    
    c.execute("""
        SELECT 
            e.event_id,
            e.timestamp_start,
            e.activity,
            e.duration_minutes,
            e.key_state,
            g.goal_name,
            g.energy_cost,
            e.physical_score,
            e.mental_score,
            e.emotional_score,
            e.notes
        FROM events e
        LEFT JOIN goals g ON e.goal_id = g.goal_id
        WHERE DATE(e.timestamp_start) = ?
        ORDER BY e.timestamp_start DESC
    """, (target_date,))
    
    events = []
    for row in c.fetchall():
        events.append({
            'event_id': row[0],
            'timestamp_start': row[1],
            'activity': row[2],
            'duration_minutes': row[3],
            'key_state': row[4],
            'goal_name': row[5],
            'energy_cost': row[6],
            'physical_score': row[7],
            'mental_score': row[8],
            'emotional_score': row[9],
            'notes': row[10]
        })
    
    conn.close()
    return jsonify(events)

@app.route('/api/events', methods=['POST'])
def create_event():
    """Create a new event"""
    data = request.json
    conn = database.create_connection()
    
    try:
        event = {
            'timestamp_start': data.get('timestamp_start', datetime.now().isoformat()),
            'duration_minutes': data['duration_minutes'],
            'activity': data['activity'],
            'goal_id': data.get('goal_id'),
            'physical_score': data.get('physical_score', 5),
            'mental_score': data.get('mental_score', 5),
            'emotional_score': data.get('emotional_score', 5),
            'key_state': data['key_state'],
            'notes': data.get('notes', '')
        }
        database.insert_event(conn, event)
        conn.close()
        return jsonify({'success': True, 'message': 'Event created successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/events/<int:event_id>/time', methods=['PUT'])
def update_event_time(event_id):
    """Update event timestamp and duration"""
    data = request.json
    conn = database.create_connection()
    c = conn.cursor()
    
    try:
        new_timestamp = data.get('timestamp_start')
        new_duration = data.get('duration_minutes')
        
        if new_timestamp and new_duration:
            c.execute("""
                UPDATE events 
                SET timestamp_start = ?, duration_minutes = ?
                WHERE event_id = ?
            """, (new_timestamp, new_duration, event_id))
        elif new_timestamp:
            c.execute("""
                UPDATE events 
                SET timestamp_start = ? 
                WHERE event_id = ?
            """, (new_timestamp, event_id))
        elif new_duration:
            c.execute("""
                UPDATE events 
                SET duration_minutes = ? 
                WHERE event_id = ?
            """, (new_duration, event_id))
            
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Event updated successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health/today', methods=['GET'])
def get_today_health():
    """Get health metrics for a specific date (defaults to today or offset)"""
    conn = database.create_connection()
    c = conn.cursor()
    
    # Check for specific date first (YYYY-MM-DD)
    date_str = request.args.get('date')
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    else:
        # Fallback to offset_days (default 0 for today)
        offset_days = request.args.get('offset_days', 0, type=int)
        target_date = (datetime.now() - timedelta(days=offset_days)).date()
    
    # Get all metrics for target date
    c.execute("""
        SELECT metric_type, value_numeric
        FROM health_metrics
        WHERE DATE(timestamp) = ? AND value_numeric > 0
    """, (target_date,))
    
    metrics = {}
    for row in c.fetchall():
        metrics[row[0]] = row[1]
    
    conn.close()
    
    # Return structured health data
    return jsonify({
        'sleep_score': metrics.get('sleep_score'),
        'sleep_total_min': metrics.get('sleep_total_min'),
        'rhr_avg': metrics.get('rhr_avg'),
        'hr_min': metrics.get('hr_min'),
        'hr_max': metrics.get('hr_max'),
        'stress_avg': metrics.get('stress_avg'),
        'steps_total': metrics.get('steps_total')
    })

@app.route('/api/health/trends', methods=['GET'])
def get_health_trends():
    """Get health metric trends"""
    days = request.args.get('days', 14, type=int)
    metric = request.args.get('metric', 'sleep_score')
    
    conn = database.create_connection()
    c = conn.cursor()
    
    start_date = (datetime.now() - timedelta(days=days - 1)).date()
    
    c.execute("""
        SELECT DATE(timestamp) as date, value_numeric
        FROM health_metrics
        WHERE metric_type = ? AND DATE(timestamp) >= ?
        ORDER BY date
    """, (metric, start_date))
    
    trends = []
    for row in c.fetchall():
        trends.append({
            'date': row[0],
            'value': row[1]
        })
    
    conn.close()
    return jsonify(trends)

@app.route('/api/trends', methods=['GET'])
def get_trends():
    """Get comprehensive daily trends"""
    days = request.args.get('days', 14, type=int)
    conn = database.create_connection()
    c = conn.cursor()
    
    start_date = (datetime.now() - timedelta(days=days - 1)).date()
    
    # Get all dates in range
    c.execute("""
        SELECT DISTINCT DATE(timestamp_start) as date
        FROM events
        WHERE DATE(timestamp_start) >= ?
        UNION
        SELECT DISTINCT DATE(timestamp) as date
        FROM health_metrics
        WHERE DATE(timestamp) >= ?
        ORDER BY date DESC
    """, (start_date, start_date))
    
    dates = [row[0] for row in c.fetchall()]
    
    trends = []
    for date in dates:
        # Get health metrics for this date
        c.execute("""
            SELECT metric_type, value_numeric
            FROM health_metrics
            WHERE DATE(timestamp) = ?
        """, (date,))
        
        metrics = {}
        for row in c.fetchall():
            metrics[row[0]] = row[1]
        
        # Get events for this date
        c.execute("""
            SELECT 
                COUNT(*) as event_count,
                COALESCE(SUM(e.duration_minutes), 0) / 60.0 as total_hours,
                COALESCE(SUM(g.energy_cost), 0) as energy_net
            FROM events e
            LEFT JOIN goals g ON e.goal_id = g.goal_id
            WHERE DATE(e.timestamp_start) = ?
        """, (date,))
        
        event_data = c.fetchone()
        
        trends.append({
            'date': date,
            'sleep_score': metrics.get('sleep_score'),
            'rhr_avg': metrics.get('rhr_avg'),
            'stress_avg': metrics.get('stress_avg'),
            'steps_total': metrics.get('steps_total'),
            'event_count': event_data[0] if event_data else 0,
            'total_hours': round(event_data[1], 1) if event_data else 0,
            'energy_net': event_data[2] if event_data else 0
        })
    
    conn.close()
    return jsonify(trends)

@app.route('/api/stats/energy-states', methods=['GET'])
def get_energy_states():
    """Get energy state distribution"""
    days = request.args.get('days', 7, type=int)
    conn = database.create_connection()
    c = conn.cursor()
    
    start_date = (datetime.now() - timedelta(days=days - 1)).date()
    
    c.execute("""
        SELECT key_state, COUNT(*) as count
        FROM events
        WHERE DATE(timestamp_start) >= ?
        GROUP BY key_state
    """, (start_date,))
    
    states = {}
    for row in c.fetchall():
        states[row[0]] = row[1]
    
    conn.close()
    return jsonify(states)

@app.route('/api/stats/balance', methods=['GET'])
def get_energy_balance():
    """Get daily energy balance"""
    days = request.args.get('days', 7, type=int)
    conn = database.create_connection()
    c = conn.cursor()
    
    start_date = (datetime.now() - timedelta(days=days - 1)).date()
    
    c.execute("""
        SELECT 
            DATE(e.timestamp_start) as date,
            COALESCE(SUM(g.energy_cost), 0) as balance
        FROM events e
        LEFT JOIN goals g ON e.goal_id = g.goal_id
        WHERE DATE(e.timestamp_start) >= ?
        GROUP BY DATE(e.timestamp_start)
        ORDER BY date
    """, (start_date,))
    
    balance = []
    for row in c.fetchall():
        balance.append({
            'date': row[0],
            'balance': row[1]
        })
    
    conn.close()
    return jsonify(balance)

@app.route('/api/import', methods=['POST'])
def import_csv_data():
    """Import health data from CSV file"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'error': 'File must be CSV format'}), 400
    
    try:
        # Save file temporarily
        import tempfile
        import os
        from importer import parse_aggregated_data, parse_sport_records
        
        # Create temp file and save uploaded file
        tmp = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv')
        tmp_path = tmp.name
        file.save(tmp_path)
        tmp.close()  # Close to ensure file is written to disk
        
        try:
            # Parse based on filename
            metrics_data = []
            filename = file.filename.lower()
            
            if 'aggregated' in filename or 'fitness_data' in filename:
                metrics_data = parse_aggregated_data(tmp_path)
            elif 'sport' in filename or 'record' in filename:
                metrics_data = parse_sport_records(tmp_path)
            else:
                return jsonify({
                    'success': False,
                    'error': 'Unsupported file. Please upload aggregated_fitness_data or sport_record CSV files.'
                }), 400
            
            if not metrics_data:
                return jsonify({
                    'success': False,
                    'error': 'No valid data found in file'
                }), 400
            
            # Import to database
            conn = database.create_connection()
            database.insert_health_metrics_batch(conn, metrics_data)
            conn.close()
            
            return jsonify({
                'success': True,
                'records_imported': len(metrics_data),
                'message': f'Successfully imported {len(metrics_data)} health records'
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Import failed: {str(e)}'
        }), 500

@app.route('/api/report', methods=['GET'])
def get_weekly_report():
    """Get weekly report data"""
    try:
        conn = database.create_connection()
        days = request.args.get('days', 7, type=int)
        report_data = analysis.get_weekly_report_data(conn, days)
        conn.close()
        return jsonify(report_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/plan', methods=['GET'])
def get_daily_plan():
    """Get daily plan data"""
    try:
        conn = database.create_connection()
        plan_data = analysis.get_daily_plan_data(conn)
        conn.close()
        return jsonify(plan_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure database is initialized
    conn = database.create_connection()
    database.create_tables(conn)
    database.migrate_db(conn)
    conn.close()
    
    # Run the server
    print("\n=================================================")
    print("Energy Manager Web Interface Starting...")
    print("=================================================")
    print("\nAccess the web interface at: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
