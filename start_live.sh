#!/usr/bin/env bash
# StreamPulse Live Runner for NTE 1.4 Preview Special Program

STREAM_URL="https://youtu.be/zrDTlGF6Pg8"
TOPIC="Neverness to Everness (NTE) Version 1.4 'For Whom the Verses Mourn' Preview Special Program"
TONE="gaming excitement, character reveals, new areas, combat gameplay mechanics, redeem codes, patch highlights"

cd /root/streampulse

echo "=========================================================="
echo " Starting StreamPulse for: NTE Version 1.4 Preview"
echo " Stream URL: $STREAM_URL"
echo " Interval: 120s (2 minutes per chunk)"
echo " Output Feed: /root/streampulse/output/live_feed.md"
echo "=========================================================="

python3 run.py run "$STREAM_URL" \
  --interval 120 \
  --topic "$TOPIC" \
  --tone "$TONE" \
  "$@"
