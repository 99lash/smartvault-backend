#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# SmartVault Wrong PIN Simulator
#
# Sends N wrong PIN attempts against the vault unlock endpoint
# to generate real access logs and trigger security alerts.
#
# Usage:
#   bash simulate_wrong_pins.sh          # 5 attempts (default)
#   bash simulate_wrong_pins.sh 10       # 10 attempts
#   bash simulate_wrong_pins.sh 25       # 25 attempts (triggers critical alert)
#
# Thresholds:
#   ≥5 failures/hr  → security warning
#   ≥20 failures/hr → security critical
#   5 consecutive   → vault lockout (423 for 5 min)
#
# Requires: backend running (make up), database seeded (make seed)
# ─────────────────────────────────────────────────────────────

set -euo pipefail

BASE_URL="${API_BASE_URL:-http://localhost:8000}"
ATTEMPTS="${1:-5}"
USER_EMAIL="owner@smartvault.dev"
USER_PASSWORD="smartvault123!"
WRONG_PIN="839271"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " SmartVault Wrong PIN Simulator"
echo " Attempts: ${ATTEMPTS} | User: ${USER_EMAIL}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Step 1: Login ──────────────────────────────────
echo -e "\n${CYAN}→ Logging in as ${USER_EMAIL}...${NC}"
login_response=$(curl -s -X POST "${BASE_URL}/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${USER_EMAIL}\",\"password\":\"${USER_PASSWORD}\"}")

access_token=$(echo "$login_response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

if [ -z "$access_token" ]; then
    echo -e "${RED}✗ Login failed${NC}"
    echo "  Response: ${login_response:0:200}"
    exit 1
fi
echo -e "${GREEN}✓ Login successful${NC} (token: ${access_token:0:20}...)"

# ── Step 2: Find vault with PIN ───────────────────
echo -e "\n${CYAN}→ Finding vault with PIN set...${NC}"
vaults_response=$(curl -s "${BASE_URL}/api/v1/vaults" \
    -H "Authorization: Bearer ${access_token}")

vault_id=$(echo "$vaults_response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
vaults = data if isinstance(data, list) else data.get('items', data.get('vaults', []))
for v in vaults:
    if v.get('pin_hash') or v.get('has_pin') or v.get('pin_set_at'):
        print(v['id'])
        break
" 2>/dev/null)

if [ -z "$vault_id" ]; then
    echo -e "${YELLOW}⚠ Could not auto-detect vault. Querying database...${NC}"
    vault_id=$(docker compose exec -T postgres psql -U postgres -d smartvault -t -A \
        -c "SELECT id FROM vaults WHERE pin_hash IS NOT NULL LIMIT 1;" 2>/dev/null | tr -d '[:space:]')
fi

if [ -z "$vault_id" ]; then
    echo -e "${RED}✗ No vault with PIN found. Run 'make seed' first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Target vault: ${vault_id}${NC}"

# ── Step 3: Send wrong PINs ──────────────────────
echo -e "\n${CYAN}→ Sending ${ATTEMPTS} wrong PIN attempts...${NC}\n"

for i in $(seq 1 "$ATTEMPTS"); do
    response=$(curl -s -w "\n%{http_code}" -X POST \
        "${BASE_URL}/api/v1/vaults/${vault_id}/unlock/pin" \
        -H "Authorization: Bearer ${access_token}" \
        -H "Content-Type: application/json" \
        -d "{\"pin\":\"${WRONG_PIN}\"}")

    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | sed '$d')

    result=$(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('result', d.get('detail','?')))" 2>/dev/null || echo "?")
    remaining=$(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('attempts_remaining'); print(f' ({r} left)' if r is not None else '')" 2>/dev/null || echo "")

    case "$http_code" in
        200)
            echo -e "  ${YELLOW}#${i}${NC}  → ${http_code}  ${result}${remaining}"
            ;;
        423)
            echo -e "  ${RED}#${i}${NC}  → ${http_code}  🔒 LOCKED OUT  ${result}"
            ;;
        429)
            echo -e "  ${RED}#${i}${NC}  → ${http_code}  ⏱  RATE LIMITED  ${result}"
            ;;
        *)
            echo -e "  ${RED}#${i}${NC}  → ${http_code}  ${result}"
            ;;
    esac

    # Small delay to avoid overwhelming
    sleep 0.3
done

# ── Step 4: Check security alerts ─────────────────
ADMIN_TOKEN="${ADMIN_TOKEN:-sk_TBn8_PzP-CD9BIODfdILDRQqIy_yGAb6kfbvHeanG2g}"
echo -e "\n${CYAN}→ Checking security alerts...${NC}"

alerts_response=$(curl -s "${BASE_URL}/api/internal/security/alerts" \
    -H "X-Admin-Token: ${ADMIN_TOKEN}")

echo "$alerts_response" | python3 -c "
import sys, json
d = json.load(sys.stdin)
status = d.get('status', '?')
alerts = d.get('active_alerts', [])
last = d.get('last_24h', {})

colors = {'ok': '\033[0;32m', 'warning': '\033[0;33m', 'critical': '\033[0;31m'}
color = colors.get(status, '\033[0m')
nc = '\033[0m'

print(f'  Status: {color}{status.upper()}{nc}')
print(f'  Failed unlocks (1h): {last.get(\"failed_unlocks_1h\", \"?\")}')
print(f'  Failed unlocks (24h): {last.get(\"failed_unlocks_24h\", \"?\")}')
print(f'  PIN lockouts (24h): {last.get(\"pin_lockouts_24h\", \"?\")}')
if alerts:
    print(f'  Active alerts:')
    for a in alerts:
        print(f'    • [{a.get(\"severity\",\"?\")}] {a.get(\"message\",\"?\")}')
" 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Done. Refresh the admin dashboard to see updates."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
