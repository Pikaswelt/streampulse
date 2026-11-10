#!/usr/bin/env bash
# Start StreamPulse Dashboard & Cloudflare Tunnel

python3 /root/streampulse/dashboard.py > /root/streampulse/output/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo "Dashboard running with PID $DASHBOARD_PID"

sleep 2

/usr/local/bin/cloudflared tunnel --url http://127.0.0.1:8080 --no-autoupdate > /root/streampulse/output/cloudflared.log 2>&1 &
TUNNEL_PID=$!
echo "Cloudflared running with PID $TUNNEL_PID"

wait
