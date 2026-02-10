from fastapi import FastAPI
import math
import requests
import os

# Get API key from environment variable
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.football-data.org/v4"
headers = {"X-Auth-Token": API_KEY}

app = FastAPI()
import os
from fastapi import FastAPI

app = FastAPI()

@app.get("/check-key")
def check_key():
    return {"API_KEY": os.getenv("API_KEY")}

from fastapi import FastAPI
import os, requests

app = FastAPI()

@app.get("/check-key")
def check_key():
    return {"API_KEY": os.getenv("API_KEY")}

@app.get("/matches")
def matches():
    api_key = os.getenv("API_KEY")
    headers = {"X-Auth-Token": api_key}
    # Ask for scheduled (upcoming) and live (present) matches
    url = "https://api.football-data.org/v4/competitions/PL/matches?status=SCHEDULED,LIVE"
    response = requests.get(url, headers=headers)
    return {"competition": "PL", "results": response.json().get("matches", [])}

def poisson_probability(lmbda, k):
    return (lmbda**k * math.exp(-lmbda)) / math.factorial(k)

def match_probability_under_45(home_avg_goals, away_avg_goals):
    max_goals = 10
    prob_under_45 = 0.0
    for home_goals in range(max_goals + 1):
        for away_goals in range(max_goals + 1):
            total_goals = home_goals + away_goals
            prob_home = poisson_probability(home_avg_goals, home_goals)
            prob_away = poisson_probability(away_avg_goals, away_goals)
            prob_match = prob_home * prob_away
            if total_goals <= 4:
                prob_under_45 += prob_match
    return prob_under_45

def get_team_stats(team_id, num_matches=10):
    url = f"{BASE_URL}/teams/{team_id}/matches?status=FINISHED&limit={num_matches}"
    response = requests.get(url, headers=headers).json()
    matches = response.get("matches", [])
    goals_scored, goals_conceded = 0, 0
    
    for match in matches:
        if match["homeTeam"]["id"] == team_id:
            goals_scored += match["score"]["fullTime"]["home"]
            goals_conceded += match["score"]["fullTime"]["away"]
        else:
            goals_scored += match["score"]["fullTime"]["away"]
            goals_conceded += match["score"]["fullTime"]["home"]
    
    avg_scored = goals_scored / len(matches) if matches else 1.0
    avg_conceded = goals_conceded / len(matches) if matches else 1.0
    return avg_scored, avg_conceded

@app.get("/matches")
def get_matches(competition: str = "PL"):
    url = f"{BASE_URL}/competitions/{competition}/matches?status=SCHEDULED"
    response = requests.get(url, headers=headers).json()
    matches = response.get("matches", [])
    results = []
    
    for match in matches:
        home_id = match["homeTeam"]["id"]
        away_id = match["awayTeam"]["id"]
        home_name = match["homeTeam"]["name"]
        away_name = match["awayTeam"]["name"]
        
        home_avg, home_conceded = get_team_stats(home_id)
        away_avg, away_conceded = get_team_stats(away_id)
        
        home_expected = (home_avg + away_conceded) / 2
        away_expected = (away_avg + home_conceded) / 2
        
        prob = match_probability_under_45(home_expected, away_expected)
        results.append({"match": f"{home_name} vs {away_name}", "probability": round(prob * 100, 2)})
    
    results.sort(key=lambda x: x["probability"], reverse=True)
    return {"competition": competition, "results": results}
