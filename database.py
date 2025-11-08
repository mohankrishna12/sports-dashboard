import sqlite3
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('cricket.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Teams table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Players table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            team_id INTEGER NOT NULL,
            role TEXT CHECK(role IN ('Batsman', 'Bowler', 'All-rounder', 'Wicket-keeper')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams (id),
            UNIQUE(name, team_id)
        )
    ''')
    
    # Matches table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team1_id INTEGER NOT NULL,
            team2_id INTEGER NOT NULL,
            match_date DATE NOT NULL,
            venue TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team1_id) REFERENCES teams (id),
            FOREIGN KEY (team2_id) REFERENCES teams (id)
        )
    ''')
    
    # Innings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS innings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER NOT NULL,
            batting_team_id INTEGER NOT NULL,
            bowling_team_id INTEGER NOT NULL,
            innings_number INTEGER NOT NULL,
            total_runs INTEGER DEFAULT 0,
            total_wickets INTEGER DEFAULT 0,
            total_balls INTEGER DEFAULT 0,
            FOREIGN KEY (match_id) REFERENCES matches (id),
            FOREIGN KEY (batting_team_id) REFERENCES teams (id),
            FOREIGN KEY (bowling_team_id) REFERENCES teams (id)
        )
    ''')
    
    # Batting scores table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS batting_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            innings_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            runs_scored INTEGER DEFAULT 0,
            balls_faced INTEGER DEFAULT 0,
            fours INTEGER DEFAULT 0,
            sixes INTEGER DEFAULT 0,
            is_out BOOLEAN DEFAULT 0,
            dismissal_type TEXT,
            bowler_id INTEGER,
            fielder_id INTEGER,
            partnership_runs INTEGER DEFAULT 0,
            batting_position INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (innings_id) REFERENCES innings (id),
            FOREIGN KEY (player_id) REFERENCES players (id),
            FOREIGN KEY (bowler_id) REFERENCES players (id),
            FOREIGN KEY (fielder_id) REFERENCES players (id)
        )
    ''')
    
    # Bowling figures table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bowling_figures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            innings_id INTEGER NOT NULL,
            bowler_id INTEGER NOT NULL,
            overs REAL DEFAULT 0,
            maidens INTEGER DEFAULT 0,
            runs_conceded INTEGER DEFAULT 0,
            wickets INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (innings_id) REFERENCES innings (id),
            FOREIGN KEY (bowler_id) REFERENCES players (id)
        )
    ''')
    
    # Partnerships table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partnerships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            innings_id INTEGER NOT NULL,
            batsman1_id INTEGER NOT NULL,
            batsman2_id INTEGER NOT NULL,
            runs INTEGER DEFAULT 0,
            balls INTEGER DEFAULT 0,
           
            wicket_number INTEGER,
            FOREIGN KEY (innings_id) REFERENCES innings (id),
            FOREIGN KEY (batsman1_id) REFERENCES players (id),
            FOREIGN KEY (batsman2_id) REFERENCES players (id)
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
