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

    # Initialize storage for 5h before kickoff to 24h after
    times = {}
    for time in range(-5, 25):
        times[time] = 0

    num_games = 0

    # 2013-2017
    all_games = games[(games['season'] >= 2013) & (games['season'] <= 2017)]

    # loop through all games in range
    for _, row in all_games.iterrows():
        away = row['away_team']
        home = row['home_team']
        gameday = row['gameday']
        gametime = row['gametime']

        kickoff = pd.to_datetime(str(gameday.date()) + " " + str(gametime))

        start_time = kickoff - timedelta(hours=5)
        end_time = kickoff + timedelta(hours=24)
        dates = pd.date_range(start_time, end_time, freq='h')

        anchors = [f"#{away}vs{home}", f"#{home}vs{away}"]

        # Collect tweets for all hashtag combos
        tweets = []
        for anchor in anchors:
            tweets.extend([t for t in get_ambient_tweets(anchor, dates, collection)])

        # if no tweets are found
        if not tweets:
            continue

        tweets_df = pd.DataFrame(tweets)
        tweets_df['tweet_created_at'] = pd.to_datetime(tweets_df['tweet_created_at'])
        tweets_df['hour'] = tweets_df['tweet_created_at'].dt.floor('h')

        # Group by hour
        hourly_counts = tweets_df.groupby('hour').size().reset_index(name='count')
        hourly_dict = dict(zip(hourly_counts['hour'], hourly_counts['count']))

        # Align tweet counts relative to kickoff
        for time in range(-5, 25):
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

    # Print results
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


    # Plot the attention curve
    plt.figure(figsize=(10, 6))
    plt.plot(attention_times['times'], attention_times['avg_tweets'], marker='o', color='blue', linewidth=2)

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
