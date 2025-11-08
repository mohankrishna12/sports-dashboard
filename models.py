from database import get_db_connection

class Team:
    @staticmethod
    def create(name):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO teams (name) VALUES (?)', (name,))
        conn.commit()
        team_id = cursor.lastrowid
        conn.close()
        return team_id
    
    @staticmethod
    def get_all():
        conn = get_db_connection()
        teams = conn.execute('SELECT * FROM teams ORDER BY name').fetchall()
        conn.close()
        return teams
    
    @staticmethod
    def get_by_id(team_id):
        conn = get_db_connection()
        team = conn.execute('SELECT * FROM teams WHERE id = ?', (team_id,)).fetchone()
        conn.close()
        return team
    
    @staticmethod
    def get_statistics(team_id):
        conn = get_db_connection()
        
        # Total matches, runs, wickets
        stats = conn.execute('''
            SELECT 
                COUNT(DISTINCT i.match_id) as matches_played,
                SUM(i.total_runs) as total_runs,
                SUM(i.total_wickets) as total_wickets,
                ROUND(AVG(i.total_runs), 2) as avg_runs_per_innings
            FROM innings i
            WHERE i.batting_team_id = ?
        ''', (team_id,)).fetchone()
        
        conn.close()
        return dict(stats)

class Player:
    @staticmethod
    def create(name, team_id, role):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO players (name, team_id, role) VALUES (?, ?, ?)',
                      (name, team_id, role))
        conn.commit()
        player_id = cursor.lastrowid
        conn.close()
        return player_id
    
    @staticmethod
    def get_all():
        conn = get_db_connection()
        players = conn.execute('''
            SELECT p.*, t.name as team_name 
            FROM players p
            JOIN teams t ON p.team_id = t.id
            ORDER BY t.name, p.name
        ''').fetchall()
        conn.close()
        return players
    
    @staticmethod
    def get_by_team(team_id):
        conn = get_db_connection()
        players = conn.execute('''
            SELECT * FROM players WHERE team_id = ? ORDER BY name
        ''', (team_id,)).fetchall()
        conn.close()
        return players
    
    @staticmethod
    def get_by_id(player_id):
        conn = get_db_connection()
        player = conn.execute('''
            SELECT p.*, t.name as team_name 
            FROM players p
            JOIN teams t ON p.team_id = t.id
            WHERE p.id = ?
        ''', (player_id,)).fetchone()
        conn.close()
        return player
    
    @staticmethod
    def get_batting_stats(player_id):
        conn = get_db_connection()
        stats = conn.execute('''
            SELECT 
                COUNT(*) as innings,
                SUM(runs_scored) as total_runs,
                SUM(balls_faced) as total_balls,
                MAX(runs_scored) as highest_score,
                ROUND(AVG(runs_scored), 2) as average,
                ROUND(CAST(SUM(runs_scored) AS FLOAT) * 100 / NULLIF(SUM(balls_faced), 0), 2) as strike_rate,
                SUM(fours) as total_fours,
                SUM(sixes) as total_sixes,
                SUM(CASE WHEN is_out = 0 THEN 1 ELSE 0 END) as not_outs
            FROM batting_scores
            WHERE player_id = ?
        ''', (player_id,)).fetchone()
        conn.close()
        return dict(stats) if stats else {}
    
    @staticmethod
    def get_bowling_stats(player_id):
        conn = get_db_connection()
        stats = conn.execute('''
            SELECT 
                COUNT(*) as innings,
                SUM(overs) as total_overs,
                SUM(runs_conceded) as runs_conceded,
                SUM(wickets) as total_wickets,
                ROUND(CAST(SUM(runs_conceded) AS FLOAT) / NULLIF(SUM(wickets), 0), 2) as average,
                ROUND(CAST(SUM(runs_conceded) AS FLOAT) * 6 / NULLIF(SUM(overs), 0), 2) as economy,
                MAX(wickets) as best_bowling
            FROM bowling_figures
            WHERE bowler_id = ?
        ''', (player_id,)).fetchone()
        conn.close()
        return dict(stats) if stats else {}

class Match:
    @staticmethod
    def create(team1_id, team2_id, match_date, venue):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO matches (team1_id, team2_id, match_date, venue)
            VALUES (?, ?, ?, ?)
        ''', (team1_id, team2_id, match_date, venue))
        conn.commit()
        match_id = cursor.lastrowid
        conn.close()
        return match_id
    
    @staticmethod
    def get_all():
        conn = get_db_connection()
        matches = conn.execute('''
            SELECT m.*, 
                   t1.name as team1_name, 
                   t2.name as team2_name
            FROM matches m
            JOIN teams t1 ON m.team1_id = t1.id
            JOIN teams t2 ON m.team2_id = t2.id
            ORDER BY m.match_date DESC
        ''').fetchall()
        conn.close()
        return matches

class Innings:
    @staticmethod
    def create(match_id, batting_team_id, bowling_team_id, innings_number):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO innings (match_id, batting_team_id, bowling_team_id, innings_number)
            VALUES (?, ?, ?, ?)
        ''', (match_id, batting_team_id, bowling_team_id, innings_number))
        conn.commit()
        innings_id = cursor.lastrowid
        conn.close()
        return innings_id
    
    @staticmethod
    def get_by_id(innings_id):
        conn = get_db_connection()
        innings = conn.execute('SELECT * FROM innings WHERE id = ?', (innings_id,)).fetchone()
        conn.close()
        return innings

class BattingScore:
    @staticmethod
    def create(innings_id, player_id, runs_scored, balls_faced, fours, sixes,
               is_out, dismissal_type=None, bowler_id=None, fielder_id=None, 
               partnership_runs=0, batting_position=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO batting_scores 
            (innings_id, player_id, runs_scored, balls_faced, fours, sixes, 
             is_out, dismissal_type, bowler_id, fielder_id, partnership_runs, batting_position)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (innings_id, player_id, runs_scored, balls_faced, fours, sixes,
              is_out, dismissal_type, bowler_id, fielder_id, partnership_runs, batting_position))
        conn.commit()
        
        # Update innings totals
        cursor.execute('''
            UPDATE innings 
            SET total_runs = (SELECT SUM(runs_scored) FROM batting_scores WHERE innings_id = ?),
                total_wickets = (SELECT SUM(is_out) FROM batting_scores WHERE innings_id = ?),
                total_balls = (SELECT SUM(balls_faced) FROM batting_scores WHERE innings_id = ?)
            WHERE id = ?
        ''', (innings_id, innings_id, innings_id, innings_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_innings(innings_id):
        conn = get_db_connection()
        scores = conn.execute('''
            SELECT bs.*, 
                   p.name as player_name,
                   b.name as bowler_name,
                   f.name as fielder_name
            FROM batting_scores bs
            JOIN players p ON bs.player_id = p.id
            LEFT JOIN players b ON bs.bowler_id = b.id
            LEFT JOIN players f ON bs.fielder_id = f.id
            WHERE bs.innings_id = ?
            ORDER BY bs.batting_position
        ''', (innings_id,)).fetchall()
        conn.close()
        return scores

class BowlingFigure:
    @staticmethod
    def create(innings_id, bowler_id, overs, maidens, runs_conceded, wickets):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bowling_figures 
            (innings_id, bowler_id, overs, maidens, runs_conceded, wickets)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (innings_id, bowler_id, overs, maidens, runs_conceded, wickets))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_innings(innings_id):
        conn = get_db_connection()
        figures = conn.execute('''
            SELECT bf.*, p.name as bowler_name
            FROM bowling_figures bf
            JOIN players p ON bf.bowler_id = p.id
            WHERE bf.innings_id = ?
        ''', (innings_id,)).fetchall()
        conn.close()
        return figures

class Partnership:
    @staticmethod
    def create(innings_id, batsman1_id, batsman2_id, runs, balls, wicket_number):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO partnerships 
            (innings_id, batsman1_id, batsman2_id, runs, balls, wicket_number)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (innings_id, batsman1_id, batsman2_id, runs, balls, wicket_number))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_innings(innings_id):
        conn = get_db_connection()
        partnerships = conn.execute('''
            SELECT p.*, 
                   p1.name as batsman1_name,
                   p2.name as batsman2_name
            FROM partnerships p
            JOIN players p1 ON p.batsman1_id = p1.id
            JOIN players p2 ON p.batsman2_id = p2.id
            WHERE p.innings_id = ?
            ORDER BY p.wicket_number
        ''', (innings_id,)).fetchall()
        conn.close()
        return partnerships
