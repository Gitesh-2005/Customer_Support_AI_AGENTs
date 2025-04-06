import sqlite3
import json
from typing import Dict, Any, List

DB_NAME = "tickets.db"

def create_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            issue_text TEXT NOT NULL,
            summary TEXT,
            severity TEXT,
            category TEXT,
            key_points TEXT,
            immediate_actions TEXT,
            escalation_required BOOLEAN,
            escalation_reason TEXT,
            team_assignment TEXT,
            follow_ups TEXT,
            required_info TEXT,
            resolution_steps TEXT,
            alternative_solutions TEXT,
            required_resources TEXT,
            status TEXT DEFAULT 'Pending',
            estimated_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add teams table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT,
            availability BOOLEAN DEFAULT true,
            performance_score FLOAT DEFAULT 0
        )
    ''')

    # Add agent performance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            tickets_resolved INTEGER DEFAULT 0,
            avg_resolution_time REAL DEFAULT 0,
            customer_satisfaction REAL DEFAULT 0,
            efficiency_score REAL DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            context TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            message TEXT NOT NULL,
            role TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_ticket(customer_name: str, issue_text: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tickets (customer_name, issue_text) 
        VALUES (?, ?)
    ''', (customer_name, issue_text))
    conn.commit()
    conn.close()

def get_all_tickets():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT 
                id, 
                customer_name, 
                issue_text, 
                summary, 
                resolution, 
                status, 
                estimated_time 
                FROM tickets''')
    tickets = c.fetchall()
    conn.close()
    return tickets

def update_ticket(ticket_id: int, summary: Dict[str, Any], actions: Dict[str, Any], resolution: Dict[str, Any]):
    """Update ticket with detailed AI analysis results"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Convert complex data structures to JSON strings
        summary_json = json.dumps(summary)
        actions_json = json.dumps(actions)
        resolution_json = json.dumps(resolution)
        
        cursor.execute('''
            UPDATE tickets 
            SET summary = ?,
                severity = ?,
                category = ?,
                key_points = ?,
                immediate_actions = ?,
                escalation_required = ?,
                escalation_reason = ?,
                team_assignment = ?,
                follow_ups = ?,
                required_info = ?,
                resolution_steps = ?,
                alternative_solutions = ?,
                required_resources = ?,
                estimated_time = ?,
                status = CASE 
                    WHEN ? = 'critical' THEN 'Urgent'
                    ELSE 'In Progress'
                END
            WHERE id = ?
        ''', (
            summary_json,
            summary.get('severity', 'medium'),
            summary.get('category', 'general'),
            json.dumps(summary.get('key_points', [])),
            json.dumps(actions.get('immediate_actions', [])),
            actions.get('escalation', {}).get('required', False),
            actions.get('escalation', {}).get('reason', ''),
            actions.get('escalation', {}).get('team', ''),
            json.dumps(actions.get('follow_ups', [])),
            json.dumps(actions.get('required_info', [])),
            json.dumps(resolution.get('steps', [])),
            json.dumps(resolution.get('alternatives', [])),
            json.dumps(resolution.get('resources', [])),
            resolution.get('total_estimated_time', ''),
            summary.get('severity', 'medium'),
            ticket_id
        ))
        conn.commit()
    except Exception as e:
        print(f"Error updating ticket: {str(e)}")
        raise
    finally:
        conn.close()

def get_ticket_by_id(ticket_id: int) -> Dict[str, Any]:
    """Get detailed ticket information by ID"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM tickets WHERE id = ?
        ''', (ticket_id,))
        ticket = cursor.fetchone()
        if ticket:
            column_names = [description[0] for description in cursor.description]
            ticket_dict = dict(zip(column_names, ticket))
            # Parse JSON strings back to lists
            for key in ['key_points', 'immediate_actions', 'follow_ups', 'required_info', 
                       'resolution_steps', 'alternative_solutions', 'required_resources']:
                if ticket_dict.get(key):
                    ticket_dict[key] = json.loads(ticket_dict[key])
            return ticket_dict
        return None
    finally:
        conn.close()

def mark_ticket_resolved(ticket_id: int):
    """Mark a ticket as resolved"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE tickets 
            SET status = 'Resolved'
            WHERE id = ?
        ''', (ticket_id,))
        conn.commit()
    finally:
        conn.close()


def get_team_performance():
    conn = sqlite3.connect(DB_NAME)
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                t.id,
                t.name,
                t.specialty,
                t.availability,
                t.performance_score,
                COUNT(tk.id) AS total_tickets,
                COALESCE(ROUND(AVG(
                    CASE WHEN tk.status = 'Resolved' THEN 1 ELSE 0 END
                ) * 100, 2), 0) AS resolution_rate
            FROM teams t
            LEFT JOIN tickets tk ON tk.team_assignment = t.name
            GROUP BY t.id
        ''')
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
        return []
    finally:
        conn.close()

def get_agent_metrics():
    """Retrieve agent performance metrics with validation"""
    conn = sqlite3.connect(DB_NAME)
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                agent_id,
                tickets_resolved,
                avg_resolution_time,
                customer_satisfaction,
                efficiency_score
            FROM agent_performance
        ''')
        
        metrics = []
        for row in cursor.fetchall():
            if len(row) != 5:
                raise ValueError("Invalid column count in agent_performance")
                
            metrics.append({
                "agent_id": row[0],
                "tickets_resolved": row[1],
                "avg_resolution_time": f"{row[2]:.1f} mins",
                "satisfaction": row[3],
                "efficiency": row[4]
            })
            
        return metrics
        
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
        raise
    except ValueError as e:
        print(f"Data validation error: {str(e)}")
        raise
    finally:
        conn.close()

def create_conversation(customer_name: str) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO conversations (customer_name) VALUES (?)',
        (customer_name,)
    )
    conversation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return conversation_id

def add_message_to_conversation(conversation_id: int, message: str, role: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO conversation_messages (conversation_id, message, role) VALUES (?, ?, ?)',
        (conversation_id, message, role)
    )
    conn.commit()
    conn.close()

def get_conversation_history(conversation_id: int, limit: int = 5):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT message, role FROM conversation_messages 
           WHERE conversation_id = ? 
           ORDER BY timestamp DESC LIMIT ?''',
        (conversation_id, limit)
    )
    messages = cursor.fetchall()
    conn.close()
    return messages

