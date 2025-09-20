### create a simple mcp server - 1

#### Initialize project
```bash
uv init

cd helloworld

uv venv

.\.venv\Scripts\activate

uv add mcp[cli]
```

#### Init mcp server
Check `weather.py`


#### Run/Test mcp server
Check `mcp dev weather.py`

> opens up brower tab for mcp inspector
> make tools calls on the tools tab

#### Add MCP server config to Claude Client
```bash
{
    "mcpServers": {
        "weather": {
            "command": "uv",
            "args": [
                "--directory",
                "C:\\Users\\Lenovo\\mcp_examples\\helloworld",
                "run",
                "weather.py"
            ]
        }
    }
}
```

#### Automatically add to Claude
You do not need to manually do the above, you can simple do
`mcp install weather.py`
