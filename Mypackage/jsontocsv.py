import json
import numpy as np
import pandas as pd
pd.set_option('future.no_silent_downcasting', True)
from tqdm import tqdm
from geopy.geocoders import Nominatim
import os

# Step 1: File Path Setup and Data Extraction
def fetch_filepaths(directory):
    filepaths = []
    for file in os.listdir(directory):
        filepaths.append(os.path.join(directory, file))
    return filepaths

# Step 2: Extract data from the JSON file, filtering out female matches
def extract_json_data(filepaths):
    dataframes = []
    counter = 1
    for file in tqdm(filepaths):
        try:
            with open(file, 'r') as f:
                content = f.read().strip()
                if content:  # Checks if file is not empty
                    json_data = json.loads(content)  # Parse JSON file
                    if json_data['info'].get('gender') == 'male':  # Filter for male matches
                        match_data = pd.DataFrame([{
                            'Match_id': counter,
                            'City': json_data['info'].get('city'),
                            'Venue': json_data['info'].get('venue'),
                            'Date': json_data['info'].get('dates', [None])[0] if json_data['info'].get('dates') else None,
                            'Match_Type': json_data['info'].get('match_type'),
                            'Gender': json_data['info'].get('gender'),
                            'Winner': json_data['info'].get('outcome', {}).get('winner'),
                            'Win_By_Wickets': json_data['info'].get('outcome', {}).get('by', {}).get('wickets', 0),  # Default to 0 if missing
                            'Player_of_Match': json_data['info'].get('player_of_match', [None])[0],
                            'Teams': ', '.join(json_data['info'].get('teams', [])),
                            'Toss_Winner': json_data['info'].get('toss', {}).get('winner'),
                            'Toss_Decision': json_data['info'].get('toss', {}).get('decision'),
                            'Overs': json_data['info'].get('overs')
                        }])
                        dataframes.append(match_data)
                        counter += 1
                else:
                    print(f"Skipping empty file: {file}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Skipping file {file} due to error: {e}")
    return pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()  # Return empty DataFrame if no valid data

# Step 3: Data Preprocessing
def preprocess_data(df):
    df['Date'] = pd.to_datetime(df['Date'])
    df = df[df['Gender'] == 'male']  # Filter for male T20 matches
    df = df[df['Overs'] == 20]
    
    # Using .loc[] to avoid SettingWithCopyWarning
    df.loc[:, 'Win_By_Wickets'] = df['Win_By_Wickets'].fillna(0).astype('int64') 
    
    # Infer object types
    df = df.infer_objects(copy=False)
    
    return df

# Step 4: Extract Ball-by-Ball Data
def extract_ball_by_ball_data(json_data, match_no):
    match_no_list, inning, batting_team, over_no, ball_no = [], [], [], [], []
    batter_name, bowler_name, batter_runs, extra_runs, total, boundaries_count = [], [], [], [], [], []

    def extract_deliveries(innings_data, inning_label):
        for inning_data in innings_data:
            team_nm = inning_data.get('team')
            print(f"Processing Inning: {inning_label}, Team: {team_nm}")
            for over in inning_data.get('overs', []):
                over_nm = over.get('over')
                b = 1  # Reset ball number at the beginning of each over
                boundary_count_for_over = 0  # Initialize boundary count for the current over
                for ball in over.get('deliveries', []):
                    # Extract data for each delivery
                    match_no_list.append(match_no)
                    inning.append(inning_label)
                    batting_team.append(team_nm)
                    over_no.append(over_nm)
                    ball_no.append(b)

                    # Capture the specific details of each ball
                    batter_name.append(ball.get('batter'))
                    bowler_name.append(ball.get('bowler'))
                    batter_runs.append(ball['runs'].get('batter', 0))
                    extra_runs.append(ball['runs'].get('extras', 0))
                    total.append(ball['runs'].get('total', 0))

                   
                    # Count boundaries only if batter runs are exactly 4 or 6
                    if ball['runs'].get('batter', 0) == 4 or ball['runs'].get('batter', 0) == 6:
                        boundary_count_for_over += 1

                    b += 1  # Move to the next ball
                    
                print(f"Over {over_nm}: Boundary Count: {boundary_count_for_over}")

                # Append the boundary count for the over after processing deliveries
                boundaries_count.append(boundary_count_for_over)

    # Extract the deliveries for each inning separately
    if len(json_data['innings']) > 0:
        print("Processing First Inning")
        extract_deliveries([json_data['innings'][0]], "First")
    if len(json_data['innings']) > 1:
        print("Processing Second Inning")
        extract_deliveries([json_data['innings'][1]], "Second")

    # Check lengths of all lists before creating DataFrame
    lengths = [
        len(match_no_list), len(inning), len(batting_team), 
        len(over_no), len(ball_no), len(batter_name), 
        len(bowler_name), len(batter_runs), len(extra_runs), 
        len(total), len(boundaries_count)
    ]
    
    # Print lengths and contents for debugging
    print(f"Lengths of lists before padding: {lengths}")  

    # Find the maximum length among the lists
    max_length = max(lengths)

    # Pad each list to match the maximum length
    match_no_list += [None] * (max_length - len(match_no_list))
    inning += [None] * (max_length - len(inning))
    batting_team += [None] * (max_length - len(batting_team))
    over_no += [None] * (max_length - len(over_no))
    ball_no += [None] * (max_length - len(ball_no))
    batter_name += [None] * (max_length - len(batter_name))
    bowler_name += [None] * (max_length - len(bowler_name))
    batter_runs += [0] * (max_length - len(batter_runs))
    extra_runs += [0] * (max_length - len(extra_runs))
    total += [0] * (max_length - len(total))
    boundaries_count += [0] * (max_length - len(boundaries_count))

    # Create DataFrame with the required ball-by-ball details and boundaries count
    return pd.DataFrame({
        'Match No': match_no_list,
        'Inning': inning,
        'Batting Team': batting_team,
        'Over': over_no,
        'Ball': ball_no,
        'Batter': batter_name,
        'Bowler': bowler_name,
        'Batter Runs': batter_runs,
        'Extra Runs': extra_runs,
        'Total Runs': total,
        'Boundaries Count': boundaries_count 
    })



# Step 5: Clean and Prepare Matches Data
def clean_matches_data(df):
    # Use .loc[] to avoid SettingWithCopyWarning
    df.loc[:, 'Year'] = df['Date'].dt.year
    df.loc[:, 'Won By'] = df.apply(lambda x: 'Chasing' if x['Winner'] in x['Teams'].split(', ') else 'Defending', axis=1)
    df.loc[:, 'City'] = df['City'].fillna(df['Venue'])
    df.loc[:, 'Winner'] = df['Winner'].fillna('Tied')
    df.loc[:, 'Player_of_Match'] = df['Player_of_Match'].fillna('None')
    return df

# Step 6: Geopy for City Coordinates
def add_city_coordinates(df):
    geolocator = Nominatim(user_agent="geoapiExercises")
    
    def get_coordinates(city):
        try:
            location = geolocator.geocode(city)
            return pd.Series([location.latitude, location.longitude])
        except:
            return pd.Series([np.nan, np.nan])
    
    df[['Latitude', 'Longitude']] = df['City'].apply(get_coordinates)
    return df

# Step 7: Create Summary and City DataFrames
def create_summary_df(df):
    print("Columns in DataFrame for summary:", df.columns)  # Check columns
    
    # Check if 'Total Runs' exists
    if 'Total Runs' not in df.columns:
        raise KeyError("The 'Total Runs' column is missing from the DataFrame.")
    
    summary = df.groupby('Winner').agg(
        Matches_Played=('Winner', 'count'),
        Total_Fours=('Total Runs', lambda x: (x == 4).sum()),  # Fours are deliveries with exactly 4 runs
        Total_Sixes=('Total Runs', lambda x: (x == 6).sum())   # Sixes are deliveries with exactly 6 runs
    ).reset_index()
    
    return summary.sort_values(by='Matches_Played', ascending=False)

def create_city_summary_df(df):
    # Define 'Score' as the sum of 'Total Runs' for each city
    df['Score'] = df.groupby('City')['Total Runs'].transform('sum')
    
    city_summary = df.groupby('City').agg(
        Matches_Played=('City', 'count'),
        First_Inn_Highest=('Score', 'max'),
        Second_Inn_Highest=('Score', 'max')
    ).reset_index()
    return city_summary.sort_values(by='Matches_Played', ascending=False)

# Step 8: Save DataFrames to CSV
def save_to_csv(df, filename):
    # Save to a specific directory, modify the path to your desired location
    output_directory = "C:\\STUDY\\PROGRAMS\\PYTHON\\T20 MEN'S CRICKET ANALYSIS DASHBOARD\\Datasets"
    
    # Check if output directory exists, and if not, create it
    if not os.path.exists(output_directory):
        os.makedirs(output_directory) # Create directory if it doesn't exist
    
    filepath = os.path.join(output_directory, filename)
    
    # Log the filepath where the file will be saved
    print(f"Attempting to save file to: {filepath}")
    
    try:
        df.to_csv(filepath, index=False)
        print(f"File successfully saved: {filepath}")
    except Exception as e:
        print(f"Failed to save file: {filepath}. Error: {e}")

#Main Function
def main():
    # Step 1: Fetch File Paths and Load Data
    directory = "C:\\STUDY\\PROGRAMS\\PYTHON\\T20 MEN'S CRICKET ANALYSIS DASHBOARD\\Datasets\\JSON DATA"
    filepaths = fetch_filepaths(directory)

    # Extract data from JSON
    raw_data = extract_json_data(filepaths)
    print("Raw Data extracted successfully.")
    print(raw_data.head())  # Check the raw data extracted

    # Step 2: Preprocess Data
    try:
        final_df = preprocess_data(raw_data)
        print("Data after preprocessing:")
        print(final_df.head())  # Check the structure of the preprocessed data
    except Exception as e:
        print(f"Error in preprocessing data: {e}")
        return

    # Step 3: Extract Ball-by-Ball Data
    ball_by_ball_data = pd.DataFrame()  # Initialize an empty DataFrame
    for index, row in final_df.iterrows():
        match_no = row['Match_id']
        json_data = json.loads(open(filepaths[index], 'r').read())  # Load corresponding JSON data
        ball_data = extract_ball_by_ball_data(json_data, match_no)
        ball_by_ball_data = pd.concat([ball_by_ball_data, ball_data], ignore_index=True)

    # Step 4: Clean and Prepare Matches Data
    try:
        matches_data = clean_matches_data(final_df)
        print("Matches DataFrame after cleaning and preprocessing:")
        print(matches_data.head())  # Check the structure of the DataFrame
    except Exception as e:
        print(f"Error in cleaning matches data: {e}")
        return

    # Step 5: Add Total Runs to Matches Data
    total_runs = ball_by_ball_data.groupby('Match No')['Total Runs'].sum().reset_index()
    matches_data = matches_data.merge(total_runs, left_on='Match_id', right_on='Match No', how='left')
    matches_data.rename(columns={'Total Runs': 'Total Runs'}, inplace=True)

    # Step 6: Create City Summary DataFrame
    try:
        city_df = create_city_summary_df(matches_data)
        print("City Summary DataFrame created:")
        print(city_df.head())
    except Exception as e:
        print(f"Error in creating city summary DataFrame: {e}")
        return

    # Step 7: Add City Coordinates
    try:
        matches_data_with_coords = add_city_coordinates(matches_data)
        print("Matches DataFrame after adding coordinates:")
        print(matches_data_with_coords.head())
    except Exception as e:
        print(f"Error in adding city coordinates: {e}")
        return

    # Step 8: Create Summary DataFrames
    try:
        summary_df = create_summary_df(matches_data_with_coords)
        print("Summary DataFrame created:")
        print(summary_df.head())
    except Exception as e:
        print(f"Error in creating summary DataFrame: {e}")
        return

    # Step 9: Save Final DataFrames as CSV
    save_to_csv(matches_data_with_coords, 'T20_Matches_Data.csv')
    save_to_csv(summary_df, 'T20_Summary_Data.csv')
    save_to_csv(ball_by_ball_data, 'T20_Ball_by_Ball_Data.csv')
    save_to_csv(city_df, 'T20_City_Summary_Data.csv')

if __name__ == "__main__":
    main()
