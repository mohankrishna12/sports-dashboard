from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import plotly.graph_objs as go
import plotly.utils
import json
from database import init_db
from models import Team, Player, Match, Innings, BattingScore, BowlingFigure, Partnership

app = Flask(__name__)
app.secret_key = 'cricket_dashboard_secret_key_2024'

# Initialize database
init_db()

@app.route('/')
def index():
    teams = Team.get_all()
    players = Player.get_all()
    matches = Match.get_all()
    return render_template('index.html', teams=teams, players=players, matches=matches)

@app.route('/add_team', methods=['GET', 'POST'])
def add_team():
    if request.method == 'POST':
        name = request.form['name']
        try:
            Team.create(name)
            flash(f'Team "{name}" added successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error adding team: {str(e)}', 'error')
    return render_template('add_team.html')

@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    teams = Team.get_all()
    if request.method == 'POST':
        name = request.form['name']
        team_id = request.form['team_id']
        role = request.form['role']
        try:
            Player.create(name, team_id, role)
            flash(f'Player "{name}" added successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error adding player: {str(e)}', 'error')
    return render_template('add_player.html', teams=teams)

@app.route('/add_score', methods=['GET', 'POST'])
def add_score():
    teams = Team.get_all()
    matches = Match.get_all()
    
    if request.method == 'POST':
        # Create match if new
        if request.form.get('new_match') == 'yes':
            team1_id = request.form['team1_id']
            team2_id = request.form['team2_id']
            match_date = request.form['match_date']
            venue = request.form['venue']
            match_id = Match.create(team1_id, team2_id, match_date, venue)
        else:
            match_id = request.form['match_id']
        
        # Create innings
        batting_team_id = request.form['batting_team_id']
        bowling_team_id = request.form['bowling_team_id']
        innings_number = request.form['innings_number']
        innings_id = Innings.create(match_id, batting_team_id, bowling_team_id, innings_number)
        
        # Add batting scores
        batting_count = int(request.form.get('batting_count', 0))
        for i in range(batting_count):
            player_id = request.form.get(f'player_id_{i}')
            if player_id:
                runs = int(request.form.get(f'runs_{i}', 0))
                balls = int(request.form.get(f'balls_{i}', 0))
                fours = int(request.form.get(f'fours_{i}', 0))
                sixes = int(request.form.get(f'sixes_{i}', 0))
                is_out = request.form.get(f'is_out_{i}') == 'yes'
                dismissal_type = request.form.get(f'dismissal_type_{i}') if is_out else None
                bowler_id = request.form.get(f'bowler_id_{i}') if is_out else None
                fielder_id = request.form.get(f'fielder_id_{i}') if is_out else None
                partnership = int(request.form.get(f'partnership_{i}', 0))
                
                BattingScore.create(innings_id, player_id, runs, balls, fours, sixes,
                                  is_out, dismissal_type, bowler_id, fielder_id, 
                                  partnership, i+1)
        
        # Add bowling figures
        bowling_count = int(request.form.get('bowling_count', 0))
        for i in range(bowling_count):
            bowler_id = request.form.get(f'bowler_pid_{i}')
            if bowler_id:
                overs = float(request.form.get(f'overs_{i}', 0))
                maidens = int(request.form.get(f'maidens_{i}', 0))
                runs_conceded = int(request.form.get(f'runs_conceded_{i}', 0))
                wickets = int(request.form.get(f'wickets_{i}', 0))
                
                BowlingFigure.create(innings_id, bowler_id, overs, maidens, runs_conceded, wickets)
        
        flash('Score added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_score.html', teams=teams, matches=matches)

@app.route('/api/players/<int:team_id>')
def get_team_players(team_id):
    players = Player.get_by_team(team_id)
    return jsonify([{'id': p['id'], 'name': p['name'], 'role': p['role']} for p in players])

@app.route('/team/<int:team_id>')
def team_dashboard(team_id):
    team = Team.get_by_id(team_id)
    players = Player.get_by_team(team_id)
    team_stats = Team.get_statistics(team_id)
    
    # Create visualizations
    player_names = [p['name'] for p in players]
    player_runs = [Player.get_batting_stats(p['id']).get('total_runs', 0) for p in players]
    player_wickets = [Player.get_bowling_stats(p['id']).get('total_wickets', 0) for p in players]
    
    # Runs bar chart
    runs_chart = go.Figure(data=[
        go.Bar(x=player_names, y=player_runs, marker_color='lightblue')
    ])
    runs_chart.update_layout(title='Total Runs by Player', xaxis_title='Player', yaxis_title='Runs')
    runs_chart_json = json.dumps(runs_chart, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Wickets bar chart
    wickets_chart = go.Figure(data=[
        go.Bar(x=player_names, y=player_wickets, marker_color='lightcoral')
    ])
    wickets_chart.update_layout(title='Total Wickets by Player', xaxis_title='Player', yaxis_title='Wickets')
    wickets_chart_json = json.dumps(wickets_chart, cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template('team_dashboard.html', 
                         team=team, 
                         players=players,
                         team_stats=team_stats,
                         runs_chart=runs_chart_json,
                         wickets_chart=wickets_chart_json)

@app.route('/player/<int:player_id>')
def player_dashboard(player_id):
    player = Player.get_by_id(player_id)
    batting_stats = Player.get_batting_stats(player_id)
    bowling_stats = Player.get_bowling_stats(player_id)
    
    # Batting pie chart (Runs distribution)
    if batting_stats.get('total_runs', 0) > 0:
        batting_pie = go.Figure(data=[go.Pie(
            labels=['Boundaries (4s & 6s)', 'Singles & Doubles'],
            values=[
                (batting_stats.get('total_fours', 0) * 4) + (batting_stats.get('total_sixes', 0) * 6),
                batting_stats.get('total_runs', 0) - ((batting_stats.get('total_fours', 0) * 4) + (batting_stats.get('total_sixes', 0) * 6))
            ],
            marker_colors=['#ff9999', '#66b3ff']
        )])
        batting_pie.update_layout(title='Runs Distribution')
        batting_pie_json = json.dumps(batting_pie, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        batting_pie_json = None
    
    # Strike rate gauge
    if batting_stats.get('strike_rate'):
        sr_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=batting_stats.get('strike_rate', 0),
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Strike Rate"},
            gauge={'axis': {'range': [None, 200]},
                   'bar': {'color': "darkblue"},
                   'steps': [
                       {'range': [0, 80], 'color': "lightgray"},
                       {'range': [80, 120], 'color': "gray"},
                       {'range': [120, 200], 'color': "lightgreen"}],
                   'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 150}}))
        sr_gauge_json = json.dumps(sr_gauge, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        sr_gauge_json = None
    
    return render_template('player_dashboard.html',
                         player=player,
                         batting_stats=batting_stats,
                         bowling_stats=bowling_stats,
                         batting_pie=batting_pie_json,
                         sr_gauge=sr_gauge_json)

if __name__ == '__main__':
    app.run(debug=True)
