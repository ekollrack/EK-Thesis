"""
This code trains a Random Forest model to predict attention
based on total_score, score_differential, home_team, away_team, and date.
Last updated 10/17 by EK
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import time

def main():
    start_time = time.time()
    
    # Load the dataset
    df = pd.read_csv("/Users/elisabethkollrack/Thesis/EK-thesis/game_attention.csv")

    # Convert date to datetime and extract numeric features
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day

    # Extract home and away teams from matchup
    df[['away_team', 'home_team']] = df['matchup'].str.split('_vs_', expand=True)

    # Label encode teams
    le_team = LabelEncoder()
    df['away_encoded'] = le_team.fit_transform(df['away_team'])
    df['home_encoded'] = le_team.fit_transform(df['home_team'])

    # Define features (X) and target (y)
    X = df[['total_score', 'score_differential', 'month', 'day', 'away_encoded', 'home_encoded']]
    y = df['attention']

    # Split into training and testing sets (80/20)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize Random Forest model
    rf = RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        n_jobs=-1
    )

    # Train model
    rf.fit(X_train, y_train)

    # Make predictions
    y_pred = rf.predict(X_test)

    # Evaluate model
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print("\nRandom Forest Results")
    print("----------------------")
    print(f"Mean Absolute Error: {mae:.2f}")
    print(f"R² Score: {r2:.3f}")

    # Show feature importances
    importance_df = pd.DataFrame({
        'Feature': X.columns,
        'Importance': rf.feature_importances_
    }).sort_values(by='Importance', ascending=False)

    print("\nFeature Importances:")
    print(importance_df)

    end_time = time.time()
    elapsed = end_time - start_time
    print(f"\nTotal runtime: {elapsed:.2f} seconds")

    return rf, importance_df

if __name__ == '__main__':
    main()
