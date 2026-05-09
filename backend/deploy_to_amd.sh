#!/bin/bash
# ============================================================
# ForgeSight Backend — AMD MI300X Deployment Script
# Run this ON the AMD instance after upload:
#   bash deploy_to_amd.sh
# ============================================================
set -e

echo "=========================================="
echo "  ForgeSight Backend — AMD MI300X Setup"
echo "=========================================="

# ── 1. System packages ──────────────────────────────────────
echo "[1/6] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y python3-pip python3-venv git curl

# ── 2. Python virtual environment ───────────────────────────
echo "[2/6] Creating Python venv..."
python3 -m venv /opt/forgesight/venv
source /opt/forgesight/venv/bin/activate

# ── 3. Install Python dependencies ──────────────────────────
echo "[3/6] Installing Python packages..."
pip install --upgrade pip
pip install \
    fastapi==0.110.1 \
    uvicorn==0.25.0 \
    motor==3.3.1 \
    pymongo==4.5.0 \
    pydantic>=2.6.4 \
    python-dotenv>=1.0.1 \
    requests>=2.31.0 \
    python-multipart>=0.0.9 \
    python-jose>=3.3.0 \
    passlib>=1.7.4 \
    bcrypt==4.1.3 \
    email-validator>=2.2.0 \
    aiohttp>=3.9.0 \
    httpx>=0.27.0

# ── 4. Install MongoDB (if not already running) ──────────────
echo "[4/6] Checking MongoDB..."
if ! command -v mongod &> /dev/null; then
    echo "Installing MongoDB..."
    wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" \
        | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    sudo apt-get update -qq
    sudo apt-get install -y mongodb-org
fi

sudo systemctl start mongod || sudo service mongod start || true
echo "MongoDB status: $(sudo systemctl is-active mongod 2>/dev/null || echo 'check manually')"

# ── 5. Write .env file ───────────────────────────────────────
echo "[5/6] Writing .env..."
cat > /opt/forgesight/.env << 'EOF'
MONGO_URL=mongodb://localhost:27017
DB_NAME=forgesight
CORS_ORIGINS=*
# Set your AMD vLLM inference server URL here:
AMD_INFERENCE_URL=http://129.212.189.214
AMD_INFERENCE_TOKEN=DiPipPSZoxb96rcrP7X+B0N5mTTEzxU/ziesgI/Z2NPo9xPKM
AMD_MODEL_NAME=Qwen/Qwen2-VL-7B-Instruct
EOF

echo ""
echo "⚠️  Edit /opt/forgesight/.env to set AMD_INFERENCE_URL if needed."
echo ""

# ── 6. Create systemd service ────────────────────────────────
echo "[6/6] Creating systemd service..."
sudo bash -c 'cat > /etc/systemd/system/forgesight.service << EOF
[Unit]
Description=ForgeSight FastAPI Backend
After=network.target mongod.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/forgesight
EnvironmentFile=/opt/forgesight/.env
ExecStart=/opt/forgesight/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF'

sudo systemctl daemon-reload
sudo systemctl enable forgesight
sudo systemctl restart forgesight

echo ""
echo "=========================================="
echo "  ✅ ForgeSight backend deployed!"
echo "  Running at: http://0.0.0.0:8001"
echo "  Status: sudo systemctl status forgesight"
echo "  Logs:   sudo journalctl -u forgesight -f"
echo "=========================================="
