import pandas as pd
from datetime import timedelta
from data_mountain_query.query import get_ambient_tweets
from data_mountain_query.connection import get_connection

games = pd.read_csv("/Users/elisabethkollrack/Thesis/EK-thesis/games.csv")
games = games[games['game_type'] == 'REG']
games['gameday'] = pd.to_datetime(games['gameday'], format='%m/%d/%y')

# --- Dallas 2013-2017 regular seasons only ---
dallas_games = games[
    (games['season'] >= 2013) &
    (games['season'] <= 2017) &
    ((games['home_team'] == 'DAL') | (games['away_team'] == 'DAL'))
].sort_values(['season', 'gameday'])

print(f"Found {len(dallas_games)} Dallas Cowboys games from 2013-2017")

collection, client = get_connection(user_loc=True)
all_tweets = []

# Process ALL Dallas games
for index, game in dallas_games.iterrows():
    gameday = game['gameday']
    
    # Determine opponent
    if game['home_team'] == 'DAL':
        opponent = game['away_team']
    else:
        opponent = game['home_team']

    anchors = [
        "#DallasCowboys", 
        "#CowboysNation",
        f"#DALvs{opponent}",
        f"#{opponent}vsDAL"
    ]
    
    print(f"Processing {game['season']}: DAL vs {opponent} on {gameday.date()}")

    start_date = gameday - timedelta(days=3)
    end_date = gameday + timedelta(days=3)
    dates = pd.date_range(start_date, end_date, freq='D')

    for anchor in anchors:
        tweets_list = [t for t in get_ambient_tweets(anchor, dates, collection)]
        all_tweets.extend(tweets_list)
        print(f"  Found {len(tweets_list)} tweets for {anchor}")

# Analyze combined city data for all games
tweets_df = pd.DataFrame(all_tweets)

if "city_state" in tweets_df.columns:
    city_counts = (
        tweets_df["city_state"]
        .dropna()
        .astype(str)
        .str.strip()
        .value_counts()
        .reset_index()
        .rename(columns={"index": "city_state", "city_state": "count"})
    )

print(f"\nTotal tweets collected: {len(all_tweets)}")
print(f"Total unique cities: {len(city_counts)}")
print("\nTop 10 cities:")
print(city_counts.head(10).to_string(index=False))