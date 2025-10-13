import pandas as pd
from datetime import datetime, timedelta
from data_mountain_query.query import get_ambient_tweets
from data_mountain_query.connection import get_connection
import matplotlib.pyplot as plt
import warnings
import os

# Suppress pymongo timeout warnings
warnings.filterwarnings("ignore", message="use an explicit session with no_cursor_timeout=True")


def main():
    # --- Load game data ---
    games = pd.read_csv("/Users/elisabethkollrack/Thesis/EK-thesis/games.csv")

    # Only include regular season games
    games = games[games['game_type'] == 'REG']
    games['gameday'] = pd.to_datetime(games['gameday'], format='%m/%d/%y')

    # Check if tweet counts already exist (for faster reruns)
    if os.path.exists("tweet_counts_per_game.csv"):
        print("✅ Loading saved tweet counts from CSV...")
        tweet_counts_df = pd.read_csv("tweet_counts_per_game.csv")

        # Compute average tweets per hour offset
        attention_times = (
            tweet_counts_df.groupby("hour_offset")["tweet_count"]
            .mean()
            .reset_index(name="avg_tweets")
        )

        # Plot from saved data
        plt.figure(figsize=(10, 6))
        plt.plot(attention_times['hour_offset'], attention_times['avg_tweets'],
                 marker='o', color='blue', linewidth=2)
        plt.axvline(0, color='red', linestyle='--', linewidth=1.5, label='Kickoff')
        plt.title("Average Attention Around Kickoff (From Saved Data)")
        plt.xlabel("Hours Relative to Kickoff")
        plt.ylabel("Average Tweets per Hour")
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.show()
        return

    # --- MongoDB connection ---
    p = 1.0
    collection, client = get_connection(p=p)

    # Initialize storage for 5h before to 48h after kickoff
    times = {time: 0 for time in range(-5, 49)}
    num_games = 0

    # Filter for desired seasons
    all_games = games[(games['season'] >= 2013) & (games['season'] <= 2017)]

    # --- Main tweet collection loop ---
    for _, row in all_games.iterrows():
        away = row['away_team']
        home = row['home_team']
        gameday = row['gameday']
        gametime = row['gametime']

        kickoff = pd.to_datetime(str(gameday.date()) + " " + str(gametime))

        # Define time window: 5h before → 48h after
        start_time = kickoff - timedelta(hours=5)
        end_time = kickoff + timedelta(hours=48)
        dates = pd.date_range(start_time, end_time, freq='h')

        anchors = [f"#{away}vs{home}", f"#{home}vs{away}"]

        # Collect tweets for both hashtag orders
        tweets = []
        for anchor in anchors:
            tweets.extend([t for t in get_ambient_tweets(anchor, dates, collection)])

        # Skip if no tweets
        if not tweets:
            continue

        # Convert tweets to DataFrame and group hourly
        tweets_df = pd.DataFrame(tweets)
        tweets_df['tweet_created_at'] = pd.to_datetime(tweets_df['tweet_created_at'])
        tweets_df['hour'] = tweets_df['tweet_created_at'].dt.floor('h')

        hourly_counts = tweets_df.groupby('hour').size().reset_index(name='count')
        hourly_dict = dict(zip(hourly_counts['hour'], hourly_counts['count']))

        # Align tweet counts relative to kickoff
        for time in range(-5, 49):
            time_point = kickoff + timedelta(hours=time)
            count = hourly_dict.get(time_point.floor('h'), 0)
            times[time] += count
        

        num_games += 1
        print(f"Processed game {num_games}: {away} vs {home} ({kickoff})")

        # --- Save per-game tweet counts for reuse ---
        game_data = pd.DataFrame({
            'away_team': [away] * 54,
            'home_team': [home] * 54,
            'kickoff': [kickoff] * 54,
            'hour_offset': list(range(-5, 49)),
            'tweet_count': [hourly_dict.get(kickoff + timedelta(hours=t), 0) for t in range(-5, 49)]
        })

        game_data.to_csv(
            "tweet_counts_per_game.csv",
            mode='a',
            header=not os.path.exists("tweet_counts_per_game.csv"),
            index=False
        )

    # --- Compute overall averages ---
    avg_tweets_hour = {time: times[time] / num_games for time in times}

    attention_times = pd.DataFrame(list(avg_tweets_hour.items()), columns=['times', 'avg_tweets'])
    attention_times = attention_times.sort_values('times')

    print("\n=== Average Attention Relative to Kickoff (All Games 2013–2017) ===")
    print("Label | Avg Tweet Count")
    for time, avg in avg_tweets_hour.items():
        if time == 0:
            label = "Kickoff"
        elif time < 0:
            label = f"{abs(time)}h before"
        else:
            label = f"{time}h after"
        print(f"{label:>10} | {avg:.2f}")

    # --- Plot the attention curve ---
    plt.figure(figsize=(10, 6))
    plt.plot(attention_times['times'], attention_times['avg_tweets'],
             marker='o', color='blue', linewidth=2)
    plt.axvline(0, color='red', linestyle='--', linewidth=1.5, label='Kickoff')
    plt.title("Average Attention Around Kickoff (2013–2017)")
    plt.xlabel("Hours Relative to Kickoff")
    plt.ylabel("Average Tweets per Hour")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.show()

    return attention_times


if __name__ == '__main__':
    main()
