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
        "DET_vs_ARI": {
            "filter": (
                ((games['away_team'] == 'DET') & (games['home_team'] == 'ARI')) |
                ((games['away_team'] == 'ARI') & (games['home_team'] == 'DET'))
            ),
            "anchors": ["#ARIvsDET", "#DETvsARI"]
        }
    }

    results_all = []
    p = 1.0
    collection, client = get_connection(p=p)

    for name, info in matchups.items():
        games_filtered = games[
            (games['season_year'] >= 2013) &
            (games['season_year'] <= 2017) &
            info["filter"]
        ][['gameday', 'total', 'result', 'season_year']]


        start_date = games_filtered['gameday'].min() - timedelta(days=7)
        end_date = games_filtered['gameday'].max() + timedelta(days=7)
        dates = pd.date_range(start_date, end_date, freq='D')

        counts = {}

        for anchor in info["anchors"]:
            tweets_list = [t for t in get_ambient_tweets(anchor, dates, collection)]
            for tweet in tweets_list:
                tweet_day = pd.to_datetime(tweet['tweet_created_at']).date()
                if tweet_day in counts:
                    counts[tweet_day] = counts[tweet_day] + 1
                else:
                    counts[tweet_day] = 1

        for year in range(2013, 2018):
            year_games = games_filtered[games_filtered['season_year'] == year].reset_index(drop=True)
            for i in range(min(2, len(year_games))):  # Only matchup 1 and 2
                gameday = year_games.loc[i, "gameday"].date()
                total_attention = 0

                # Sum counts for 7 days before, gameday, 7 days after
                for d in range(-7, 8):
                    day = gameday + timedelta(days=d)
                    if day in counts:
                        total_attention = total_attention + counts[day]

                results_all.append({
                    "matchup": name,
                    "matchup number": f"{year} Matchup {i+1}",
                    "total score": year_games.loc[i, "total"],
                    "score differential": abs(year_games.loc[i, "result"]),
                    "attention": total_attention
                })

    results_df = pd.DataFrame(results_all)
    print(results_df)
    return results_df


if __name__ == '__main__':
    main()
