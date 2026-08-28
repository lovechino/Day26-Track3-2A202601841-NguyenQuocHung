from typing import Any
import asyncio
import json
import httpx
import os
from datetime import datetime, timezone
from mcp.server.fastmcp import FastMCP
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings

# Initialize FastMCP server
port = int(os.getenv("PORT", 8085))

# --- Authentication Setup ---
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "dev-token-abc123")

class WeatherTokenVerifier(TokenVerifier):
    """Verify bearer token for MCP server access."""
    
    async def verify_token(self, token: str) -> AccessToken | None:
        if token == MCP_AUTH_TOKEN:
            return AccessToken(
                token=token,
                client_id="weather-client",
                scopes=["weather:read", "weather:forecast"]
            )
        return None

auth_settings = AuthSettings(
    issuer_url=f"http://localhost:{port}",
    resource_server_url=f"http://localhost:{port}",
)

mcp = FastMCP(
    "weather",
    host="0.0.0.0",
    port=port,
    auth=auth_settings,
    token_verifier=WeatherTokenVerifier(),
)

# Constants
WEATHERAPI_BASE = "https://api.weatherapi.com/v1"
USER_AGENT = "weather-app/1.0"
API_KEY = os.getenv("WEATHERAPI_KEY")
SERVER_VERSION = "2.0.0"

async def make_weather_request(endpoint: str, params: dict[str, str]) -> dict[str, Any] | None:
    """Make a request to the WeatherAPI with proper error handling."""
    if not API_KEY:
        print("ERROR: WeatherAPI key not set. Please set WEATHERAPI_KEY environment variable.")
        return None
        
    headers = {"User-Agent": USER_AGENT}
    params["key"] = API_KEY
    url = f"{WEATHERAPI_BASE}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error {e.response.status_code}: {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"Request Error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

def format_current_weather(data: dict, include_forecast: bool = False, units: str = "celsius") -> str:
    """Format current weather data for v1 (string) or v2 (JSON)."""
    current = data["current"]
    location = data["location"]
    
    temp_c = current['temp_c']
    temp_f = current['temp_f']
    
    if units == "fahrenheit":
        temp_display = f"{temp_f}°F ({temp_c}°C)"
    else:
        temp_display = f"{temp_c}°C ({temp_f}°F)"
    
    feelslike_c = current['feelslike_c']
    feelslike_f = current['feelslike_f']
    if units == "fahrenheit":
        feelslike_display = f"{feelslike_f}°F ({feelslike_c}°C)"
    else:
        feelslike_display = f"{feelslike_c}°C ({feelslike_f}°F)"
    
    if include_forecast:
        # v2 JSON format
        result = {
            "api_version": "2.0",
            "city": location['name'],
            "region": location['region'],
            "country": location['country'],
            "temperature": temp_display,
            "feels_like": feelslike_display,
            "condition": current['condition']['text'],
            "humidity": f"{current['humidity']}%",
            "wind": f"{current['wind_kph']} km/h ({current['wind_mph']} mph) {current['wind_dir']}",
            "pressure": f"{current['pressure_mb']} mb",
            "uv_index": current['uv'],
            "visibility": f"{current['vis_km']} km",
            "last_updated": current['last_updated'],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if "forecast" in data:
            result["forecast"] = data["forecast"]["forecastday"]
        return json.dumps(result, ensure_ascii=False, indent=2)
    else:
        # v1 string format
        return f"""
Current Weather for {location['name']}, {location['region']}, {location['country']}:

Temperature: {temp_display}
Feels like: {feelslike_display}
Condition: {current['condition']['text']}
Humidity: {current['humidity']}%
Wind: {current['wind_kph']} km/h ({current['wind_mph']} mph) {current['wind_dir']}
Pressure: {current['pressure_mb']} mb
UV Index: {current['uv']}
Visibility: {current['vis_km']} km

Last updated: {current['last_updated']}
"""

# ============================================================
# TOOL v1 — Backward compatible (deprecated but functional)
# ============================================================
@mcp.tool()
async def get_current_weather(city: str) -> str:
    """[v1] Get current weather conditions for a city. Returns formatted string.
    
    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney")
    
    Deprecated: Use get_current_weather_v2 for JSON output with more options.
    """
    params = {"q": city, "aqi": "no"}
    data = await make_weather_request("current.json", params)

    if not data:
        if not API_KEY:
            return "❌ WeatherAPI key not configured. Please set WEATHERAPI_KEY environment variable with your API key from weatherapi.com"
        return f"Unable to fetch current weather data for {city}. Please check the city name and API key configuration."

    return format_current_weather(data)


# ============================================================
# TOOL v2 — Enhanced with JSON output, optional params
# ============================================================
@mcp.tool()
async def get_current_weather_v2(
    city: str,
    include_forecast: bool = False,
    units: str = "celsius",
) -> str:
    """[v2] Get current weather conditions for a city. Returns structured JSON.
    
    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney")
        include_forecast: Include forecast data in response (default: false)
        units: Temperature units - "celsius" or "fahrenheit" (default: "celsius")
    """
    params = {"q": city, "aqi": "no"}
    data = await make_weather_request("current.json", params)

    if not data:
        if not API_KEY:
            return json.dumps({
                "error": "WeatherAPI key not configured",
                "api_version": "2.0"
            }, ensure_ascii=False)
        return json.dumps({
            "error": f"Unable to fetch current weather data for {city}",
            "api_version": "2.0"
        }, ensure_ascii=False)

    return format_current_weather(data, include_forecast=include_forecast, units=units)


@mcp.tool()
async def get_forecast(city: str, days: int = 3) -> str:
    """[v1] Get weather forecast for a city. Returns formatted string.
    
    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney", "Melbourne")
        days: Number of days to forecast (1-3 for free tier, max 10 for paid)
    
    Deprecated: Use get_forecast_v2 for JSON output with more options.
    """
    days = min(days, 10)
    params = {"q": city, "days": str(days), "aqi": "no", "alerts": "no"}
    data = await make_weather_request("forecast.json", params)

    if not data:
        if not API_KEY:
            return "❌ WeatherAPI key not configured. Please set WEATHERAPI_KEY environment variable with your API key from weatherapi.com"
        return f"Unable to fetch forecast data for {city}. Please check the city name and API key configuration."

    location = data["location"]
    forecast_days = data["forecast"]["forecastday"]
    
    forecasts = []
    forecasts.append(f"Weather Forecast for {location['name']}, {location['region']}, {location['country']}:")
    
    for day in forecast_days:
        day_data = day["day"]
        date = day["date"]
        forecast = f"""
{date}:
High: {day_data['maxtemp_c']}°C ({day_data['maxtemp_f']}°F)
Low: {day_data['mintemp_c']}°C ({day_data['mintemp_f']}°F)
Condition: {day_data['condition']['text']}
Chance of Rain: {day_data['daily_chance_of_rain']}%
Max Wind: {day_data['maxwind_kph']} km/h
UV Index: {day_data['uv']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)


@mcp.tool()
async def get_forecast_v2(
    city: str,
    days: int = 3,
    units: str = "celsius",
) -> str:
    """[v2] Get weather forecast for a city. Returns structured JSON.
    
    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney", "Melbourne")
        days: Number of days to forecast (1-3 for free tier, max 10 for paid)
        units: Temperature units - "celsius" or "fahrenheit" (default: "celsius")
    """
    days = min(days, 10)
    params = {"q": city, "days": str(days), "aqi": "no", "alerts": "no"}
    data = await make_weather_request("forecast.json", params)

    if not data:
        if not API_KEY:
            return json.dumps({
                "error": "WeatherAPI key not configured",
                "api_version": "2.0"
            }, ensure_ascii=False)
        return json.dumps({
            "error": f"Unable to fetch forecast data for {city}",
            "api_version": "2.0"
        }, ensure_ascii=False)

    location = data["location"]
    forecast_days = data["forecast"]["forecastday"]
    
    forecasts = []
    for day in forecast_days:
        day_data = day["day"]
        date = day["day"]
        forecast = {
            "date": day["date"],
            "high_temp": f"{day_data['maxtemp_c']}°C ({day_data['maxtemp_f']}°F)" if units == "celsius" else f"{day_data['maxtemp_f']}°F ({day_data['maxtemp_c']}°C)",
            "low_temp": f"{day_data['mintemp_c']}°C ({day_data['mintemp_f']}°F)" if units == "celsius" else f"{day_data['mintemp_f']}°F ({day_data['mintemp_c']}°C)",
            "condition": day_data['condition']['text'],
            "chance_of_rain": f"{day_data['daily_chance_of_rain']}%",
            "max_wind": f"{day_data['maxwind_kph']} km/h",
            "uv_index": day_data['uv'],
        }
        forecasts.append(forecast)

    return json.dumps({
        "api_version": "2.0",
        "city": location['name'],
        "region": location['region'],
        "country": location['country'],
        "forecast_days": forecasts,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def health_check() -> str:
    """Health check endpoint for deployment verification."""
    return "✅ Weather MCP Server is running! Ready to provide weather data."


# ============================================================
# RESOURCE: Server metadata for versioning/discovery
# ============================================================
@mcp.resource("server://info")
def server_info() -> str:
    """Server metadata — version, tools, deprecation notices, migration guide."""
    return json.dumps({
        "name": "weather",
        "version": SERVER_VERSION,
        "description": "Weather MCP Server providing current weather and forecasts via WeatherAPI.com",
        "transport": "streamable-http",
        "authentication": "Bearer token (MCP_AUTH_TOKEN env var)",
        "tools": {
            "get_current_weather": {
                "version": "1.0",
                "status": "deprecated",
                "description": "Get current weather - returns formatted string",
                "replacement": "get_current_weather_v2"
            },
            "get_current_weather_v2": {
                "version": "2.0",
                "status": "current",
                "description": "Get current weather - returns JSON with optional forecast and units",
                "parameters": {
                    "city": {"type": "string", "required": True},
                    "include_forecast": {"type": "boolean", "default": False},
                    "units": {"type": "string", "enum": ["celsius", "fahrenheit"], "default": "celsius"}
                }
            },
            "get_forecast": {
                "version": "1.0",
                "status": "deprecated",
                "description": "Get weather forecast - returns formatted string",
                "replacement": "get_forecast_v2"
            },
            "get_forecast_v2": {
                "version": "2.0",
                "status": "current",
                "description": "Get weather forecast - returns JSON with units option",
                "parameters": {
                    "city": {"type": "string", "required": True},
                    "days": {"type": "integer", "default": 3, "minimum": 1, "maximum": 10},
                    "units": {"type": "string", "enum": ["celsius", "fahrenheit"], "default": "celsius"}
                }
            },
            "health_check": {
                "version": "1.0",
                "status": "current",
                "description": "Health check endpoint"
            }
        },
        "deprecated_tools": ["get_current_weather", "get_forecast"],
        "migration_guide": "Migrate from v1 tools to v2 tools: get_current_weather -> get_current_weather_v2, get_forecast -> get_forecast_v2. v2 tools return JSON with optional parameters (include_forecast, units). v1 tools remain functional for backward compatibility.",
        "authentication": {
            "type": "bearer",
            "header": "Authorization: Bearer <MCP_AUTH_TOKEN>",
            "scopes": ["weather:read", "weather:forecast"]
        }
    }, ensure_ascii=False, indent=2)


print("✅ MCP server initialized with Streamable HTTP transport")
print("🔧 Available tools:")
print("   - get_current_weather (v1, deprecated)")
print("   - get_current_weather_v2 (v2, JSON, optional forecast/units)")
print("   - get_forecast (v1, deprecated)")
print("   - get_forecast_v2 (v2, JSON, optional units)")
print("   - health_check")
print("📋 Server metadata: server://info")

if __name__ == "__main__":
    import sys
    
    is_cloud_run = bool(os.getenv("PORT"))
    is_standalone = len(sys.argv) == 1 and sys.stdin.isatty()
    
    if is_cloud_run or is_standalone:
        print(f"🚀 Starting MCP server on http://0.0.0.0:{port}/mcp")
        mcp.run(transport="streamable-http")
    else:
        print("Starting FastMCP server in stdio mode for local client", file=sys.stderr)
        mcp.run()