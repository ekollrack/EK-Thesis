"""
This code trains a Linear Regression model to predict attention
based on total_score and score_differential, and generates diagnostic plots.
Last updated 10/19 by EK
"""

from statsmodels.stats.outliers_influence import variance_inflation_factor
import pandas as pd

games = pd.read_csv("/Users/elisabethkollrack/Thesis/EK-thesis/game_attention.csv")
categorical_cols = ['weekday', 'home_team', 'away_team']
games_encoded = pd.get_dummies(games, columns = categorical_cols, drop_first = True)
X = games_encoded.select_dtypes(include='number').drop(columns=['attention'])
vif = pd.DataFrame()
vif['feature'] = X.columns
vif['VIF'] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
print(vif.sort_values(by='VIF', ascending=False))
