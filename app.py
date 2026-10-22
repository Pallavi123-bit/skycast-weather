
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    80: "Rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail"
}

ICONS = {
    "Clear": "☀️",
    "Mainly clear": "🌤️",
    "Partly cloudy": "⛅",
    "Overcast": "☁️",
    "Foggy": "🌫️",
    "drizzle": "🌦️",
    "rain": "🌧️",
    "Rain": "🌧️",
    "snow": "❄️",
    "Snow": "❄️",
    "Thunderstorm": "⛈️"
}


def get_icon(description):
    for key, icon in ICONS.items():
        if key.lower() in description.lower():
            return icon
    return "🌡️"


PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Check current weather conditions around the world with SkyCast.">
<title>SkyCast | Weather Forecast</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{
  font-family:Arial,sans-serif;
  min-height:100vh;
  color:#fff;
  background:linear-gradient(135deg,#10213d,#234b70,#387e98);
  padding:24px;
}
.container{max-width:900px;margin:auto}
header{
  display:flex;justify-content:space-between;align-items:center;
  padding:12px 0 30px;gap:15px
}
.logo{font-size:27px;font-weight:800}
.logo span{color:#ffd36e}
header p{font-size:13px;color:#d4e3f2}
.hero{text-align:center;margin:20px 0 28px}
.hero h1{font-size:clamp(32px,6vw,48px);margin-bottom:10px}
.hero h1 span{color:#ffd36e}
.hero p{color:#d5e4f2;line-height:1.6}
.search{
  display:flex;gap:10px;max-width:570px;margin:25px auto 10px
}
input{
  min-width:0;flex:1;padding:15px 18px;border:0;
  border-radius:12px;font-size:16px;outline:2px solid transparent
}
input:focus{outline-color:#ffd36e}
button{
  border:0;border-radius:12px;padding:14px 20px;
  font-weight:bold;cursor:pointer;background:#ffd36e;color:#24354b
}
button:hover{background:#ffe49c}
button:disabled{opacity:.6;cursor:wait}
.status{text-align:center;min-height:28px;color:#ffdf9b;font-size:14px}
.weather{
  display:none;background:#ffffff12;
  border:1px solid #ffffff2b;border-radius:24px;
  padding:28px;backdrop-filter:blur(10px);
  box-shadow:0 15px 50px #07182a33
}
.location{font-size:23px;font-weight:bold}
.local-time{font-size:13px;color:#d4e3f2;margin-top:5px}
.current{
  display:flex;align-items:center;justify-content:space-between;
  gap:15px;padding:25px 0
}
.temperature{font-size:clamp(54px,10vw,82px);font-weight:800;letter-spacing:-3px}
.condition{font-size:18px;color:#e1eaf4}
.weather-icon{font-size:75px}
.details{
  display:grid;grid-template-columns:repeat(3,1fr);gap:14px
}
.detail{
  padding:19px 15px;background:#ffffff12;
  border:1px solid #ffffff20;border-radius:15px
}
.detail .symbol{font-size:24px}
.detail p{font-size:13px;color:#d3e1ef;margin:9px 0}
.detail strong{font-size:20px}
footer{text-align:center;color:#d2e0ed;font-size:12px;padding:30px 0 5px}
@media(max-width:550px){
  body{padding:16px}
  header{padding-bottom:20px}
  header p{display:none}
  .search{flex-direction:column}
  .weather{padding:20px}
  .current{padding:20px 0}
  .weather-icon{font-size:55px}
  .details{grid-template-columns:1fr 1fr}
  .detail{padding:14px 11px}
}
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="logo">☁ Sky<span>Cast</span></div>
    <p>YOUR WEATHER, AT A GLANCE</p>
  </header>

  <section class="hero">
    <h1>Weather made <span>simple.</span></h1>
    <p>Discover current weather conditions for any city around the world.</p>
    <form class="search" id="weatherForm">
      <input id="city" type="text" placeholder="Enter city name (e.g. Pune)"
        aria-label="City name" required maxlength="100">
      <button id="searchButton" type="submit">Search Weather</button>
    </form>
  </section>

  <p class="status" id="status" role="status" aria-live="polite">
    Search for a city to see its weather.
  </p>

  <section class="weather" id="weather">
    <div class="location" id="location"></div>
    <div class="local-time" id="localTime"></div>

    <div class="current">
      <div>
        <div class="temperature"><span id="temperature">--</span>°C</div>
        <div class="condition" id="condition"></div>
      </div>
      <div class="weather-icon" id="weatherIcon">🌤️</div>
    </div>

    <div class="details">
      <div class="detail">
        <div class="symbol">🌡️</div>
        <p>Feels Like</p>
        <strong id="feelsLike">--</strong>
      </div>
      <div class="detail">
        <div class="symbol">💧</div>
        <p>Humidity</p>
        <strong id="humidity">--</strong>
      </div>
      <div class="detail">
        <div class="symbol">💨</div>
        <p>Wind Speed</p>
        <strong id="wind">--</strong>
      </div>
      <div class="detail">
        <div class="symbol">🌧️</div>
        <p>Precipitation</p>
        <strong id="rain">--</strong>
      </div>
      <div class="detail">
        <div class="symbol">☀️</div>
        <p>Daylight</p>
        <strong id="daylight">--</strong>
      </div>
      <div class="detail">
        <div class="symbol">🕒</div>
        <p>Local Time</p>
        <strong id="clock">--</strong>
      </div>
    </div>
  </section>

  <footer>
    <p>© 2026 SkyCast Weather · Weather data by Open-Meteo</p>
    <p style="margin-top:7px">Built with Python, Flask, HTML, CSS and JavaScript.</p>
  </footer>
</div>

<script>
const form = document.getElementById("weatherForm");
const button = document.getElementById("searchButton");
const statusText = document.getElementById("status");
const weatherPanel = document.getElementById("weather");

function show(id, value) {
  document.getElementById(id).textContent = value;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const city = document.getElementById("city").value.trim();
  if (!city) return;

  button.disabled = true;
  button.textContent = "Loading...";
  statusText.textContent = "Getting the latest weather...";
  weatherPanel.style.display = "none";

  try {
    const response = await fetch(
      "/api/weather?city=" + encodeURIComponent(city)
    );
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Unable to get weather.");
    }

    show("location", data.city + ", " + data.country);
    show("localTime", "Local time: " + data.local_time);
    show("temperature", data.temperature);
    show("condition", data.description);
    show("weatherIcon", data.icon);
    show("feelsLike", data.feels_like + "°C");
    show("humidity", data.humidity + "%");
    show("wind", data.wind_speed + " km/h");
    show("rain", data.precipitation + " mm");
    show("daylight", data.is_day ? "Daytime" : "Nighttime");
    show("clock", data.local_time.split(" ")[1] || data.local_time);

    weatherPanel.style.display = "block";
    statusText.textContent = "Weather updated successfully.";
  } catch (error) {
    statusText.textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = "Search Weather";
  }
});
</script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(PAGE)


@app.route("/api/weather")
def weather():
    city = request.args.get("city", "").strip()

    if not city or len(city) > 100:
        return jsonify({"error": "Please enter a valid city name."}), 400

    try:
        geo_response = requests.get(
            GEOCODING_URL,
            params={
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json"
            },
            timeout=10
        )
        geo_response.raise_for_status()
        locations = geo_response.json().get("results", [])

        if not locations:
            return jsonify({
                "error": "City not found. Check the spelling and try again."
            }), 404

        place = locations[0]

        weather_response = requests.get(
            WEATHER_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": (
                    "temperature_2m,relative_humidity_2m,"
                    "apparent_temperature,is_day,precipitation,"
                    "weather_code,wind_speed_10m"
                ),
                "timezone": "auto"
            },
            timeout=10
        )
        weather_response.raise_for_status()

        current = weather_response.json()["current"]
        code = current["weather_code"]
        description = WEATHER_CODES.get(code, "Weather conditions unavailable")

        return jsonify({
            "city": place["name"],
            "country": place.get("country", ""),
            "temperature": current["temperature_2m"],
            "feels_like": current["apparent_temperature"],
            "humidity": current["relative_humidity_2m"],
            "wind_speed": current["wind_speed_10m"],
            "precipitation": current["precipitation"],
            "description": description,
            "icon": get_icon(description),
            "is_day": bool(current["is_day"]),
            "local_time": current["time"].replace("T", " ")
        })

    except requests.RequestException:
        return jsonify({
            "error": "Weather service unavailable. Please try again."
        }), 502
    except (KeyError, ValueError, TypeError):
        return jsonify({
            "error": "Unexpected weather data. Please try again."
        }), 502


if __name__ == "__main__":
    app.run(debug=True)
