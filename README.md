# Ollama WebUI
A simple, multi-tab web interface for interacting with one or more Ollama instances

## Install packages
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Edit the config.yaml

```yaml
servers:
  - name: "Local Ollama"
    url: "http://127.0.0.1:11434"
  - name: "Remote Test Server"
    url: "http://192.168.1.100:11434"
```

## Run the app
```bash
chmod +x run.sh
./run.sh
```

## Run with Docker
```bash
docker-compose up -d
```