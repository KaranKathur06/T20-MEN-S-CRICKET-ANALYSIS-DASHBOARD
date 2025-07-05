import os
import json
import pandas as pd
import streamlit as st

@st.cache_data
def read_json_files(json_folder):
    all_matches_data = []
    all_ball_data = []

    for file_name in os.listdir(json_folder):
        if file_name.endswith('.json'):
            file_path = os.path.join(json_folder, file_name)
            
            with open(file_path, 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                    
                    match_info = data.get('info', {})
                    innings_data = data.get('innings', [])
                    
                    match_data = {
                        'match_no ': file_name[:-5],
                        'date': match_info.get('dates', ['N/A'])[0],
                        'city': match_info.get('city', 'Unknown'),
                        'venue': match_info.get('venue', 'Unknown'),
                        'team1': match_info.get('teams', ['N/A', 'N/A'])[0],
                        'team2': match_info.get('teams', ['N/A', 'N/A'])[1],
                        'toss_winner': match_info.get('toss', {}).get('winner', 'Unknown'),
                        'toss_decision': match_info.get('toss', {}).get('decision', 'Unknown'),
                        'winner': match_info.get('outcome', {}).get('winner', 'No result'),
                        'win_by': match_info.get('outcome', {}).get('by', {}),
                        'player_of_match': match_info.get('player_of_match', ['N/A'])[0],
                        'overs': match_info.get('overs', 'N/A'),
                        'balls_per_over': match_info.get('balls_per_over', 6),
                        'latitude': match_info.get('latitude', None), 
                        'longitude': match_info.get('longitude', None),
                    }
                    all_matches_data.append(match_data)

                    for inning in innings_data:
                        team = inning.get('team', 'Unknown')
                        for over in inning.get('overs', []):
                            over_num = over.get('over', 0)
                            for delivery in over.get('deliveries', []):
                                ball_data = {
                                    'match_no ': match_data['match_no '],
                                    'innings': innings_data.index(inning) + 1,
                                    'batting_team': team,
                                    'bowling_team': match_data['team2'] if team == match_data['team1'] else match_data['team1'],
                                    'over': over_num,
                                    'ball': delivery.get('ball', 0),
                                    'batter': delivery.get('batter', 'Unknown'),
                                    'non_striker': delivery.get('non_striker', 'Unknown'),
                                    'bowler': delivery.get('bowler', 'Unknown'),
                                    'runs_batter': delivery.get('runs', {}).get('batter', 0),
                                    'runs_extras': delivery.get('runs', {}).get('extras', 0),
                                    'runs_total': delivery.get('runs', {}).get('total', 0),
                                    'extras_type': ', '.join(delivery.get('extras', {}).keys()),
                                    'is_wicket': 1 if 'wickets' in delivery else 0,
                                    'wicket_type': delivery.get('wickets', [{}])[0].get('kind', '') if 'wickets' in delivery else '',
                                    'player_out': delivery.get('wickets', [{}])[0].get('player_out', '') if 'wickets' in delivery else '',
                                    'boundary': delivery.get('boundary', 'None'),
                                }
                                all_ball_data.append(ball_data)

                except json.JSONDecodeError as e:
                    st.error(f"Error reading {file_name}: {e}")

    match_df = pd.DataFrame(all_matches_data) if all_matches_data else pd.DataFrame()
    ball_df = pd.DataFrame(all_ball_data) if all_ball_data else pd.DataFrame()

    # For summary_df
    summary_df = pd.DataFrame({
    'match_no ': match_df['match_no '],
    'team1': match_df['team1'],
    'team2': match_df['team2'],
    'winner': match_df['winner'],
    'win_by': match_df['win_by'].apply(lambda x: x.get('runs', 0) if isinstance(x, dict) else x if x else 0),
    'player_of_match': match_df['player_of_match'],
})

    #For city_df
    city_df = match_df.groupby('city')['match_no '].count().reset_index()
    city_df.columns = ['city', 'matches']

    return match_df, ball_df, summary_df, city_df
