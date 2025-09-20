from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather")

@ mcp.tool()
def get_weather(location: str) -> str:
    """
    Get weather in a given location
    Args:
        location: location, can be city state
    """
    return "Weather is cold and slightly wet"

if __name__ == "__main__":
    mcp.run()