FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app and agents
COPY app.py .
COPY agents.py .

# Copy the React build
COPY build/ ./build/

# Expose port 7860 (required by HF Spaces)
EXPOSE 7860

# Run the app
# We'll use uvicorn to run the FastAPI + Gradio app
CMD ["python", "app.py"]
