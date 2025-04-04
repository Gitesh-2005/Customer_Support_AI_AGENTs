import sqlite3
import json
from typing import Dict, Any

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
            avg_resolution_time FLOAT DEFAULT 0,
            customer_satisfaction FLOAT DEFAULT 0,
            efficiency_score FLOAT DEFAULT 0,
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
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tickets')
    tickets = cursor.fetchall()
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
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT teams.id, teams.name, teams.specialty, teams.availability, teams.performance_score,
                   COUNT(tickets.id) as total_tickets,
                   ROUND(AVG(CASE WHEN tickets.status = 'Resolved' THEN 1 ELSE 0 END) * 100, 2) as resolution_rate
            FROM teams
            LEFT JOIN tickets ON tickets.team_assignment = teams.name
            GROUP BY teams.id
        ''')
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error fetching team performance: {str(e)}")
        raise
    finally:
        conn.close()

def get_agent_metrics():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM agent_performance')
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error fetching agent metrics: {str(e)}")
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