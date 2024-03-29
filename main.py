import os
import requests
import base64
import asyncio
from datetime import datetime
from typing import Annotated
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="templates")

@app.get("/api/weather_recommendations", response_class=HTMLResponse)
async def get_weather_recommendations(request: Request, latitude: str, longitude: str, genres: str, access_token: Annotated[str | None, Header()] = None):
    if not access_token: return

    weather_data, suntime_data = await (asyncio.gather(fetch_weather(latitude, longitude),fetch_suntime(latitude, longitude)))

    feelslike_c, precip_mm = extract_weather(weather_data)
    suntime_hours = extract_suntime(suntime_data)
    
    valence, energy = calculate_recommendation_parameters(feelslike_c, precip_mm, suntime_hours)
    recommendations_data = await fetch_recommendations(access_token, valence, energy, genres)
    tracks_info = extract_recommendations(recommendations_data)
    
    weather_info = {
        'feelslike_c': round(feelslike_c, 2),
        'precip_mm': round(precip_mm, 2),
        'suntime_hours': round(suntime_hours, 2)
    }
    recommendation_info = {
        'valence': round(valence, 2),
        'energy': round(energy, 2)
    }

    return templates.TemplateResponse(request=request, name="weather_recommendations.html", context={"weather_info": weather_info,"recommendation_info": recommendation_info,"tracks_info": tracks_info})

@app.get("/api/recommendations")
async def fetch_recommendations(access_token: str, target_valence: float, target_energy: float, seed_genres: str):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    # TODO: implement more parameters (genres, check market, artists, etc.)
    payload = {
        "market": "PL",
        "seed_genres": seed_genres.split(","),
        "target_valence": target_valence,
        "target_energy": target_energy

    }
    response = requests.get("https://api.spotify.com/v1/recommendations", headers=headers, params=payload)
    return response.json()
def extract_recommendations(data):
    tracks_info = []
    for track in data["tracks"]:
        artists_names = [artist["name"] for artist in track["album"]["artists"]]
        first_image = track["album"]["images"][0]["url"]
        track_name = track["name"]
        spotify_external_url = track["external_urls"]["spotify"]
        
        tracks_info.append({
            "artists_names": artists_names,
            "first_image": first_image,
            "track_name": track_name,
            "spotify_external_url": spotify_external_url
        })
    return tracks_info

weather_api_url = lambda api_method, latitude, longitude: f"http://api.weatherapi.com/v1/{api_method}?key=e67c5fd1d3fc4375b1e210330241603 &q={latitude},{longitude}&aqi=no"

@app.get("/api/weather")
async def fetch_weather(latitude, longitude):
    response = requests.get(weather_api_url("current.json", latitude, longitude))
    return response.json()
def extract_weather(data):
    feelslike_c = data["current"]["feelslike_c"]
    precip_mm = data["current"]["precip_mm"]
    return feelslike_c, precip_mm

@app.get("/api/suntime")
async def fetch_suntime(latitude, longitude):
    response = requests.get(weather_api_url("astronomy.json", latitude, longitude))
    return response.json()
def extract_suntime(data):
    sunrise_str = data["astronomy"]["astro"]["sunrise"]
    sunset_str = data["astronomy"]["astro"]["sunset"]
    sunrise_time = datetime.strptime(sunrise_str, "%I:%M %p")
    sunset_time = datetime.strptime(sunset_str, "%I:%M %p")
    
    time_difference = sunset_time - sunrise_time
    hours_difference = time_difference.total_seconds() / 3600
    return hours_difference

def calculate_recommendation_parameters(feelslike_c: float, precip_mm: float, suntime_hours: float):
    suntime_standardized = suntime_hours / 16.5 # range 0h-16.5h
    feelslike_standardized = ( feelslike_c + 17.8 ) / 46.2 # range (-17.8C)-(28.4C)
    precip_standardized = precip_mm / 47.10 # range 0mm-47.10mm
    
    suntime_weight = 2
    feelslike_weight = 3
    precip_weight = 4

    # NOTE: suntime-energy is kinda scientifically based, rest is totally arbitrary lol
    valence = ( suntime_weight * suntime_standardized + feelslike_weight * feelslike_standardized + precip_weight * precip_standardized ) / (suntime_weight + feelslike_weight + precip_weight)
    energy = suntime_standardized
    return valence, energy

@app.get("/api/spotify-auth")
async def authorize_spotify():
    auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}" 
    base64_auth_string = base64.b64encode(auth_string.encode()).decode()
    response = requests.post("https://accounts.spotify.com/api/token", headers={
        "Authorization": f"Basic {base64_auth_string}"
    }, data={
        "grant_type": "client_credentials"
    })
    return response.json()

@app.get("/callback")
async def callback(request: Request):
    # Extracting query parameters
    params = request.query_params
    
    # Constructing new URL without /callback
    new_path = "/"
    new_url = f"{request.url.scheme}://{request.url.netloc}{new_path}"
    
    if params:
        new_url += "?" + params.__str__()
    
    return RedirectResponse(url=new_url)
app.mount(path="/", app=StaticFiles(directory="static", html=True), name="static")
