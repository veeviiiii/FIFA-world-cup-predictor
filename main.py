from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import pickle
import numpy as np
import os
import uvicorn

# Initialize the FastAPI app
app = FastAPI(
    title="FIFA Score Predictor API",
    description="API to serve engineered ML features and predict World Cup match outcomes using XGBoost."
)

# Configure CORS middleware to allow all origins (so the frontend can access it without blockages)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to hold our features DataFrame, trained ML model, and player data in memory
team_features_df = None
xgb_model = None
players_df = None

@app.on_event("startup")
def load_data_and_model():
    """
    On startup, load the engineered_team_features.csv, the xgboost_model.pkl, 
    and prepare player data for the frontend.
    """
    global team_features_df, xgb_model, players_df
    
    # 1. Load the engineered features
    try:
        team_features_df = pd.read_csv('engineered_team_features.csv')
        # Set 'Team' as the index for faster O(1) lookups later
        team_features_df.set_index('Team', inplace=True)
        print("Successfully loaded engineered_team_features.csv into memory.")
    except FileNotFoundError:
        print("Error: 'engineered_team_features.csv' not found. Features won't be available.")
        team_features_df = pd.DataFrame(columns=['team_current_form_xg'])
        
    # 2. Load the trained XGBoost model
    try:
        with open('xgboost_model.pkl', 'rb') as f:
            xgb_model = pickle.load(f)
        print("Successfully loaded xgboost_model.pkl into memory.")
    except FileNotFoundError:
        print("Error: 'xgboost_model.pkl' not found. Predictions will fail.")
        xgb_model = None

    # 3. Load player data for the new endpoint
    try:
        # Load raw data to extract individual players and calculate their form on the fly
        # (Since engineered_team_features.csv is aggregated by Team based on earlier steps)
        raw_df = pd.read_csv('raw_wc_player_stats.csv')
        
        # Calculate decay_weight and current form score for players
        if 'Date' in raw_df.columns and 'match_date' not in raw_df.columns:
            raw_df.rename(columns={'Date': 'match_date'}, inplace=True)
            
        if 'match_date' not in raw_df.columns:
            # Create a dummy match_date column if it doesn't exist
            raw_df['match_date'] = pd.to_datetime('today') - pd.to_timedelta(np.random.randint(0, 30, size=len(raw_df)), unit='D')
            
        raw_df['match_date'] = pd.to_datetime(raw_df['match_date'], errors='coerce')
        raw_df = raw_df.dropna(subset=['match_date'])
        
        current_date = pd.to_datetime('today')
        raw_df['days_ago'] = (current_date - raw_df['match_date']).dt.days
        raw_df['days_ago'] = raw_df['days_ago'].clip(lower=0)
        
        # W(d) = e^(-lambda * d)
        raw_df['decay_weight'] = np.exp(-0.05 * raw_df['days_ago'])
        
        # Figure out the xG column
        xg_col = 'xG' if 'xG' in raw_df.columns else ('Expected_xG' if 'Expected_xG' in raw_df.columns else None)
        if xg_col is None:
            raw_df['xG'] = np.random.uniform(0.0, 1.5, size=len(raw_df))
            xg_col = 'xG'
            
        raw_df['current_form_score'] = raw_df[xg_col] * raw_df['decay_weight']
        
        # Normalize typical FBref columns for the frontend
        name_col = 'Player' if 'Player' in raw_df.columns else raw_df.columns[0]
        nation_col = 'Nation' if 'Nation' in raw_df.columns else ('Squad' if 'Squad' in raw_df.columns else raw_df.columns[1])
        pos_col = 'Pos' if 'Pos' in raw_df.columns else raw_df.columns[2]
        
        raw_df.rename(columns={name_col: 'Name', nation_col: 'Country', pos_col: 'Position'}, inplace=True)
        
        # Extract necessary columns and get the top 20 players by current form
        cols_to_keep = ['Name', 'Country', 'Position', 'decay_weight', 'current_form_score']
        players_df = raw_df[cols_to_keep].sort_values(by='current_form_score', ascending=False).head(20)
        print("Successfully loaded and processed player data.")
    except FileNotFoundError:
        print("Error: 'raw_wc_player_stats.csv' not found. Player endpoint will be empty.")
        players_df = pd.DataFrame(columns=['Name', 'Country', 'Position', 'decay_weight', 'current_form_score'])


@app.get("/api/matchup")
def get_matchup(team_a: str = Query(..., description="Name of the first team"), 
                team_b: str = Query(..., description="Name of the second team")):
    """
    Retrieves the current forms for both requested teams, calculates the form difference,
    and passes these features into the loaded XGBoost model to get exact win probabilities.
    """
    if team_features_df is None or team_features_df.empty:
        raise HTTPException(status_code=500, detail="Feature data is not available.")
    if xgb_model is None:
        raise HTTPException(status_code=500, detail="Machine learning model is not available.")

    try:
        form_a = float(team_features_df.loc[team_a, 'team_current_form_xg'])
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Team '{team_a}' not found in the dataset.")
        
    try:
        form_b = float(team_features_df.loc[team_b, 'team_current_form_xg'])
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Team '{team_b}' not found in the dataset.")

    form_diff = form_a - form_b
    
    features_df = pd.DataFrame([{
        'team_a_form': form_a,
        'team_b_form': form_b,
        'form_difference': form_diff
    }])
    
    probabilities = xgb_model.predict_proba(features_df)[0]
    prob_b = float(probabilities[0]) 
    prob_a = float(probabilities[1])

    return {
        "team_a": team_a,
        "team_b": team_b,
        "form_score_a": round(form_a, 4),
        "form_score_b": round(form_b, 4),
        "win_probability_a": round(prob_a, 4),
        "win_probability_b": round(prob_b, 4)
    }

@app.get("/api/fixtures")
def get_fixtures():
    """
    Returns a JSON list of upcoming World Cup fixtures (mocked).
    Calculates form differences and includes predicted win probabilities.
    """
    if team_features_df is None or team_features_df.empty or xgb_model is None:
        raise HTTPException(status_code=500, detail="Model or data not available.")
    
    # Get a list of available teams
    teams = list(team_features_df.index)
    if len(teams) < 8:
        # If we don't have enough real teams in the dataset, append mock teams for demonstration
        mock_teams = ["Argentina", "France", "Brazil", "England", "Spain", "Germany", "Portugal", "Netherlands"]
        for t in mock_teams:
            if t not in teams:
                teams.append(t)
                # Assign random form for mock teams
                team_features_df.loc[t] = [np.random.uniform(0.5, 3.0)]

    # Create 4 mock quarter-final fixtures
    mock_matches = [
        {"team_a": teams[0], "team_b": teams[1]},
        {"team_a": teams[2], "team_b": teams[3]},
        {"team_a": teams[4], "team_b": teams[5]},
        {"team_a": teams[6], "team_b": teams[7]}
    ]
    
    results = []
    for match in mock_matches:
        team_a = match['team_a']
        team_b = match['team_b']
        
        # Calculate form difference
        form_a = float(team_features_df.loc[team_a, 'team_current_form_xg'])
        form_b = float(team_features_df.loc[team_b, 'team_current_form_xg'])
        form_diff = form_a - form_b
        
        # Run through XGBoost model
        features_df = pd.DataFrame([{
            'team_a_form': form_a,
            'team_b_form': form_b,
            'form_difference': form_diff
        }])
        
        probabilities = xgb_model.predict_proba(features_df)[0]
        prob_b = float(probabilities[0])
        prob_a = float(probabilities[1])
        
        results.append({
            "team_a": team_a,
            "team_b": team_b,
            "team_a_prob": round(prob_a * 100, 1),
            "team_b_prob": round(prob_b * 100, 1)
        })
        
    return results

@app.get("/api/players")
def get_players():
    """
    Returns the top 20 players based on their calculated current form score.
    """
    if players_df is None or players_df.empty:
        raise HTTPException(status_code=500, detail="Player data not available.")
    
    # Convert DataFrame to a list of dictionaries for JSON response
    # Fill NaN values with an empty string or suitable default
    results = players_df.fillna("").to_dict(orient="records")
    return results

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
