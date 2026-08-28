# Phân biệt MCP và Function Calling

Đây là hai khái niệm hay bị nhầm lẫn nhưng thực ra ở **hai tầng khác nhau**, và **bổ sung cho nhau** chứ không thay thế.

## Cấu trúc repo

```
Day26-Track3-2A202601841-NguyenQuocHung/
├── README.md                ← Bạn đang đọc file này
├── requirements.txt         ← pip install -r requirements.txt
├── start_lab04.ps1          ← Script khởi động Lab 04 (PowerShell)
├── SUBMISSION.md            ← Báo cáo nộp bài
│
├── 01-function-calling/     ← Bước 1: Function Calling thuần (Gemini SDK)
│   ├── README.md
│   └── weather_function_calling.py
│
├── 02-mcp-basics/           ← Bước 2: MCP server + client (không cần API key)
│   ├── README.md
│   ├── weather_server.py
│   └── weather_client.py
│
├── 03-production/           ← Bước 3: Auth, Tool Registry, Versioning
│   ├── README.md
│   ├── auth_server.py
│   ├── auth_client.py
│   ├── registry.json
│   ├── registry_client.py
│   └── versioned_server.py
│
└── 04-lab/                  ← Bước 4: Lab hoàn chỉnh - ADK Agent + MCP Server
    ├── README.md
    ├── mcp-server/          # MCP Server (FastMCP + Streamable HTTP)
    │   ├── weather.py       # Server chính: 5 tools, Auth, Versioning, server://info
    │   ├── pyproject.toml
    │   ├── .env.example
    │   ├── Dockerfile
    │   └── README.md
    │
    └── mcp-client/          # ADK Client (Google Agent Development Kit)
        ├── weather_agent/
        │   ├── agent.py     # Agent đọc server://info, chọn tool v2
        │   └── __init__.py
        ├── pyproject.toml
        ├── .env             # GOOGLE_API_KEY, GEMINI_API_KEY
        ├── verify_setup.py  # Kiểm tra setup
        └── README.md
```

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# MCP demo (không cần API key)
cd 02-mcp-basics && python weather_client.py

# Function Calling (cần Gemini API key)
export GEMINI_API_KEY=...
cd 01-function-calling && python weather_function_calling.py

# Production — Auth (2 terminal)
cd 03-production
python auth_server.py              # terminal 1
python auth_client.py              # terminal 2

# Production — Tool Registry
cd 03-production && python registry_client.py
```

---

## Định nghĩa ngắn gọn

**Function Calling** là một *khả năng của model* (capability). Model được huấn luyện để khi bạn đưa cho nó danh sách các "công cụ" (kèm schema mô tả tham số), nó có thể tự quyết định gọi công cụ nào và sinh ra JSON tham số phù hợp. Bản thân model **không chạy** function — nó chỉ nói "hãy gọi `get_weather(city='Hanoi')`". App mới là nơi chạy tool.

**MCP (Model Context Protocol)** là một *giao thức chuẩn* (protocol) — giống như USB-C hay HTTP cho thế giới AI. Nó định nghĩa cách một **MCP Client** (như Claude Code, Claude Desktop) kết nối tới các **MCP Server** để khám phá và sử dụng tools, resources, prompts một cách thống nhất.

---

## So sánh trực tiếp

| Tiêu chí | Function Calling | Model Context Protocol (MCP) |
|---|---|---|
| **Bản chất** | Tính năng của mô hình (Model capability) | Giao thức giao tiếp client–server |
| **Ai định nghĩa tool?** | Bạn hard-code trong từng app | Server tự công bố (self-describe) tool |
| **Tái sử dụng** | Phải viết lại cho mỗi app/model | Viết 1 lần, mọi MCP client dùng được |
| **Thực thi** | App của bạn tự chạy | MCP Server chạy, client điều phối |
| **Tính chuẩn hóa** | Mỗi nhà cung cấp 1 kiểu (OpenAI, Anthropic khác nhau) | Một chuẩn chung do Anthropic đề xuất |
| **Hệ sinh thái** | Khó chia sẻ dạng module đóng gói sẵn | Dễ dàng chia sẻ và tải về các "MCP Servers" mã nguồn mở |

## Quan hệ giữa chúng

Điểm quan trọng nhất: **MCP dùng Function Calling bên dưới**. Chúng không loại trừ nhau.

```
User hỏi
   │
   ▼
LLM (dùng Function Calling để quyết định gọi tool nào)
   │
   ▼
MCP Client  ──[giao thức MCP]──►  MCP Server (thực thi tool thật)
   │                                   │
   ◄───────────── kết quả ─────────────┘
   ▼
LLM tổng hợp câu trả lời
```

## Khi nào dùng cái nào?

- **Function Calling thuần**: app đơn giản, tool gắn chặt với 1 ứng dụng, không cần chia sẻ.
- **MCP**: muốn tool/tích hợp dùng lại được trên nhiều AI client, muốn tách biệt logic tool khỏi app, hoặc xây hệ sinh thái tích hợp (DB, file, API nội bộ...).

---

## Minh hoạ bằng mã nguồn

Cùng một tool `get_weather`, dưới đây là hai cách triển khai để thấy rõ sự khác biệt.

### [Cách 1 — Function Calling thuần (Google Gemini SDK)](01-function-calling/)

Tool được **định nghĩa và thực thi ngay trong app**. Model chỉ quyết định gọi tool nào, app tự chạy và đưa kết quả trở lại.

```
User hỏi → Model quyết định gọi get_weather("Hà Nội")
                    │
                    ▼
             App TỰ THỰC THI hàm get_weather
                    │
                    ▼
             Model tổng hợp câu trả lời
```

> Nhược điểm: schema viết tay, tool gắn chặt trong app — muốn dùng lại ở app khác phải copy cả schema lẫn hàm.

Chi tiết + code: xem [`01-function-calling/README.md`](01-function-calling/README.md)

### [Cách 2 — MCP (server tự công bố tool, mọi client dùng chung)](02-mcp-basics/)

Tool được tách ra **một MCP server độc lập**. Server tự "khai báo" nó có tool gì; bất kỳ MCP client nào (Claude Code, Claude Desktop, Cursor...) cũng cắm vào dùng được mà không cần biết code bên trong.

```
weather_client.py                       weather_server.py
┌─────────────┐    giao thức MCP    ┌─────────────────┐
│  list_tools │ ──────────────────▶ │ @mcp.tool()     │
│  call_tool  │ ◀────────────────── │ get_weather()   │
└─────────────┘     stdio           └─────────────────┘
```

Chi tiết + code: xem [`02-mcp-basics/README.md`](02-mcp-basics/README.md)

### Điểm khác biệt rút ra từ code

| | Function Calling thuần | MCP |
|---|---|---|
| Khai báo schema | Tự viết tay trong app | `@mcp.tool()` tự sinh từ type hints |
| Nơi thực thi tool | Trong app gọi model | Trong MCP server riêng |
| Khám phá tool | Hard-code danh sách `tools` | `session.list_tools()` tại runtime |
| Dùng lại ở app khác | Copy code | Cắm thêm client, không sửa server |
| Vai trò Function Calling | Là toàn bộ cơ chế | Là lớp model bên trong MCP |

---

## [MCP trong Production](03-production/)

Các ví dụ trên chạy tốt trên máy cá nhân, nhưng đưa vào **hệ thống production** cần giải quyết thêm ba vấn đề:

```
┌─────────────────────────────────────────────────────┐
│                  Production MCP                     │
│                                                     │
│  ┌──────────┐   ┌───────────┐   ┌───────────────┐   │
│  │ Security │   │ Registry  │   │  Versioning   │   │
│  │          │   │           │   │               │   │
│  │ • Auth   │   │ • Discover│   │ • v1 compat   │   │
│  │ • Token  │   │ • Connect │   │ • v2 features │   │
│  │ • Scopes │   │ • Health  │   │ • Deprecation │   │
│  └──────────┘   └───────────┘   └───────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 1. Security — Authentication & Authorization

MCP server phục vụ qua **HTTP** cho nhiều client → cần xác thực. MCP SDK hỗ trợ sẵn **Bearer Token** verification:

- Server: cấu hình `AuthSettings` + implement `TokenVerifier` protocol
- Client: gửi header `Authorization: Bearer <token>` qua `httpx.AsyncClient`
- Không có token → 401, token sai → 403, logic tool không biết gì về auth

| Tầng | Demo (stdio) | Production (HTTP) |
|---|---|---|
| Transport | stdio (cùng máy) | Streamable HTTP (qua mạng) |
| Auth | Không cần | Bearer token / OAuth / mTLS |
| Phạm vi truy cập | Toàn bộ | Scopes giới hạn từng client |

### 2. Tool Registry & Discovery

Agent **không hard-code** tool nào. Nó hỏi **Tool Registry** — danh mục trung tâm liệt kê tất cả tool từ mọi server — theo yêu cầu task:

```
Agent nhận task "lấy thời tiết Hà Nội"
   │
   ▼
Tool Registry: "tool nào có tag 'weather'?"
   │
   ├── get_weather v1.0 → server: weather (stdio)
   └── get_weather_v2 v2.0 → server: weather-v2 (stdio)
   │
   ▼
Agent chọn best match (v2.0, không deprecated)
   │
   ▼
Kết nối tới server weather-v2, gọi get_weather_v2(city="Hanoi")
```

Registry là **tool-centric** — đơn vị khám phá là **tool** (tag, description, parameters), không phải server.

| | Hard-code (demo) | Tool Registry (production) |
|---|---|---|
| Agent biết tool nào? | Chỉ tool được code sẵn | Tất cả tool trong registry |
| Tìm tool | Theo tên cố định | Theo tag, keyword, capability |
| Thêm tool mới | Sửa code agent | Thêm entry vào registry |
| Chọn tool | Developer quyết định | Agent tự chọn best match |

### 3. Versioning & Backward Compatibility

Server v1 có `get_weather(city)` trả chuỗi đơn giản. V2 muốn trả JSON chi tiết, thêm `include_forecast`. Nếu đổi trực tiếp → mọi client cũ break. Giải pháp — 3 kỹ thuật kết hợp:

| Kỹ thuật | Mô tả |
|---|---|
| **Tool mới song song** | `get_weather_v2` tồn tại bên cạnh `get_weather` — không xoá tool cũ |
| **Tham số optional** | `include_forecast`, `units` có default → client cũ gọi vẫn đúng |
| **Server metadata** | Resource `server://info` công bố version + deprecation notice |

Chi tiết + code cho cả 3 phần: xem [`03-production/README.md`](03-production/README.md)

### Tổng kết Production Checklist

| Khía cạnh | Dev/Demo | Production |
|---|---|---|
| **Transport** | stdio (cùng máy) | HTTP/SSE (qua mạng) |
| **Auth** | Không | Bearer token, OAuth, mTLS |
| **Discovery** | Hard-code tool/server | Tool Registry — agent tìm tool theo task |
| **Versioning** | 1 tool duy nhất | Tool v1 + v2 song song, deprecation notice |
| **Health** | Không | Health check, retry, circuit breaker |
| **Logging** | `print()` | Structured logging, tracing (OpenTelemetry) |

---

## [Lab 04 — Weather Agent với MCP Server Production-Ready](04-lab/)

Lab hoàn chỉnh kết hợp tất cả kiến thức: **MCP Server production** (Auth + Versioning + Metadata) + **ADK Agent** thông minh đọc metadata trước khi gọi tool.

### Kiến trúc

```
┌─────────────────┐   Streamable HTTP    ┌─────────────────┐      REST       ┌─────────────────┐
│   ADK Agent     │ ──────────────────── │   MCP Server    │ ─────────────── │  WeatherAPI.com │
│  (mcp-client)   │   localhost:8085/mcp │  (mcp-server)   │                 │                 │
└─────────────────┘                      └─────────────────┘                 └─────────────────┘
```

### Tính năng Production-Ready trong MCP Server (`04-lab/mcp-server/weather.py`)

| Tính năng | Implementation |
|-----------|----------------|
| **Transport** | Streamable HTTP (`transport="streamable-http"`) |
| **Authentication** | Bearer token (`MCP_AUTH_TOKEN` env, scopes `weather:read`, `weather:forecast`) |
| **Versioning** | 5 tools: v1 (deprecated) + v2 (JSON, optional params) song song |
| **Metadata** | Resource `server://info` — version, tools, deprecation, migration guide |
| **Health** | Tool `health_check()` |

### ADK Agent thông minh (`04-lab/mcp-client/weather_agent/agent.py`)

Agent **tự động đọc `server://info`** khi khởi động:
1. Fetch metadata từ MCP Server
2. Phân tích tools: ưu tiên v2 (`current` status), bỏ qua v1 (`deprecated`)
3. Log danh sách tool được chọn
4. Sử dụng tool v2 cho user queries

### Quick Start Lab 04

```bash
# 1. Cài đặt dependencies
cd 04-lab/mcp-server && uv sync
cd ../mcp-client && uv sync

# 2. Cấu hình environment
# Server
cp 04-lab/mcp-server/.env.example 04-lab/mcp-server/.env
# Edit .env: điền WEATHERAPI_KEY từ weatherapi.com

# Client
echo "GOOGLE_API_KEY=your_gemini_key" > 04-lab/mcp-client/.env

# 3. Chạy (2 terminal) hoặc dùng script PowerShell
# Terminal 1 - MCP Server:
cd 04-lab/mcp-server && uv run python weather.py

# Terminal 2 - ADK Web:
cd 04-lab/mcp-client && uv run adk web

# 4. Mở http://localhost:8000 → chọn weather_agent → chat
```

### Script khởi động tự động (Windows PowerShell)

```powershell
# Tự load .env, kill port cũ, start cả 2 service
.\start_lab04.ps1
```

### Test Authentication

```bash
# Token đúng
curl -X POST http://localhost:8085/mcp -H "Authorization: Bearer dev-token-abc123" -d '{"jsonrpc":"2.0","id":1,"method":"initialize",...}'

# Token sai → 403
# Thiếu token → 401
```

### Test Versioning

```bash
# Đọc metadata
curl -X POST http://localhost:8085/mcp -H "Authorization: Bearer dev-token-abc123" -d '{"jsonrpc":"2.0","id":1,"method":"resources/read","params":{"uri":"server://info"}}'

# Gọi v2 tool (JSON + optional params)
curl -X POST http://localhost:8085/mcp -H "Authorization: Bearer dev-token-abc123" -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_current_weather_v2","arguments":{"city":"Hanoi","include_forecast":true,"units":"celsius"}}}'
```

---

**Tóm lại:** Function Calling là *cơ chế model gọi công cụ*; MCP là *chuẩn để kết nối model với các công cụ đó* — và MCP thực chất dùng Function Calling làm nền tảng để hoạt động.

Lab 04 minh hoạ **full production MCP stack**: Server có Auth + Versioning + Metadata, Agent đọc metadata tự chọn tool phù hợp.
