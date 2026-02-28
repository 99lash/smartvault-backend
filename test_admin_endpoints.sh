#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# SmartVault Internal Admin Endpoint Tester
#
# Curls every internal admin endpoint and reports PASS/FAIL.
# Requires: backend running (make up), database seeded (make seed),
#           Redis seeded (make seed-redis).
#
# Usage: bash test_admin_endpoints.sh
# ─────────────────────────────────────────────────────────────

set -euo pipefail

BASE_URL="${API_BASE_URL:-http://localhost:8000}"
ADMIN_TOKEN="${ADMIN_TOKEN:-sk_TBn8_PzP-CD9BIODfdILDRQqIy_yGAb6kfbvHeanG2g}"

PASS=0
FAIL=0
WARN=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

check_endpoint() {
    local method="$1"
    local path="$2"
    local expected_status="${3:-200}"
    local label="$4"

    local url="${BASE_URL}${path}"
    local response
    local http_code
    local body

    response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" \
        -H "X-Admin-Token: ${ADMIN_TOKEN}" \
        -H "Content-Type: application/json" 2>&1) || true

    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "$expected_status" ]; then
        echo -e "  ${GREEN}✓ PASS${NC}  ${method} ${path} → ${http_code}  ${CYAN}${label}${NC}"
        PASS=$((PASS + 1))

        # Print summary info for key endpoints
        case "$path" in
            */ops/summary)
                echo "         $(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); b=d.get('business',{}); print(f'users={b.get(\"users\",{}).get(\"total\",\"?\")}, vaults={b.get(\"vaults\",{}).get(\"total\",\"?\")}, status={d.get(\"overall_status\",\"?\")}')" 2>/dev/null || echo "(parse error)")"
                ;;
            */security/alerts)
                echo "         $(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'status={d.get(\"status\",\"?\")}, alerts={len(d.get(\"active_alerts\",[]))}')" 2>/dev/null || echo "(parse error)")"
                ;;
            */sessions/stats)
                echo "         $(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'active_tokens={d.get(\"total_active_tokens\",\"?\")}')" 2>/dev/null || echo "(parse error)")"
                ;;
            */rate-limits)
                echo "         $(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'active_keys={d.get(\"total_active_keys\",\"?\")}')" 2>/dev/null || echo "(parse error)")"
                ;;
            */business/overview)
                echo "         $(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'users={d.get(\"users\",{}).get(\"total\",\"?\")}, vaults={d.get(\"vaults\",{}).get(\"total\",\"?\")}, members={d.get(\"members\",{}).get(\"total_authorizations\",\"?\")}')" 2>/dev/null || echo "(parse error)")"
                ;;
            */notifications/email)
                echo "         $(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'sent_today={d.get(\"sent_today\",\"?\")}, failed_today={d.get(\"failed_today\",\"?\")}')" 2>/dev/null || echo "(parse error)")"
                ;;
            */ops/audit)
                echo "         $(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); items=d.get('items',d if isinstance(d,list) else []); print(f'entries={len(items)}')" 2>/dev/null || echo "(parse error)")"
                ;;
            */ops/api-keys)
                echo "         $(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); items=d.get('items',d if isinstance(d,list) else []); print(f'keys={len(items)}')" 2>/dev/null || echo "(parse error)")"
                ;;
        esac
    else
        echo -e "  ${RED}✗ FAIL${NC}  ${method} ${path} → ${http_code} (expected ${expected_status})  ${label}"
        echo "         ${body:0:200}"
        FAIL=$((FAIL + 1))
    fi
}

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " SmartVault Internal Admin Endpoint Test"
echo " Base: ${BASE_URL}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Health ─────────────────────────────────────────
echo -e "\n${CYAN}─── Health ───${NC}"
check_endpoint GET "/api/internal/ping" 200 "Health check"

# ── Ops ────────────────────────────────────────────
echo -e "\n${CYAN}─── Operations ───${NC}"
check_endpoint GET "/api/internal/ops/summary" 200 "Dashboard summary"
check_endpoint GET "/api/internal/ops/diagnostics/redis" 200 "Redis diagnostics"
check_endpoint GET "/api/internal/ops/diagnostics/websockets" 200 "WebSocket diagnostics"
check_endpoint GET "/api/internal/ops/diagnostics/database" 200 "Database diagnostics"
check_endpoint GET "/api/internal/ops/rate-limits" 200 "Rate limit metrics"
check_endpoint GET "/api/internal/ops/sessions/stats" 200 "Session statistics"
check_endpoint GET "/api/internal/ops/notifications/email" 200 "Email notifications"
check_endpoint GET "/api/internal/ops/audit" 200 "Audit logs"
check_endpoint GET "/api/internal/ops/api-keys" 200 "API keys"

# ── Business ───────────────────────────────────────
echo -e "\n${CYAN}─── Business ───${NC}"
check_endpoint GET "/api/internal/business/overview" 200 "Business overview"
check_endpoint GET "/api/internal/business/trends" 200 "Business trends"
check_endpoint GET "/api/internal/business/activity" 200 "Business activity"

# ── Security ───────────────────────────────────────
echo -e "\n${CYAN}─── Security ───${NC}"
check_endpoint GET "/api/internal/security/alerts" 200 "Security alerts"

# ── Auth Check (negative test) ────────────────────
echo -e "\n${CYAN}─── Auth Validation ───${NC}"
bad_response=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
    "${BASE_URL}/api/internal/ops/summary" \
    -H "X-Admin-Token: invalid-token" 2>&1) || true
if [ "$bad_response" = "401" ]; then
    echo -e "  ${GREEN}✓ PASS${NC}  GET /api/internal/ops/summary (bad token) → 401  ${CYAN}Rejects invalid token${NC}"
    PASS=$((PASS + 1))
else
    echo -e "  ${RED}✗ FAIL${NC}  GET /api/internal/ops/summary (bad token) → ${bad_response} (expected 401)"
    FAIL=$((FAIL + 1))
fi

no_token_response=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
    "${BASE_URL}/api/internal/ops/summary" 2>&1) || true
if [ "$no_token_response" = "401" ] || [ "$no_token_response" = "403" ]; then
    echo -e "  ${GREEN}✓ PASS${NC}  GET /api/internal/ops/summary (no token) → ${no_token_response}  ${CYAN}Rejects missing token${NC}"
    PASS=$((PASS + 1))
else
    echo -e "  ${RED}✗ FAIL${NC}  GET /api/internal/ops/summary (no token) → ${no_token_response} (expected 401/403)"
    FAIL=$((FAIL + 1))
fi

# ── Summary ────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TOTAL=$((PASS + FAIL))
echo -e " Results: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC} / ${TOTAL} total"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
