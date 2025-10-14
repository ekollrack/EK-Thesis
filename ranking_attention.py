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

    # Initialize storage for tweets per team
    teams_times = {}  # {team: {time_offset: total_tweets}}
    teams_games_count = {}  # {team: number_of_games}

    # 2013-2017
    all_games = games[(games['season'] >= 2013) & (games['season'] <= 2017)]

    # loop through all games
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

        # Collect tweets for both anchors
        tweets = []
        for anchor in anchors:
            tweets.extend([t for t in get_ambient_tweets(anchor, dates, collection)])

        if not tweets:
            continue

        tweets_df = pd.DataFrame(tweets)
        tweets_df['tweet_created_at'] = pd.to_datetime(tweets_df['tweet_created_at'])
        tweets_df['hour'] = tweets_df['tweet_created_at'].dt.floor('h')

        # Group by hour
        hourly_counts = tweets_df.groupby('hour').size().reset_index(name='count')
        hourly_dict = dict(zip(hourly_counts['hour'], hourly_counts['count']))

        # Initialize storage for teams if not exist
        for team in [away, home]:
            if team not in teams_times:
                teams_times[team] = {h: 0 for h in range(-5, 25)}
                teams_games_count[team] = 0

        # Align tweet counts relative to kickoff
        for time in range(-5, 25):
            time_point = kickoff + timedelta(hours=time)
            count = hourly_dict.get(time_point.floor('h'), 0)
            teams_times[away][time] += count
            teams_times[home][time] += count

        # Increment game count
        teams_games_count[away] += 1
        teams_games_count[home] += 1

        print(f"Processed game: {away} vs {home} ({kickoff})")

    # Compute average tweets per hour per team
    avg_tweets_per_team = {}
    for team in teams_times:
        avg_tweets_per_team[team] = {time: teams_times[team][time] / teams_games_count[team]
                                     for time in teams_times[team]}

    # Compute overall attention for sorting (sum over 5h-24h)
    team_total_attention = {}
    for team, counts in avg_tweets_per_team.items():
        team_total_attention[team] = sum(counts[time] for time in range(-5, 25))

    # Sort teams by total attention
    sorted_teams = sorted(team_total_attention.items(), key=lambda x: x[1], reverse=True)

    print("\n=== Teams Ranked by Average Attention (2013–2017) ===")
    for team, total in sorted_teams:
        print(f"{team:>10}: {total:.2f}")

    # Plot top 5 teams
    top_n = 5
    plt.figure(figsize=(14,6))
    for team, _ in sorted_teams[:top_n]:
        times = list(avg_tweets_per_team[team].keys())
        counts = list(avg_tweets_per_team[team].values())
        plt.plot(times, counts, marker='o', label=team)

    plt.axvline(0, color='red', linestyle='--', linewidth=1.5, label='Kickoff')
    plt.xticks(range(-5, 25), [f"{abs(t)}h before" if t<0 else ("Kickoff" if t==0 else f"{t}h after") for t in range(-5,25)], rotation=45)
    plt.xlabel("Hours Relative to Kickoff")
    plt.ylabel("Average Tweets per Hour")
    plt.title(f"Top {top_n} Teams by Attention (2013–2017)")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.show()

    return avg_tweets_per_team, sorted_teams


if __name__ == '__main__':
    avg_per_team, ranked_teams = main()
