# Weather MCP Server

MCP Server cung cấp dữ liệu thời tiết thực tế từ **WeatherAPI.com** qua giao thức **Model Context Protocol (MCP)** với transport **Streamable HTTP**.

## 🌟 Tính năng

| Tool | Phiên bản | Mô tả | Input | Output |
|------|-----------|-------|-------|--------|
| `get_current_weather` | v1 (deprecated) | Thời tiết hiện tại - trả chuỗi định dạng | `city: string` | `string` |
| `get_current_weather_v2` | v2 (current) | Thời tiết hiện tại - trả JSON có cấu trúc | `city: string`, `include_forecast?: boolean`, `units?: "celsius"\|"fahrenheit"` | `JSON` |
| `get_forecast` | v1 (deprecated) | Dự báo thời tiết - trả chuỗi định dạng | `city: string`, `days?: integer` | `string` |
| `get_forecast_v2` | v2 (current) | Dự báo thời tiết - trả JSON có cấu trúc | `city: string`, `days?: integer`, `units?: "celsius"\|"fahrenheit"` | `JSON` |
| `health_check` | v1 | Kiểm tra server hoạt động | - | `string` |

## 📦 Cài đặt

### Yêu cầu
- Python 3.10+
- `uv` (khuyên dùng) hoặc `pip`
- API Key từ [WeatherAPI.com](https://www.weatherapi.com/) (free tier: 1M calls/tháng)

### Cài đặt dependencies
```bash
cd 04-lab/mcp-server
uv sync
# hoặc: pip install -e .
```

## 🚀 Chạy Server

### 1. Tạo file `.env` từ mẫu
```bash
cp .env.example .env
# Chỉnh sửa .env và điền WEATHERAPI_KEY
```

### 2. Chạy server (Streamable HTTP - port 8085)
```bash
uv run python weather.py
# Server chạy tại http://localhost:8085/mcp
```

### 3. Chạy server (stdio mode - cho Claude Code local)
```bash
# Không set PORT hoặc chạy với input pipe
uv run python weather.py < /dev/null
```

## 🔐 Authentication

Server yêu cầu **Bearer Token** trong header `Authorization`:

```bash
# Token mặc định (dev): dev-token-abc123
# Override qua env:
export MCP_AUTH_TOKEN="your-secure-token"
```

### Test Authentication
```bash
# Token đúng (200 OK)
curl -X POST http://localhost:8085/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer dev-token-abc123" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}'

# Token sai (403 Forbidden)
curl -X POST http://localhost:8085/mcp \
  -H "Authorization: Bearer wrong-token" \
  ...

# Thiếu token (401 Unauthorized)
curl -X POST http://localhost:8085/mcp \
  ...
```

## 📋 Versioning & Metadata

### Đọc server metadata
```bash
# qua MCP resource
curl -X POST http://localhost:8085/mcp \
  -H "Authorization: Bearer dev-token-abc123" \
  -d '{"jsonrpc":"2.0","id":1,"method":"resources/read","params":{"uri":"server://info"}}'
```

Metadata trả về:
```json
{
  "name": "weather",
  "version": "2.0.0",
  "tools": {
    "get_current_weather": {"version": "1.0", "status": "deprecated", "replacement": "get_current_weather_v2"},
    "get_current_weather_v2": {"version": "2.0", "status": "current", ...},
    "get_forecast": {"version": "1.0", "status": "deprecated", "replacement": "get_forecast_v2"},
    "get_forecast_v2": {"version": "2.0", "status": "current", ...},
    "health_check": {"version": "1.0", "status": "current"}
  },
  "deprecated_tools": ["get_current_weather", "get_forecast"],
  "migration_guide": "Migrate from v1 tools to v2 tools...",
  "authentication": {"type": "bearer", "header": "Authorization: Bearer <MCP_AUTH_TOKEN>"}
}
```

### Chiến lược Versioning
1. **Parallel tools**: v1 và v2 tồn tại song song (`get_current_weather` + `get_current_weather_v2`)
2. **Optional params**: v2 thêm `include_forecast`, `units` với default → client v1 gọi v2 vẫn chạy
3. **Metadata resource**: `server://info` công bố version, deprecation, migration guide

## 🤖 Đăng ký với AI Clients

### Claude Code
```bash
# Chạy server stdio mode (không cần PORT)
claude mcp add weather -- python /path/to/04-lab/mcp-server/weather.py
```

### Gemini CLI
```json
// ~/.gemini/settings.json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["/path/to/04-lab/mcp-server/weather.py"]
    }
  }
}
```

### Kết nối Streamable HTTP (remote)
```python
# Python client
from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession
import httpx

async with httpx.AsyncClient(headers={"Authorization": "Bearer dev-token-abc123"}) as http:
    async with streamable_http_client("http://localhost:8085/mcp", http_client=http) as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            tools = await session.list_tools()
            result = await session.call_tool("get_current_weather_v2", {"city": "Hanoi", "include_forecast": true})
```

## 🧪 Test Tools

### 1. Health Check
```bash
curl -X POST http://localhost:8085/mcp \
  -H "Authorization: Bearer dev-token-abc123" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"health_check","arguments":{}}}'
```

### 2. Current Weather v2 (JSON)
```bash
curl -X POST http://localhost:8085/mcp \
  -H "Authorization: Bearer dev-token-abc123" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_current_weather_v2","arguments":{"city":"Hanoi","include_forecast":true,"units":"celsius"}}}'
```

### 3. Forecast v2 (JSON)
```bash
curl -X POST http://localhost:8085/mcp \
  -H "Authorization: Bearer dev-token-abc123" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_forecast_v2","arguments":{"city":"Danang","days":2,"units":"celsius"}}}'
```

### 4. Sử dụng script verify_setup.py (từ mcp-client)
```bash
cd ../mcp-client
uv run python verify_setup.py
```

## 🐳 Deploy với Docker

```bash
# Build
docker build -t weather-mcp-server .

# Run
docker run -d \
  -p 8085:8085 \
  -e WEATHERAPI_KEY=your_key \
  -e MCP_AUTH_TOKEN=your_token \
  -e PORT=8085 \
  weather-mcp-server
```

## 📁 Cấu trúc dự án

```
04-lab/mcp-server/
├── weather.py          # Main MCP Server (FastMCP)
├── pyproject.toml      # Dependencies
├── .env                # Environment variables (KHÔNG commit)
├── .env.example        # Template env
├── Dockerfile          # Container config
└── README.md           # This file
```

## 🔧 Environment Variables

| Variable | Mặc định | Mô tả |
|----------|----------|-------|
| `WEATHERAPI_KEY` | *(required)* | API Key từ WeatherAPI.com |
| `MCP_AUTH_TOKEN` | `dev-token-abc123` | Bearer token cho authentication |
| `PORT` | `8085` | Port server (Cloud Run sẽ override) |

## 📝 License

MIT License - Day26 Lab Exercise