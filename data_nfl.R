library(nflreadr)
library(dplyr)

# Seasons to process
seasons <- 2013:2017

# -------------------------------
# 1. Load play-by-play for all seasons and calculate lead changes
# -------------------------------
pbp_all <- load_pbp(seasons = seasons)

lead_changes_all <- pbp_all %>%
  filter(!is.na(posteam)) %>%  # plays with a possessing team
  mutate(
    score_diff = total_home_score - total_away_score,
    leader = case_when(
      score_diff > 0 ~ home_team,
      score_diff < 0 ~ away_team,
      TRUE ~ "TIE"
    )
  ) %>%
  filter(leader != "TIE") %>%  # ignore ties
  group_by(game_id) %>%
  arrange(game_id, play_id) %>%
  mutate(
    lead_change = if_else(leader != lag(leader), 1, 0)
  ) %>%
  summarise(lead_changes = sum(lead_change, na.rm = TRUE))

# -------------------------------
# 2. Initialize dataframe for all seasons
# -------------------------------
win_pct_all <- data.frame()

for (season_year in seasons) {
  
  # Load season schedule
  games <- load_schedules(seasons = season_year)
  
  # Keep only regular season games and relevant columns
  games <- games %>%
    filter(game_type == "REG") %>%
    select(game_id, week, gameday, home_team, away_team, home_score, away_score) %>%
    arrange(gameday)
  
  # Initialize cumulative stats for teams in this season
  team_stats <- data.frame(
    team = unique(c(games$home_team, games$away_team)),
    wins = 0,
    games = 0
  )
  
  # Create a result dataframe for this season
  win_pct_data <- data.frame()
  
  # Loop over each game
  for (i in 1:nrow(games)) {
    
    game <- games[i, ]
    
    home <- game$home_team
    away <- game$away_team
    home_score <- game$home_score
    away_score <- game$away_score
    
    # Calculate win/tie outcome
    if (home_score > away_score) {
      home_win <- 1
      away_win <- 0
    } else if (home_score < away_score) {
      home_win <- 0
      away_win <- 1
    } else {
      home_win <- 0.5
      away_win <- 0.5
    }
    
    # Get cumulative stats before this game
    home_stats <- team_stats[team_stats$team == home, ]
    away_stats <- team_stats[team_stats$team == away, ]
    
    home_win_pct <- ifelse(home_stats$games == 0, 0, home_stats$wins / home_stats$games)
    away_win_pct <- ifelse(away_stats$games == 0, 0, away_stats$wins / away_stats$games)
    
    # ✅ Add lead changes for this game
    lead_changes <- lead_changes_all$lead_changes[lead_changes_all$game_id == game$game_id]
    lead_changes <- ifelse(length(lead_changes) == 0, 0, lead_changes)  # default to 0 if missing
    
    # Add row to season result
    win_pct_data <- rbind(win_pct_data, data.frame(
      season = season_year,
      game_id = game$game_id,
      gameday = game$gameday,
      home_team = home,
      away_team = away,
      home_win_pct = home_win_pct,
      away_win_pct = away_win_pct,
      lead_changes = lead_changes
    ))
    
    # Update cumulative team stats
    team_stats$wins[team_stats$team == home] <- home_stats$wins + home_win
    team_stats$games[team_stats$team == home] <- home_stats$games + 1
    team_stats$wins[team_stats$team == away] <- away_stats$wins + away_win
    team_stats$games[team_stats$team == away] <- away_stats$games + 1
  }
  
  # Add this season's data to the all-seasons dataframe
  win_pct_all <- rbind(win_pct_all, win_pct_data)
}

# -------------------------------
# 3. Save and preview
# -------------------------------
write.csv(win_pct_all, "nfl_win_pct_2013_2017_with_lead_changes.csv", row.names = FALSE)
head(win_pct_all)
