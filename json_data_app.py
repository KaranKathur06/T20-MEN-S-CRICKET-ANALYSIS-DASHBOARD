import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from Mypackage import json_dataset,helper
from PIL import Image
import base64

def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/{"jpg"};base64,{encoded_string.decode()});
        background-size: 100%;
        background-position: right center;
        background-repeat: no-repeat;
    }}  
    </style>
    """,
    unsafe_allow_html=True
    )

add_bg_from_local('static/bgg.jpg')

img = Image.open('static/sideimage.jpg')

#Loading json datas into Dataframes
json_folder = "C:\\STUDY\\PROGRAMS\\PYTHON\\T20 MEN'S CRICKET ANALYSIS DASHBOARD\\Datasets\\JSON DATA"
match_df, ball_df, summary_df, city_df = json_dataset.read_json_files(json_folder)

st.title("ICC Men's T20I Matches")

total_matches = len(match_df)
total_deliveries = len(ball_df)
total_fours = len(ball_df[ball_df['runs_batter'] == 4])
total_sixes = len(ball_df[ball_df['runs_batter'] >= 6])
total_wickets = len(ball_df[ball_df['is_wicket'] == 1])

st.write(f"Total Matches: {total_matches}")
st.write(f"Total Deliveries: {total_deliveries}")
st.write(f"Total Fours: {total_fours}")
st.write(f"Total Sixes: {total_sixes}")
st.write(f"Total Wickets: {total_wickets}")

st.sidebar.image(img)
st.sidebar.title("T20 Cricket Analysis From (2005-2024)")

user_menu = st.sidebar.radio(
    'Select Option',
    ('Overview', 'Player Stats', 'Players Comparison', 'Overall Analysis', 'Teamwise Analysis', 'Yearwise Analysis')
)

if user_menu == 'Overview':
    st.title("Top Statistics")

    total_matches = ball_df['Match No'].nunique()
    total_teams = ball_df['Batting Team'].nunique()
    total_balls_bowled = len(ball_df)
    players = ball_df['Batter'].append(ball_df['Non-Striker']).append(ball_df['Bowler'])
    total_players = players.nunique()

    total_fours = len(ball_df[ball_df['Boundary'] == 4])
    total_sixes = len(ball_df[ball_df['Boundary'] == 6])
    total_runs = ball_df['Total Runs'].sum()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.header("Matches")
        st.title(total_matches)
    with col2:
        st.header("Teams")
        st.title(total_teams)
    with col3:
        st.header("Players")
        st.title(total_players)
    with col4:
        st.header("Balls")
        st.title(total_balls_bowled)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.header("Fours")
        st.title(total_fours)
    with col2:
        st.header("Sixes")
        st.title(total_sixes)
    with col3:
        st.header("Runs")
        st.title(total_runs)

    data = match_df[['latitude', 'longitude']]
    data.dropna(inplace=True)
    st.title("Match Venues")
    st.map(data)

