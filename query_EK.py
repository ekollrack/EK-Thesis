"""
Function to query various anchors for testing purposes.
Shows the total amount of tweets for the selected matchup throughout the dataset
Last updated 10/15 by EK
"""

import pandas as pd
from datetime import datetime, timedelta
from data_mountain_query.query import get_ambient_tweets
from data_mountain_query.connection import get_connection


def main():
    games = pd.read_csv("/Users/elisabethkollrack/Thesis/EK-thesis/games.csv")
    games = games[games['game_type'] == 'REG']
    games['gameday'] = pd.to_datetime(games['gameday'], format='%m/%d/%y')

    # Assign season year
    games['season_year'] = games['gameday'].apply(
        lambda d: d.year - 1 if d.month == 1 else d.year
    )

    matchups = {
        "DAL_vs_NYG": {
            "filter": (
                ((games['away_team'] == 'DAL') & (games['home_team'] == 'NYG')) |
                ((games['away_team'] == 'NYG') & (games['home_team'] == 'DAL'))
            ),
            "anchors": ["#NYGvsDAL", "#DALvsNYG"]
        }
    }

    results_all = []
    p = 1.0
    collection, client = get_connection(p=p)

    for name, info in matchups.items():
        games_filtered = games[
            (games['season_year'] == 2013) &
            info["filter"]
        ][['gameday', 'total', 'result', 'season_year']]

        # Get the first matchup of 2013
        if len(games_filtered) > 0:
            first_matchup = games_filtered.iloc[0]
            gameday = first_matchup['gameday'].date()
            
            # Define 3-day window: day before, gameday, day after
            start_date = gameday - timedelta(days=1)
            end_date = gameday + timedelta(days=1)
            dates = pd.date_range(start_date, end_date, freq='D')

            counts = {}
            total_tweets = 0

            for anchor in info["anchors"]:
                tweets_list = [t for t in get_ambient_tweets(anchor, dates, collection)]
                for tweet in tweets_list:
                    tweet_day = pd.to_datetime(tweet['tweet_created_at']).date()
                    if tweet_day in counts:
                        counts[tweet_day] = counts[tweet_day] + 1
                    else:
                        counts[tweet_day] = 1
                    total_tweets += 1

            # Sum counts for the 3-day window
            window_tweets = 0
            for d in range(-1, 2):  # -1, 0, +1 days
                day = gameday + timedelta(days=d)
                if day in counts:
                    window_tweets += counts[day]

            results_all.append({
                "matchup": name,
                "matchup_number": "2013 Matchup 1",
                "gameday": gameday,
                "3_day_window_start": start_date,
                "3_day_window_end": end_date,
                "total_tweets_in_window": window_tweets,
                "total_tweets_collected": total_tweets,
                "score": first_matchup["total"],
                "score_differential": abs(first_matchup["result"])
            })

    results_df = pd.DataFrame(results_all)
    print(results_df)
    
    # Print summary
    if len(results_df) > 0:
        print(f"\nSUMMARY:")
        print(f"First DAL vs NYG matchup in 2013: {results_df.iloc[0]['gameday']}")
        print(f"3-day window: {results_df.iloc[0]['3_day_window_start']} to {results_df.iloc[0]['3_day_window_end']}")
        print(f"Total tweets in 3-day window: {results_df.iloc[0]['total_tweets_in_window']}")
    
    return results_df


if __name__ == '__main__':
    main()