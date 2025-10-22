"""
This code trains a Linear Regression model to predict attention
based on total_score, score_differential, home_team, away_team, and date.
Last updated 10/19 by EK
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder


def main():
    
    # Load the dataset
    games = pd.read_csv("/Users/elisabethkollrack/Thesis/EK-thesis/game_attention.csv")

    # Define features (X) and target (y)
    X = games[['total_score', 'score_differential']]
    y = games['attention']

    # Split into training and testing sets (80/20)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize Linear Regression model
    model = LinearRegression()

    # Train model
    model.fit(X_train, y_train)

    # Make predictions
    y_pred = model.predict(X_test)

    # Evaluate model
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print("\nLinear Regression Results")
    print("-------------------------")
    print(f"Mean Absolute Error: {mae:.2f}")
    print(f"R² Score: {r2:.3f}")

    # Show coefficients
    coef_df = pd.DataFrame({
        'Feature': X.columns,
        'Coefficient': model.coef_
    })

    print("\nFeature Coefficients:")
    print(coef_df)


    return model, coef_df

if __name__ == '__main__':
    main()
