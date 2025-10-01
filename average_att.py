import pandas as pd
from datetime import timedelta
from data_mountain_query.query import get_ambient_tweets
from data_mountain_query.connection import get_connection
import matplotlib.pyplot as plt
import time

def main():
    start_time = time.time()
    
    # Load games
    games = pd.read_csv("/Users/elisabethkollrack/Thesis/games.csv")
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

    # Combine all seasons into one line (average attention per week)
    weekly_totals = {}

    for season, counts in total_counts_all.items():
        for week, attention in counts.items():
            if week not in weekly_totals:
                weekly_totals[week] = []
            weekly_totals[week].append(attention)

    # Compute average attention per week
    weekly_avg = {week: sum(vals)/len(vals) for week, vals in weekly_totals.items()}

    # Plot single line
    plt.figure(figsize=(12, 6))
    df_avg = pd.DataFrame(list(weekly_avg.items()), columns=['week', 'attention']).sort_values('week')
    plt.plot(df_avg['week'], df_avg['attention'], marker='o', linestyle='-', color='blue')

    plt.title('Average Weekly Attention (2013–2017)')
    plt.xlabel('Week')
    plt.ylabel('Average Attention')
    plt.xticks(range(1, 18))
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"\nTotal runtime: {elapsed:.2f} seconds")

    return total_counts_all

if __name__ == '__main__':
    main()

