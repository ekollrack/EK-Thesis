"""
This code graphs the weekly attention year over year for each season
Last modified 10/15 by EK
"""

import pandas as pd
from datetime import timedelta
from data_mountain_query.query import get_ambient_tweets
from data_mountain_query.connection import get_connection
import matplotlib.pyplot as plt
import time

def main():
    start_time = time.time()
    
    # Load games
    games = pd.read_csv("/Users/elisabethkollrack/Thesis/EK-thesis/games.csv")
    games = games[games['game_type'] == 'REG']
    games['gameday'] = pd.to_datetime(games['gameday'], format='%m/%d/%y')

    total_counts_all = {}  # {season: {week: attention}}

    p = 1.0
    collection, client = get_connection(p=p)

    # Loop over each season 2013–2017
    for season in range(2013, 2018):
        games_season = games[games['season'] == season]
        total_counts = {}  # {week: attention}

        # Unique matchups (order-insensitive)
        games_season['matchup_key'] = games_season.apply(
            lambda r: "_vs_".join(sorted([r['away_team'], r['home_team']])), axis=1
        )
        matchups = games_season['matchup_key'].unique()

        for matchup in matchups:
            teams = matchup.split("_vs_")
            team1, team2 = teams[0], teams[1]

            games_filtered = games_season[
                ((games_season['away_team'] == team1) & (games_season['home_team'] == team2)) |
                ((games_season['away_team'] == team2) & (games_season['home_team'] == team1))
            ][['gameday', 'week']]

            if games_filtered.empty:
                continue

            anchors = [f"#{team1}vs{team2}", f"#{team2}vs{team1}"]

            start_date = games_filtered['gameday'].min() - timedelta(days=7)
            end_date = games_filtered['gameday'].max() + timedelta(days=7)
            dates = pd.date_range(start_date, end_date, freq='D')

            counts = {}
            for anchor in anchors:
                tweets_list = [t for t in get_ambient_tweets(anchor, dates, collection)]
                for tweet in tweets_list:
                    tweet_day = pd.to_datetime(tweet['tweet_created_at']).date()
                    counts[tweet_day] = counts.get(tweet_day, 0) + 1

            # Aggregate attention by week
            for _, row in games_filtered.iterrows():
                gameday = row["gameday"].date()
                week = row['week']
                for d in range(-7, 8):
                    day = gameday + timedelta(days=d)
                    total_counts[week] = total_counts.get(week, 0) + counts.get(day, 0)

        total_counts_all[season] = total_counts

    # Print total tweets per season
    print("Total tweets per season:")
    for season, counts in total_counts_all.items():
        total_tweets = sum(counts.values())
        print(f"{season}: {total_tweets}")

    # Plot line graph
    plt.figure(figsize=(12, 6))
    for season, counts in total_counts_all.items():
        df_season = pd.DataFrame(list(counts.items()), columns=['week', 'attention']).sort_values('week')
        plt.plot(df_season['week'], df_season['attention'], marker='o', linestyle='-', label=f'{season}')

    plt.title('Weekly Attention by Season (2013–2017)')
    plt.xlabel('Week')
    plt.ylabel('Total Attention')
    plt.xticks(range(1, 18))  # 17-week regular season
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    
    plt.show()
    
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"\nTotal runtime: {elapsed:.2f} seconds")

    return total_counts_all

if __name__ == '__main__':
    main()

