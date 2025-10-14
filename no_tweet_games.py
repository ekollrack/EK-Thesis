import pandas as pd
from datetime import timedelta
from data_mountain_query.query import get_ambient_tweets
from data_mountain_query.connection import get_connection
import warnings
warnings.filterwarnings("ignore", message="use an explicit session with no_cursor_timeout=True")


def main():
    games = pd.read_csv("/Users/elisabethkollrack/Thesis/EK-thesis/games.csv")
    # Only regular season
    games = games[games['game_type'] == 'REG']
    games['gameday'] = pd.to_datetime(games['gameday'], format='%m/%d/%y')

    p = 1.0
    collection, client = get_connection(p=p)

    # 2013-2017
    all_games = games[(games['season'] >= 2013) & (games['season'] <= 2017)]

    zero_tweet_games = []

    # Loop through all games
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

        # Collect tweets
        tweets = []
        for anchor in anchors:
            tweets.extend([t for t in get_ambient_tweets(anchor, dates, collection)])

        # Check if there were no tweets
        if not tweets:
            zero_tweet_games.append({
                "away_team": away,
                "home_team": home,
                "kickoff": kickoff
            })

    # Print results
    if zero_tweet_games:
        print(f"\nFound {len(zero_tweet_games)} games with 0 tweets (2013–2017):")
        for game in zero_tweet_games:
            print(f"{game['away_team']} vs {game['home_team']} on {game['kickoff']}")
    else:
        print("✅ All games had at least some tweets!")

    return zero_tweet_games


if __name__ == '__main__':
    zero_tweet_games = main()
