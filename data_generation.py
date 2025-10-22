"""
Generates data to be used for models. Play by play game data
and game result data will be used to predict attention
Last updated 10/22 by EK
"""

import pandas as pd
from datetime import timedelta
from data_mountain_query.query import get_ambient_tweets
from data_mountain_query.connection import get_connection
import time


def main():
    start_time = time.time()
    
    # Load games
    games = pd.read_csv("/Users/elisabethkollrack/Thesis/EK-thesis/games.csv")
    games = games[games['game_type'] == 'REG']
    games['gameday'] = pd.to_datetime(games['gameday'], format='%m/%d/%y')
    
    # Load cumulative win percentages
    win_pct = pd.read_csv("/Users/elisabethkollrack/Thesis/EK-thesis/nfl_r_data.csv")
    
    # Merge win_pct into games on 'game_id'
    games = games.merge(
        win_pct[['game_id', 'home_win_pct', 'away_win_pct', 'lead_changes']],
        on='game_id',
        how='left'
    )

    p = 1.0
    collection, client = get_connection(p=p)

    data_rows = []  # store data for final DataFrame

    # Loop over each season 2013–2017
    for season in range(2013, 2018):
        # Filter the games for that season
        games_season = games[games['season'] == season]

        # Unique matchups (order-insensitive)
        games_season['matchup_key'] = games_season.apply(
            lambda r: "_vs_".join(sorted([r['away_team'], r['home_team']])), axis=1
        )

        for _, row in games_season.iterrows():
            team1, team2 = row['away_team'], row['home_team']
            gameday = row['gameday']
            total_score = row['total']
            score_diff = abs(row['result'])

            anchors = [f"#{team1}vs{team2}", f"#{team2}vs{team1}"]
            start_date = gameday - timedelta(days=7)
            end_date = gameday + timedelta(days=7)
            dates = pd.date_range(start_date, end_date, freq='D')

            counts = {}
            for anchor in anchors:
                tweets_list = [t for t in get_ambient_tweets(anchor, dates, collection)]
                for tweet in tweets_list:
                    tweet_day = pd.to_datetime(tweet['tweet_created_at']).date()
                    counts[tweet_day] = counts.get(tweet_day, 0) + 1

            # total attention for this game (sum over the ±7 days)
            attention = sum(counts.get((gameday + timedelta(days=d)).date(), 0) for d in range(-7, 8))

            data_rows.append({
                'date': gameday.date(),
                'game_id': row['game_id'],
                'season': row['season'],
                'week': row['week'],
                'weekday': row['weekday'],
                'gametime': row['gametime'],
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'home_win_pct': row['home_win_pct'],
                'away_win_pct': row['away_win_pct'],
                'num_lead_changes': int(row['lead_changes']),
                'total_score': total_score,
                'score_differential': score_diff,
                'overtime': int(row['overtime']),
                'attention': attention
            })

    # Create final DataFrame
    df = pd.DataFrame(data_rows)
    
    # Save to CSV
    output_path = "/Users/elisabethkollrack/Thesis/EK-thesis/game_attention.csv"
    df.to_csv(output_path, index=False)
    
    print(df.head())  # preview
    print(f"\nSaved to: {output_path}")
    print(f"Total rows: {len(df)}")

    end_time = time.time()
    elapsed = end_time - start_time
    print(f"\nTotal runtime: {elapsed:.2f} seconds")

    return df

if __name__ == '__main__':
    main()
