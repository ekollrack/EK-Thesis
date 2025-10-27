"""
This code graphs and prints average attention of all NFL games 
(2013-2017 seasons) per half hour relative to kickoff.
Last modified: 10/15/2025 by EK
"""

import pandas as pd
import numpy as np
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

    # Initialize 30-minute bins from 5 hours before to 15 hours after kickoff
    times = {t: 0 for t in np.arange(-5, 15, 0.5)}
    num_games = 0

    # 2013-2017
    all_games = games[(games['season'] >= 2013) & (games['season'] <= 2017)]

    # loop through all games in range
    for _, row in all_games.iterrows():
        away = row['away_team']
        home = row['home_team']
        gameday = row['gameday']
        gametime = row['gametime']

        # Localize kickoff as EST (DST-aware)
        kickoff = pd.to_datetime(str(gameday.date()) + " " + str(gametime))
        kickoff = kickoff.tz_localize('US/Eastern')

        start_time = kickoff - timedelta(hours=5)
        end_time = kickoff + timedelta(hours=15)
        dates = pd.date_range(start_time, end_time, freq='30min')

        anchors = [f"#{away}vs{home}", f"#{home}vs{away}"]

        # Collect tweets for all hashtag combos
        tweets = []
        for anchor in anchors:
            tweets.extend([t for t in get_ambient_tweets(anchor, dates, collection)])

        # if no tweets are found, skip this game
        if not tweets:
            continue

        tweets_df = pd.DataFrame(tweets)

        # Convert tweet timestamps from GMT/UTC to EST with DST handling
        tweets_df['tweet_created_at'] = pd.to_datetime(tweets_df['tweet_created_at'], utc=True)
        tweets_df['tweet_created_at'] = tweets_df['tweet_created_at'].dt.tz_convert('US/Eastern')

        # Bin into 30-minute intervals
        tweets_df['time_bin'] = tweets_df['tweet_created_at'].dt.floor('30min')

        # Group by 30-minute interval
        half_hour_counts = tweets_df.groupby('time_bin').size().reset_index(name='count')
        count_dict = dict(zip(half_hour_counts['time_bin'], half_hour_counts['count']))

        # Align counts relative to kickoff
        for t in times.keys():
            time_point = kickoff + timedelta(hours=t)
            count = count_dict.get(time_point.floor('30min'), 0)
            times[t] += count

        num_games += 1

    # Compute average attention per half hour
    avg_tweets_half_hour = {t: times[t] / num_games for t in times}

    # Convert to DataFrame for plotting
    attention_times = pd.DataFrame(list(avg_tweets_half_hour.items()), columns=['times', 'avg_tweets'])
    attention_times = attention_times.sort_values('times')

    # Print results
    print("\n=== Average Attention Relative to Kickoff (All Games 2013–2017, 30-minute intervals) ===")
    print("Label | Avg Tweet Count")
    for time, avg in avg_tweets_half_hour.items():
        if time == 0:
            label = "Kickoff"
        elif time < 0:
            label = f"{abs(time)}h before"
        else:
            label = f"{time}h after"
        print(f"{label:>10} | {avg:.2f}")

    # Plot the attention curve
    plt.figure(figsize=(10, 6))
    plt.plot(attention_times['times'], attention_times['avg_tweets'], marker='o', linewidth=2)

    plt.axvline(0, linestyle='--', linewidth=1.5, label='Kickoff')
    plt.title("Average Attention Around Kickoff (2013–2017, 30-minute intervals)")
    plt.xlabel("Hours Relative to Kickoff")
    plt.ylabel("Average Tweets per Half Hour")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.show()

    return attention_times


if __name__ == '__main__':
    main()
