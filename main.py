import yaml
import aiohttp
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.yaml"
HTML_PATH = BASE_DIR / "index.html"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_config():
    """Loads the server configuration from config.yaml."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="config.yaml not found.")
    except yaml.YAMLError as e:
        raise HTTPException(status_code=500, detail=f"Error parsing config.yaml: {e}")

config = load_config()
OLLAMA_SERVERS = {server['name']: server['url'] for server in config.get('servers', [])}

@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serves the main HTML file for the UI."""
    if not HTML_PATH.is_file():
        raise HTTPException(status_code=500, detail="index.html not found.")
    return HTML_PATH.read_text()

@app.get("/servers")
async def get_servers():
    """Returns the list of configured Ollama server names."""
    return {"servers": list(OLLAMA_SERVERS.keys())}

@app.post("/api/tags")
async def get_ollama_tags(request: Request):
    """
    Proxies the request to fetch available models (tags) from a selected Ollama server.
    """
    data = await request.json()
    server_name = data.get('server')
    if not server_name or server_name not in OLLAMA_SERVERS:
        raise HTTPException(status_code=400, detail="Invalid or missing server name.")

    ollama_url = f"{OLLAMA_SERVERS[server_name]}/api/tags"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(ollama_url) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=502, detail=f"Error connecting to Ollama server '{server_name}': {e}")


@app.post("/api/chat")
async def ollama_chat_proxy(request: Request):
    """
    Proxies the chat request to the selected Ollama server and streams the response.
    """
    try:
        data = await request.json()
        server_name = data.get('server')
        model = data.get('model')
        messages = data.get('messages')

        if not all([server_name, model, messages]):
            raise HTTPException(status_code=400, detail="Missing server, model, or messages in request.")
        
        if server_name not in OLLAMA_SERVERS:
            raise HTTPException(status_code=400, detail="Invalid server name.")

        ollama_url = f"{OLLAMA_SERVERS[server_name]}/api/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True
        }

        async def stream_generator():
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(ollama_url, json=payload) as response:
                        response.raise_for_status()
                        async for chunk in response.content.iter_any():
                            yield chunk
                except aiohttp.ClientError as e:
                    print(f"Error during streaming from Ollama server '{server_name}': {e}")
                    yield f'{{"error": "Failed to stream from Ollama: {e}"}}'.encode()


        return StreamingResponse(stream_generator(), media_type="application/x-ndjson")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
