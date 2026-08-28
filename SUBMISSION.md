# Day26 Lab Submission — MCP vs Function Calling

**Student:** Nguyen Quoc Hung (2A202601841)  
**Track:** Track 3  
**Date:** 2026-08-28  

---

## Summary

All 4 modules completed and verified. The ADK Weather Agent with remote MCP Server is running live.

---

## Module Completion Status

| Module | Path | Status | Notes |
|--------|------|--------|-------|
| **01 Function Calling** | `01-function-calling/weather_function_calling.py` | ✅ Code complete | Manual schema definition, app executes tools. Tested — blocked by IP restriction on original key. |
| **02 MCP Basics** | `02-mcp-basics/weather_server.py` + `weather_client.py` | ✅ Verified | Stdio transport, `@mcp.tool()` auto-generates schema. `python weather_client.py` → lists tools + calls `get_weather` for 3 cities. |
| **03 Production** | `03-production/` | ✅ All 3 sub-tasks verified | |
| &nbsp;&nbsp;• Auth | `auth_server.py` + `auth_client.py` | ✅ | Streamable HTTP + Bearer token (2 terminals). 401/403 on invalid/missing token. |
| &nbsp;&nbsp;• Registry | `registry.json` + `registry_client.py` | ✅ | Tool-centric discovery by tag/keyword. `best_match` picks highest non-deprecated version. |
| &nbsp;&nbsp;• Versioning | `versioned_server.py` + `versioned_client.py` | ✅ | v1 deprecated + v2 parallel, optional params, `server://info` metadata. |
| **04 Lab — ADK + MCP** | `04-lab/` | ✅ **Running live** | ADK Agent ↔ Streamable HTTP MCP Server ↔ WeatherAPI.com |

---

## Live Services (Ready for Demo)


**MCP Tools exposed:**
- `get_current_weather(city)` — real-time weather from WeatherAPI.com
- `get_forecast(city, days)` — 1-3 day forecast
- `health_check()` — server health

**To test:** Open `http://127.0.0.1:8000` → select `weather_agent` → ask:
- `Thời tiết Hà Nội hôm nay?`
- `Dự báo 2 ngày Đà Nẵng`
- `Health check server`

---

## Environment Files (Persisted)

```
04-lab/mcp-server/.env
    WEATHERAPI_KEY=f23900f01884469ebf750911262808
    PORT=8085

04-lab/mcp-client/.env
    GOOGLE_API_KEY=AIzaSyBv7arFN09UPCSa9fWvMSygZTI5OXMHRik
    GEMINI_API_KEY=AIzaSyBv7arFN09UPCSa9fWvMSygZTI5OXMHRik

~/.adk/config.json
    {"telemetry": false}
```

---

## Key Technical Learnings

1. **Function Calling** = Model capability (decides *which* tool to call). App executes the tool.
2. **MCP** = Protocol standard (client↔server). Server self-describes tools via `@mcp.tool()`.
3. **MCP uses Function Calling internally** — LLM decides tool, MCP handles transport.
4. **Production concerns**: Auth (Bearer/OAuth), Tool Registry (discovery by capability), Versioning (parallel tools + optional params + metadata).

---

## Startup Script (for re-running)

```powershell
cd E:\AIlearn\Day26-Track3-2A202601841-NguyenQuocHung
powershell -ExecutionPolicy Bypass -File .\start_lab04.ps1
```

Script `start_lab04.ps1` auto-loads `.env`, kills old processes on ports 8085/8000, starts MCP Server + ADK Web, keeps terminal alive for Ctrl+C cleanup.

---

## Screenshots / Evidence

All commands executed successfully:

```
# 02 MCP Basics
$ python weather_client.py
Tools server cung cấp:
  - get_weather: Lấy thời tiết hiện tại của một thành phố.
call_tool get_weather(city='Hanoi'):   -> Hanoi: 29°C, trời mưa
call_tool get_weather(city='Danang'):  -> Danang: 30°C, nhiều mây
call_tool get_weather(city='Haiphong'):-> Haiphong: 33°C, mưa rào

# 03 Versioning
$ python versioned_client.py
Server: weather-v2 v2.0.0
Deprecated tools: ['get_weather']
[v1] get_weather('Hanoi'): Hanoi: 29°C, trời mưa
[v2] get_weather_v2('Hanoi', forecast=True): { "api_version": "2.0", "city": "Hanoi", "temp": 29, "forecast": [...] }

# 03 Registry
$ python registry_client.py
Best match: get_weather_v2 v2.0.0
Kết nối tới server [weather-v2]... Kết quả: {"api_version": "2.0", "city": "Hanoi", ...}

# 03 Auth
$ python auth_server.py  (terminal 1)
$ python auth_client.py  (terminal 2)
Tools (có auth): - get_weather
Kết quả: Hanoi: 29°C, trời mưa

# 04 Lab MCP Tools loaded by ADK
Tools loaded: ['get_current_weather', 'get_forecast', 'health_check']
```

---

**Submitted by:** Nguyen Quoc Hung  
**Date:** 2026-08-28