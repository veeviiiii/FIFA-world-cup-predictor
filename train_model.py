import pandas as pd
import numpy as np
import pickle
import itertools
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score

def main():
    # 1. Load engineered_team_features.csv using Pandas
    input_file = 'engineered_team_features.csv'
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: '{input_file}' not found. Please ensure feature_engineer.py has been run.")
        return

    # Check if we have enough teams to create matchups
    if len(df) < 2:
        print("Not enough teams to generate matchups. We need at least 2 teams.")
        return

    # 2. Data Preparation: Create a synthetic training dataset of historical matchups.
    # We will generate all possible pair combinations (Team A vs Team B).
    matchups = []
    
    print("Generating synthetic matchup dataset...")
    # Generate all possible permutations of matchups between teams
    for team_a, team_b in itertools.permutations(df['Team'], 2):
        # Extract the current form score for Team A and Team B
        form_a = df.loc[df['Team'] == team_a, 'team_current_form_xg'].values[0]
        form_b = df.loc[df['Team'] == team_b, 'team_current_form_xg'].values[0]
        
        # Calculate the form difference feature
        form_diff = form_a - form_b
        
        # 3. Target Variable: Create a binary target column 'team_a_win'
        # 1 if Team A's form > Team B's form + a small random noise threshold to simulate upsets, 0 otherwise.
        # We add a random noise drawn from a normal distribution to introduce uncertainty.
        noise = np.random.normal(0, 0.2)
        team_a_win = 1 if form_a > (form_b + noise) else 0
        
        matchups.append({
            'team_a_form': form_a,
            'team_b_form': form_b,
            'form_difference': form_diff,
            'team_a_win': team_a_win
        })

    # Convert the synthetic matchups into a pandas DataFrame
    train_df = pd.DataFrame(matchups)
    
    # Define our input features (X) and target variable (y)
    feature_cols = ['team_a_form', 'team_b_form', 'form_difference']
    X = train_df[feature_cols]
    y = train_df['team_a_win']

    # 4. Model Training: Initialize an XGBClassifier from the xgboost library
    # Using basic parameters suitable for this synthetic classification task
    model = XGBClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=42,
        eval_metric='logloss' # Explicitly set eval_metric to avoid warnings
    )

    # Train the model on the features against the target
    print("Training XGBoost classifier...")
    model.fit(X, y)

    # 5. Print the model's training accuracy to the console
    y_pred = model.predict(X)
    accuracy = accuracy_score(y, y_pred)
    print(f"Model training complete. Training Accuracy: {accuracy * 100:.2f}%")

    # 6. Serialization: Use the pickle library to save the trained model
    model_filename = 'xgboost_model.pkl'
    with open(model_filename, 'wb') as f:
        pickle.dump(model, f)
        
    print(f"Model successfully saved as '{model_filename}'.")

if __name__ == "__main__":
    main()
