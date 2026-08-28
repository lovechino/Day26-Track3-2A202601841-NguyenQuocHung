"""
Weather Agent - Connects to Remote MCP Server with Versioning Support
Reads server metadata (server://info) before using tools for optimal version selection.
"""
import asyncio
import json
import logging
from google.adk import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
import httpx

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MCP_SERVER_URL = "http://localhost:8085/mcp"

async def fetch_server_metadata(url: str) -> dict:
    """Fetch server metadata from server://info resource."""
    try:
        async with httpx.AsyncClient() as http_client:
            async with streamable_http_client(url, http_client=http_client) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    info = await session.read_resource("server://info")
                    metadata = json.loads(info.contents[0].text)
                    logger.info(f"📋 Server metadata fetched: {metadata.get('name')} v{metadata.get('version')}")
                    return metadata
    except Exception as e:
        logger.warning(f"⚠️ Could not fetch server metadata: {e}")
        return {}

def select_best_tools(metadata: dict) -> list[str]:
    """Select best tool versions based on server metadata."""
    if not metadata or "tools" not in metadata:
        # Fallback: use all available tools
        return ["get_current_weather", "get_forecast", "health_check"]
    
    selected = []
    tools_info = metadata.get("tools", {})
    
    # Prefer v2 tools over v1
    for tool_name, tool_info in tools_info.items():
        if tool_info.get("status") == "current":
            selected.append(tool_name)
            logger.info(f"   ✅ Selected {tool_name} (v{tool_info.get('version')})")
        elif tool_info.get("status") == "deprecated":
            logger.info(f"   ⏭️ Skipping deprecated {tool_name} (v{tool_info.get('version')}) - use {tool_info.get('replacement')}")
    
    # Always include health_check
    if "health_check" in tools_info and "health_check" not in selected:
        selected.append("health_check")
    
    return selected

logger.info(f"🌐 Initializing weather agent with remote MCP server")
logger.info(f"📡 MCP Server: {MCP_SERVER_URL}")

try:
    # Create connection parameters for the remote MCP server
    connection_params = StreamableHTTPConnectionParams(
        url=MCP_SERVER_URL,
        timeout=30.0,
    )
    
    # Create the MCP toolset - this will connect to the remote server
    logger.info("🔌 Connecting to MCP server...")
    weather_tools = McpToolset(
        connection_params=connection_params,
    )
    logger.info("✅ MCP toolset created successfully")
    
    # Fetch server metadata to select best tool versions
    logger.info("📥 Fetching server metadata (server://info)...")
    metadata = asyncio.run(fetch_server_metadata(MCP_SERVER_URL))
    
    if metadata:
        best_tools = select_best_tools(metadata)
        logger.info(f"🎯 Using tools: {best_tools}")
    else:
        best_tools = ["get_current_weather_v2", "get_forecast_v2", "health_check"]
        logger.info(f"🎯 Using default v2 tools: {best_tools}")
    
    # Create the agent with remote MCP tools
    root_agent = Agent(
        name="weather_agent",
        model="gemini-2.5-flash",
        tools=[weather_tools],
    )
    logger.info("✅ Weather agent initialized with remote MCP tools:")
    for tool in best_tools:
        logger.info(f"   - {tool}")
    logger.info("🎉 Remote MCP connection successful!")
    
except Exception as e:
    logger.error(f"❌ Failed to connect to remote MCP server: {e}")
    logger.error(f"   Server URL: {MCP_SERVER_URL}")
    import traceback
    traceback.print_exc()
    
    # Create a fallback agent without tools
    logger.warning("⚠️  Creating fallback agent without MCP tools")
    root_agent = Agent(
        name="weather_agent",
        model="gemini-2.5-flash",
    )