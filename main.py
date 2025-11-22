from flask import Flask, render_template_string, jsonify, request
import requests, json, os
from datetime import datetime

# --- Configuration ---
API_KEY = "f84eee37c2c4ff4a3a3d83e0d5b3e972"
CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Cities with coordinates (Pakistan)
CITIES = [
    {"name":"Karachi","lat":24.8607,"lon":67.0011},
    {"name":"Lahore","lat":31.5204,"lon":74.3587},
    {"name":"Islamabad","lat":33.6844,"lon":73.0479},
    {"name":"Quetta","lat":30.1798,"lon":66.9750},
    {"name":"Peshawar","lat":34.0151,"lon":71.5249},
    {"name":"Multan","lat":30.1575,"lon":71.5249},
    {"name":"Faisalabad","lat":31.4180,"lon":73.0790},
    {"name":"Hyderabad","lat":25.3960,"lon":68.3578},
    {"name":"Rawalpindi","lat":33.5651,"lon":73.0169},
    {"name":"Sialkot","lat":32.4990,"lon":74.5229},
    {"name":"Gujranwala","lat":32.1877,"lon":74.1945}
]

app = Flask(__name__)

# --- Backend Function ---
def get_weather(city):
    if not city:
        return {"error": "City cannot be empty"}
    cache_file = f"{CACHE_DIR}/{city.lower()}.json"
    try:
        # Check cache (valid for 5 minutes)
        if os.path.exists(cache_file):
            ts = os.path.getmtime(cache_file)
            if datetime.now().timestamp() - ts < 300:
                with open(cache_file,"r") as f:
                    return json.load(f)

        # Fetch new data from OpenWeatherMap
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if "main" not in data:
            raise ValueError("Invalid city or API limit reached")
            
        result = {
            "Temp": data["main"]["temp"],
            "Humidity": data["main"]["humidity"],
            "Pressure": data["main"]["pressure"],
            "Wind": data["wind"]["speed"],
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save to cache
        with open(cache_file,"w") as f:
            json.dump(result,f)
            
        return result
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Network/API Error: {e}"}
    except Exception as e:
        return {"error": str(e)}

# --- Routes ---
@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Pakistan Weather Dashboard</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style>
body {
    font-family: 'Segoe UI', sans-serif; 
    padding:20px; 
    background:#121212; 
    color:#f5f5f5; 
    transition: background 0.5s, color 0.5s;
}
h1 {
    color:#f39c12; 
    text-align: center; 
    transition: color 0.5s;
}
#hackathon-banner {
    background: #e74c3c; 
    color: #ffffff; 
    padding: 12px; 
    margin: 15px 0 25px 0; 
    text-align: center; 
    font-size: 1.2em; 
    font-weight: bold;
    border-radius: 8px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.3);
}

input, select, button {
    padding:10px 14px; 
    margin:5px 5px 15px 0; 
    border-radius:8px; 
    border:1px solid #888; 
    font-size:16px; 
    transition: background 0.5s, color 0.5s, box-shadow 0.3s;
}
input {
    width:100%; 
    max-width:400px; 
    box-shadow: inset 0 3px 6px rgba(0,0,0,0.2);
}
button{
    cursor:pointer; 
    background:#f39c12; 
    color:#121212;
    border:none;
    box-shadow: 0 3px 6px rgba(0,0,0,0.3);
}
button:hover{
    transform: translateY(-2px);
    box-shadow: 0 5px 10px rgba(0,0,0,0.4);
}

#error-msg{ color:#e74c3c; font-weight:bold;}

#weather-chart,#pak-map{ 
    width:100%; 
    max-width:800px; 
    height:450px; 
    margin-top:20px;
    border-radius:8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
#update-time{margin-top:12px; font-weight:bold;}

.container{ display:flex; flex-wrap: wrap; gap:20px;}
.chart-box{ flex:1; min-width:350px;}

#mode-toggle { 
    position: absolute; top: 20px; right: 20px; 
    padding: 10px; background: #333; color: white; 
    border-radius: 5px; border: 1px solid #f39c12; 
}

/* Light Mode Styles */
body.light-mode { background:#ffffff; color:#333333; }
body.light-mode h1 { color:#d35400; }
body.light-mode #hackathon-banner { background: #c0392b; color: #ffffff; }
body.light-mode input, body.light-mode select { background:#eeeeee; color:#333333; }
body.light-mode button { background:#d35400; color:#ffffff; }
body.light-mode #mode-toggle { background: #f39c12; color: #121212; border: 1px solid #333; }
</style>
</head>
<body>
<h1>🌦️ Pakistan Weather Dashboard</h1>
<p id="hackathon-banner">Made for SMIT Hackathon</p>

<button id="mode-toggle" onclick="toggleMode()">Light Mode</button>

<input type="text" id="city" placeholder="Enter city" list="city-list" value="Karachi">
<datalist id="city-list">
{% for c in cities %}
<option value="{{c['name']}}">
{% endfor %}
</datalist>

<button onclick="updateWeather()">Update</button>

<br>
<label>Temp: </label>
<select id="temp-unit" onchange="updateWeather()">
    <option value="C">°C</option>
    <option value="F">°F</option>
</select>
<label>Wind: </label>
<select id="wind-unit" onchange="updateWeather()">
    <option value="ms">m/s</option>
    <option value="kmh">km/h</option>
</select>
<label>Pressure: </label>
<select id="pressure-unit" onchange="updateWeather()">
    <option value="hpa">hPa</option>
    <option value="atm">atm</option>
</select>

<p id="error-msg"></p>

<div class="container">
<div class="chart-box">
<div id="weather-chart"></div>
<p id="update-time"></p>
</div>
<div class="chart-box">
<div id="pak-map"></div>
</div>
</div>

<script>
const REFRESH = 10000;
let autoUpdate;
const CITIES = {{ cities|tojson }};
let lastWeatherData = null;

function getCityCoords(name){
    const c = CITIES.find(c=>c.name.toLowerCase()===name.toLowerCase());
    return c? {lat:c.lat, lon:c.lon}:null;
}

async function fetchWeather(city){
    const res = await fetch(`/api/weather?city=${city}`);
    return await res.json();
}

function getChartBgColor() {
    return document.body.classList.contains('light-mode') ? '#ffffff' : '#1e1e1e';
}

function updateChartTheme(city, tempUnit, pressureUnit, windUnit, temp, humidity, pressure, wind) {
    const bgColor = getChartBgColor();
    const fontColor = document.body.classList.contains('light-mode') ? '#333333' : '#f5f5f5';
    const gridColor = fontColor === '#f5f5f5' ? '#444' : '#ccc';

    const params=[`Temp (${tempUnit})`,"Humidity (%)",`Pressure (${pressureUnit})`,`Wind (${windUnit})`];
    const values=[temp,humidity,pressure,wind];
    const colors=['#e74c3c','#3498db','#2ecc71','#f1c40f'];
    
    Plotly.react('weather-chart',[{
        x: params, y: values, type:'bar', marker:{color:colors}, text:values.map(v=>v.toFixed(1)), textposition:'auto'
    }], {
        title:`Live Weather in ${city}`, 
        yaxis:{title:"Value", gridcolor: gridColor},
        plot_bgcolor: bgColor,
        paper_bgcolor: bgColor,
        font: { color: fontColor }
    });
    
    const coords = getCityCoords(city);
    const mapData = [];
    if(coords){
        mapData.push({
            type:'scattergeo',
            lon:[coords.lon],
            lat:[coords.lat],
            text:[city],
            mode:'markers+text',
            marker:{size:20,color:'red'},
            textposition:'top center'
        });
    }

    const layoutMap={
        geo:{scope:'asia', center:{lat:30, lon:70}, projection:{type:'mercator'}, showcountries:true, countrycolor:"black",
            lataxis:{range:[23,37]}, lonaxis:{range:[60,77]}, visible:false},
        title:"Selected City in Pakistan",
        height:450,
        dragmode:false,
        plot_bgcolor: bgColor,
        paper_bgcolor: bgColor,
        font: { color: fontColor }
    };
    Plotly.react('pak-map',mapData,layoutMap);
}

async function updateWeather(isToggle=false){
    const city = document.getElementById("city").value.trim();
    const errorEl = document.getElementById("error-msg");
    errorEl.innerText = "";
    
    let data;
    if(!isToggle || lastWeatherData === null){ 
        if(!city){ errorEl.innerText="Please enter a city"; return; }
        data = await fetchWeather(city);
        if(data.error){ errorEl.innerText=data.error; return; }
        lastWeatherData = data;
    } else {
        data = lastWeatherData;
    }

    let temp=data.Temp, wind=data.Wind, pressure=data.Pressure;
    const tempUnit=document.getElementById("temp-unit").value;
    const windUnit=document.getElementById("wind-unit").value;
    const pressureUnit=document.getElementById("pressure-unit").value;
    
    if(tempUnit==="F") temp=temp*9/5+32;
    if(windUnit==="kmh") wind=wind*3.6;
    if(pressureUnit==="atm") pressure=pressure/1013.25;

    updateChartTheme(city, tempUnit, pressureUnit, windUnit, temp, data.Humidity, pressure, wind);

    document.getElementById("update-time").innerText=`Last updated: ${data.Time}`;
}

function toggleMode(){
    document.body.classList.toggle('light-mode');
    document.getElementById("mode-toggle").innerText = document.body.classList.contains('light-mode') ? "Dark Mode" : "Light Mode";
    updateWeather(true);
}

updateWeather();
clearInterval(autoUpdate);
autoUpdate=setInterval(updateWeather, REFRESH);
</script>
</body>
</html>
""", cities=CITIES)

@app.route('/api/weather')
def weather_api():
    city=request.args.get("city","").strip()
    data=get_weather(city)
    return jsonify(data)

if __name__=="__main__":
    app.run(debug=True)
