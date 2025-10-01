import pandas as pd
from datetime import datetime, timedelta
from data_mountain_query.query import get_ambient_tweets
from data_mountain_query.connection import get_connection
import matplotlib.pyplot as plt


def main():
    games = pd.read_csv("/Users/elisabethkollrack/Thesis/EK-thesis/games.csv")
    games = games[games['game_type'] == 'REG']
    games['gameday'] = pd.to_datetime(games['gameday'], format='%m/%d/%y')

    # Assign season year
    games['season_year'] = games['gameday'].apply(
        lambda d: d.year - 1 if d.month == 1 else d.year
    )

    matchups = {
        "SEA_vs_SF": {
            "filter": (
                ((games['away_team'] == 'SEA') & (games['home_team'] == 'SF')) |
                ((games['away_team'] == 'SF') & (games['home_team'] == 'SEA'))
            ),
            "anchors": ["#SEAvsSF", "#SFvsSEA"]
        }
    }

    p = 1.0
    collection, client = get_connection(p=p)

    for name, info in matchups.items():
        games_filtered = games[
            (games['season_year'] == 2013) &
            info["filter"]
        ][['gameday', 'gametime', 'total', 'result', 'season_year']].reset_index(drop=True)

        if len(games_filtered) == 0:
            print("No games found for 2013.")
            return

        # Get game day + kickoff time
        gameday = games_filtered.loc[0, "gameday"]
        gametime = games_filtered.loc[0, "gametime"]
        kickoff = pd.to_datetime(str(gameday.date()) + " " + str(gametime))

        # We only want day before, gameday, and day after
        start_date = gameday - timedelta(days=0)
        end_date = gameday + timedelta(days=2)
        dates = pd.date_range(start_date, end_date, freq='H')  # HOURLY

        # Collect tweets
        tweets = []
        for anchor in info["anchors"]:
            tweets.extend([t for t in get_ambient_tweets(anchor, dates, collection)])

        # Put into DataFrame
        tweets_df = pd.DataFrame(tweets)
        tweets_df['tweet_created_at'] = pd.to_datetime(tweets_df['tweet_created_at'])
        tweets_df['hour'] = tweets_df['tweet_created_at'].dt.floor('H')

        # Group by hour
        hourly_counts = tweets_df.groupby('hour').size().reset_index(name='count')

        # Plot
        plt.figure(figsize=(12, 6))
        plt.plot(hourly_counts['hour'], hourly_counts['count'], marker='o', linestyle='-')

        # Mark kickoff time
        plt.axvline(kickoff, color='red', linestyle='--', linewidth=2, label='Kickoff')

        # Shade ~3 hours for game duration
        plt.axvspan(kickoff, kickoff + timedelta(hours=3), color='red', alpha=0.1, label='Game Duration')

        plt.title(f"Hourly Attention: {name} (2013 First Matchup)")
        plt.xlabel("Time (Hourly)")
        plt.ylabel("Tweet Count")
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()

        plt.show()

        return hourly_counts


if __name__ == '__main__':
    main()
