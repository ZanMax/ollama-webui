# Use an official Python runtime as a parent image
FROM python:3.11-slim
WORKDIR /app
COPY main.py index.html config.yaml /app/
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" aiohttp pyyaml
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
