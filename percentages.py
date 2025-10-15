"""
This code calculates the percentage of tweets that are posted plus/minus
72 hours from kickoff out of the tweets posted plus/minus 1 week of gameday
"""


import pandas as pd
from datetime import datetime, timedelta
from data_mountain_query.query import get_ambient_tweets
from data_mountain_query.connection import get_connection
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore", message="use an explicit session with no_cursor_timeout=True")


def main():
    games = pd.read_csv("/Users/elisabethkollrack/Thesis/EK-thesis/games.csv")
    # Only want regular season
    games = games[games['game_type'] == 'REG']
    games['gameday'] = pd.to_datetime(games['gameday'], format='%m/%d/%y')

    p = 1.0
    collection, client = get_connection(p=p)

    # Initialize storage for 7 days before kickoff to 7 days after (hours)
    times = {}
    for time in range(-336, 337):  # 7 days * 24 hours = 168 hours each direction
        times[time] = 0

    num_games = 0

    # 2013–2017
    all_games = games[(games['season'] >= 2013) & (games['season'] <= 2017)]

    for _, row in all_games.iterrows():
        away = row['away_team']
        home = row['home_team']
        gameday = row['gameday']
        gametime = row['gametime']

        kickoff = pd.to_datetime(str(gameday.date()) + " " + str(gametime))

        start_time = kickoff - timedelta(hours=336)
        end_time = kickoff + timedelta(hours=336)
        dates = pd.date_range(start_time, end_time, freq='h')

        anchors = [f"#{away}vs{home}", f"#{home}vs{away}"]

        tweets = []
        for anchor in anchors:
            tweets.extend([t for t in get_ambient_tweets(anchor, dates, collection)])

        if not tweets:
            continue

        tweets_df = pd.DataFrame(tweets)
        tweets_df['tweet_created_at'] = pd.to_datetime(tweets_df['tweet_created_at'])
        tweets_df['hour'] = tweets_df['tweet_created_at'].dt.floor('h')

        hourly_counts = tweets_df.groupby('hour').size().reset_index(name='count')
        hourly_dict = dict(zip(hourly_counts['hour'], hourly_counts['count']))

        for time in range(-336, 337):
            time_point = kickoff + timedelta(hours=time)
            count = hourly_dict.get(time_point.floor('h'), 0)
            times[time] += count

        num_games += 1
        print(f"Processed game {num_games}: {away} vs {home} ({kickoff})")

    # Compute average tweets per hour offset
    avg_tweets_hour = {time: times[time] / num_games for time in times}

    # Convert to DataFrame for plotting
    attention_times = pd.DataFrame(list(avg_tweets_hour.items()), columns=['times', 'avg_tweets'])
    attention_times = attention_times.sort_values('times')

    # --- Compute total tweet counts for each time range ---
    total_5to24 = sum(times[t] for t in range(-5, 25))
    total_7day = sum(times[t] for t in range(-168, 169))
    total_14day = sum(times[t] for t in range(-336, 337))
    total_3to14 = sum(times[t] for t in range(-3, 15))
    total_72to72 = sum(times[t] for t in range(-72, 73))



    print("\n=== Total Tweet Volume Comparison ===")
    pct = (total_5to24 / total_7day) * 100
    print(f"5 hour to 24 hour / 7 to 7 day: %{pct:.2f}")
    pct_72to72 = (total_72to72 / total_7day) * 100
    print(f"72 hour to 72 hour / 7 to 7 day: %{pct_72to72:.2f}")

    return attention_times


if __name__ == '__main__':
    main()
