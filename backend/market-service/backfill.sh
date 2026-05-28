#!/bin/bash
# =============================================================================
# Bhavcopy backfill script
# Ingests the last N trading days into market-service
# Run this once to seed enough history for all technical indicators:
#   RSI(14)  needs 14+ days
#   MACD     needs 26+ days
#   MA50     needs 50+ days  ← this is why 4 days produces no results
#   MA200    needs 200 days  (optional, enhances scoring)
#
# Usage:
#   chmod +x backfill.sh
#   ./backfill.sh YOUR_JWT_TOKEN
#   ./backfill.sh YOUR_JWT_TOKEN 120   # backfill 120 trading days
# =============================================================================

TOKEN="${1}"
DAYS="${2:-90}"
BASE_URL="http://localhost/api"

if [ -z "$TOKEN" ]; then
  echo "Usage: $0 <jwt_token> [days]"
  echo ""
  echo "Get your token:"
  echo "  curl -s -X POST $BASE_URL/auth/login \\"
  echo "    -H 'Content-Type: application/json' \\"
  echo "    -d '{\"email\":\"you@example.com\",\"password\":\"yourpass\"}' \\"
  echo "    | python3 -c \"import sys,json; print(json.load(sys.stdin)['access_token'])\""
  exit 1
fi

echo "================================================"
echo "  Stock Alert — Bhavcopy Backfill"
echo "  Target : last $DAYS trading days"
echo "  API    : $BASE_URL/market/ingest/manual"
echo "================================================"
echo ""

# Generate trading days list (Mon-Fri, oldest first)
python3 -c "
from datetime import date, timedelta
days_target = int('$DAYS')
today = date.today()
trading_days = []
d = today - timedelta(days=1)
while len(trading_days) < days_target:
    if d.weekday() < 5:
        trading_days.append(d.strftime('%Y-%m-%d'))
    d -= timedelta(days=1)
for day in reversed(trading_days):
    print(day)
" > /tmp/backfill_dates.txt

TOTAL=$(wc -l < /tmp/backfill_dates.txt)
SUCCESS=0
SKIPPED=0
FAILED=0
COUNT=0

while IFS= read -r trade_date; do
    COUNT=$((COUNT + 1))
    printf "[%3d/%d] %s ... " "$COUNT" "$TOTAL" "$trade_date"

    RESPONSE=$(curl -s -X POST \
        "$BASE_URL/market/ingest/manual?trade_date=$trade_date" \
        -H "Authorization: Bearer $TOKEN" \
        --max-time 30)

    STATUS=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','error'))" 2>/dev/null)
    ROWS=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('rows',''))" 2>/dev/null)

    case "$STATUS" in
        success)
            SUCCESS=$((SUCCESS + 1))
            echo "✓  $ROWS rows"
            ;;
        skipped)
            SKIPPED=$((SKIPPED + 1))
            echo "—  skipped (holiday/already done)"
            ;;
        *)
            FAILED=$((FAILED + 1))
            echo "✗  $RESPONSE"
            ;;
    esac

    sleep 0.8

done < /tmp/backfill_dates.txt

echo ""
echo "================================================"
echo "  Done"
echo "  ✓  Success : $SUCCESS days"
echo "  —  Skipped : $SKIPPED days"
echo "  ✗  Failed  : $FAILED days"
echo "================================================"
echo ""

if [ "$SUCCESS" -ge 50 ]; then
    echo "✅ Enough history loaded — scanner should now return results."
elif [ "$SUCCESS" -ge 14 ]; then
    echo "⚠  RSI/MACD will work but MA50 needs 50+ days."
    echo "   Re-run: $0 $TOKEN 120"
else
    echo "❌ Not enough days. Check failed entries above."
fi

rm -f /tmp/backfill_dates.txt