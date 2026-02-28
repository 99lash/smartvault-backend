"""
Database Seeder for SmartVault

Seeds the database with test data for development:
- 4 users (owner, admin, member, viewer)
- 2 vaults (1 locked with PIN, 1 unlocked)
- 3 vault authorizations (admin, member, viewer on vault 1)
- 26 access log entries across 7 days (unlocks, failures, lockouts, member ops)
- 2 API keys (active + expired)
- 12 admin audit log entries across 7 days

Security alert triggers (seeded):
- 6 failed unlocks in last hour → warning alert
- 3 PIN lockouts in 24h → warning alert

All users have password: smartvault123!
Vault 1 PIN: 482916

Usage: python seed.py          # Seed Postgres only
       python seed.py --redis  # Seed Postgres + Redis
"""

import hashlib
import sys
import uuid
from datetime import datetime, timezone, timedelta

from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models.user_orm import UserORM
from app.infrastructure.db.models.vault_orm import VaultORM
from app.infrastructure.db.models.vault_authorization_orm import VaultAuthorizationORM
from app.infrastructure.db.models.access_log_orm import AccessLogORM
from app.infrastructure.db.models.api_key_orm import APIKeyORM
from app.infrastructure.db.models.admin_audit_orm import AdminAuditORM
from app.application.services.password_hasher_service import PBKDF2PasswordHasher


def generate_id() -> str:
    return str(uuid.uuid4())


def seed():
    db = SessionLocal()
    hasher = PBKDF2PasswordHasher()

    # Check if already seeded
    if db.query(UserORM).count() > 0:
        print("Database already has data. Skipping seed.")
        print("To re-seed, run: make db-reset && make migrate && make seed")
        db.close()
        return

    print("Seeding database...")

    now = datetime.now(timezone.utc)
    password_hash = hasher.hash("smartvault123!")

    # ── Users ──────────────────────────────────────────────
    user_owner_id = generate_id()
    user_admin_id = generate_id()
    user_member_id = generate_id()
    user_viewer_id = generate_id()

    users = [
        UserORM(
            id=user_owner_id,
            email="owner@smartvault.dev",
            password_hash=password_hash,
            full_name="John Owner",
            created_at=now,
            updated_at=now,
        ),
        UserORM(
            id=user_admin_id,
            email="admin@smartvault.dev",
            password_hash=hasher.hash("smartvault123!"),
            full_name="Jane Admin",
            created_at=now,
            updated_at=now,
        ),
        UserORM(
            id=user_member_id,
            email="member@smartvault.dev",
            password_hash=hasher.hash("smartvault123!"),
            full_name="Mike Member",
            created_at=now,
            updated_at=now,
        ),
        UserORM(
            id=user_viewer_id,
            email="viewer@smartvault.dev",
            password_hash=hasher.hash("smartvault123!"),
            full_name="Vera Viewer",
            created_at=now,
            updated_at=now,
        ),
    ]

    db.add_all(users)
    db.flush()
    print(f"  Created {len(users)} users")

    # ── Vaults ─────────────────────────────────────────────
    vault1_id = generate_id()
    vault2_id = generate_id()
    pin_hash = hasher.hash("482916")

    vaults = [
        VaultORM(
            id=vault1_id,
            owner_id=user_owner_id,
            hardware_uuid="ESP32-SV-001-ABCDEF",
            vault_name="Home Vault",
            status="LOCKED",
            last_seen_at=now - timedelta(minutes=5),
            pin_hash=pin_hash,
            pin_set_at=now - timedelta(days=3),
            created_at=now - timedelta(days=7),
            updated_at=now,
        ),
        VaultORM(
            id=vault2_id,
            owner_id=user_owner_id,
            hardware_uuid="ESP32-SV-002-GHIJKL",
            vault_name="Office Vault",
            status="UNLOCKED",
            last_seen_at=now - timedelta(minutes=1),
            pin_hash=None,
            pin_set_at=None,
            created_at=now - timedelta(days=3),
            updated_at=now,
        ),
    ]

    db.add_all(vaults)
    db.flush()
    print(f"  Created {len(vaults)} vaults")

    # ── Vault Authorizations ───────────────────────────────
    authorizations = [
        VaultAuthorizationORM(
            id=generate_id(),
            vault_id=vault1_id,
            user_id=user_admin_id,
            role="ADMIN",
            granted_by=user_owner_id,
            granted_at=now - timedelta(days=5),
        ),
        VaultAuthorizationORM(
            id=generate_id(),
            vault_id=vault1_id,
            user_id=user_member_id,
            role="MEMBER",
            granted_by=user_owner_id,
            granted_at=now - timedelta(days=4),
        ),
        VaultAuthorizationORM(
            id=generate_id(),
            vault_id=vault1_id,
            user_id=user_viewer_id,
            role="VIEWER",
            granted_by=user_admin_id,
            granted_at=now - timedelta(days=2),
        ),
    ]

    db.add_all(authorizations)
    print(f"  Created {len(authorizations)} vault authorizations")

    # ── Access Logs ────────────────────────────────────────
    # Spread realistic activity across 7 days to populate ops/business/security dashboards
    logs = [
        # --- Day 7 (oldest): Initial setup activity ---
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_owner_id,
            action="PIN_SET", method="COMMAND",
            metadata_={"source": "initial_setup"},
            created_at=now - timedelta(days=7, hours=2),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_owner_id,
            action="VAULT_STATE_CHANGED", method="SYSTEM",
            metadata_={"from": "OFFLINE", "to": "LOCKED"},
            created_at=now - timedelta(days=7, hours=1),
        ),
        # --- Day 5: Member management ---
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_owner_id,
            action="MEMBER_ADDED", method="COMMAND",
            metadata_={"added_user_id": user_admin_id, "role": "ADMIN"},
            created_at=now - timedelta(days=5, hours=3),
        ),
        # --- Day 4: More member management + vault usage ---
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_owner_id,
            action="MEMBER_ADDED", method="COMMAND",
            metadata_={"added_user_id": user_member_id, "role": "MEMBER"},
            created_at=now - timedelta(days=4, hours=6),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_owner_id,
            action="VAULT_UNLOCKED", method="PIN",
            metadata_={"ip": "192.168.1.10"},
            created_at=now - timedelta(days=4, hours=2),
        ),
        # --- Day 3: Normal usage ---
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_admin_id,
            action="VAULT_UNLOCKED", method="COMMAND",
            metadata_={"ip": "10.0.0.5"},
            created_at=now - timedelta(days=3, hours=8),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_admin_id,
            action="UNLOCK_COMMAND_SENT", method="COMMAND",
            metadata_={"ip": "10.0.0.5"},
            created_at=now - timedelta(days=3, hours=4),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault2_id, user_id=user_owner_id,
            action="VAULT_UNLOCKED", method="PIN",
            metadata_={"ip": "192.168.1.10"},
            created_at=now - timedelta(days=3, hours=1),
        ),
        # --- Day 2: Viewer added, mixed activity ---
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_admin_id,
            action="MEMBER_ADDED", method="COMMAND",
            metadata_={"added_user_id": user_viewer_id, "role": "VIEWER"},
            created_at=now - timedelta(days=2, hours=10),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_member_id,
            action="VAULT_UNLOCKED", method="PIN",
            metadata_={"ip": "172.16.0.22"},
            created_at=now - timedelta(days=2, hours=5),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_member_id,
            action="VAULT_UNLOCK_FAILED", method="PIN",
            metadata_={"reason": "invalid_pin"},
            created_at=now - timedelta(days=2, hours=3),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault2_id, user_id=user_owner_id,
            action="VAULT_STATE_CHANGED", method="SYSTEM",
            metadata_={"from": "LOCKED", "to": "UNLOCKED"},
            created_at=now - timedelta(days=2, hours=1),
        ),
        # --- Day 1: Heavier usage ---
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_owner_id,
            action="VAULT_UNLOCKED", method="PIN",
            metadata_={"ip": "192.168.1.10"},
            created_at=now - timedelta(days=1, hours=9),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_admin_id,
            action="VAULT_UNLOCKED", method="COMMAND",
            metadata_={"ip": "10.0.0.5"},
            created_at=now - timedelta(days=1, hours=6),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_member_id,
            action="VAULT_UNLOCK_FAILED", method="PIN",
            metadata_={"reason": "invalid_pin"},
            created_at=now - timedelta(days=1, hours=4),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_member_id,
            action="VAULT_UNLOCK_FAILED", method="PIN",
            metadata_={"reason": "invalid_pin"},
            created_at=now - timedelta(days=1, hours=3, minutes=55),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_member_id,
            action="VAULT_UNLOCK_FAILED", method="PIN",
            metadata_={"reason": "invalid_pin", "lockout": True},
            created_at=now - timedelta(days=1, hours=3, minutes=50),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=None,
            action="MEMBER_REMOVED", method="COMMAND",
            metadata_={"removed_user_id": user_viewer_id, "by": user_owner_id},
            created_at=now - timedelta(days=1, hours=1),
        ),
        # --- Today: Recent failed unlock spike (triggers security alerts) ---
        # 6 failed unlocks in last hour → triggers "warning" (threshold ≥5/hr)
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_member_id,
            action="VAULT_UNLOCK_FAILED", method="PIN",
            metadata_={"reason": "invalid_pin"},
            created_at=now - timedelta(minutes=55),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_member_id,
            action="VAULT_UNLOCK_FAILED", method="PIN",
            metadata_={"reason": "invalid_pin"},
            created_at=now - timedelta(minutes=45),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_member_id,
            action="VAULT_UNLOCK_FAILED", method="PIN",
            metadata_={"reason": "invalid_pin"},
            created_at=now - timedelta(minutes=35),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_member_id,
            action="VAULT_UNLOCK_FAILED", method="PIN",
            metadata_={"reason": "invalid_pin"},
            created_at=now - timedelta(minutes=25),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_member_id,
            action="VAULT_UNLOCK_FAILED", method="PIN",
            metadata_={"reason": "invalid_pin"},
            created_at=now - timedelta(minutes=15),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_member_id,
            action="VAULT_UNLOCK_FAILED", method="PIN",
            metadata_={"reason": "invalid_pin", "lockout": True},
            created_at=now - timedelta(minutes=10),
        ),
        # 2 lockouts in 24h (from today + yesterday) → combined ≥3 triggers "warning"
        AccessLogORM(
            id=generate_id(), vault_id=vault1_id, user_id=user_owner_id,
            action="VAULT_UNLOCKED", method="PIN",
            metadata_={"ip": "192.168.1.10"},
            created_at=now - timedelta(hours=3),
        ),
        AccessLogORM(
            id=generate_id(), vault_id=vault2_id, user_id=user_owner_id,
            action="VAULT_STATE_CHANGED", method="SYSTEM",
            metadata_={"from": "UNLOCKED", "to": "LOCKED"},
            created_at=now - timedelta(hours=2),
        ),
    ]

    db.add_all(logs)
    print(f"  Created {len(logs)} access logs")

    # ── API Keys ───────────────────────────────────────────
    api_keys = [
        APIKeyORM(
            key_hash=hashlib.sha256("sv_dev_key_001".encode()).hexdigest(),
            name="Development Key",
            created_by="admin@smartvault.dev",
            last_used_at=now - timedelta(hours=1),
            expires_at=now + timedelta(days=90),
            is_active=True,
            created_at=now - timedelta(days=30),
        ),
        APIKeyORM(
            key_hash=hashlib.sha256("sv_expired_key_002".encode()).hexdigest(),
            name="Expired Integration Key",
            created_by="owner@smartvault.dev",
            last_used_at=now - timedelta(days=15),
            expires_at=now - timedelta(days=5),
            is_active=False,
            created_at=now - timedelta(days=60),
        ),
    ]

    db.add_all(api_keys)
    print(f"  Created {len(api_keys)} API keys")

    # ── Admin Audit Logs ───────────────────────────────────
    audit_logs = [
        # Day 6
        AdminAuditORM(
            action="VIEW_BUSINESS_OVERVIEW",
            target_type="system", target_id=None,
            details={"source": "admin_dashboard"},
            ip_address="192.168.1.10",
            created_at=now - timedelta(days=6, hours=4),
        ),
        # Day 5
        AdminAuditORM(
            action="CREATE_API_KEY",
            target_type="api_key", target_id="1",
            details={"key_name": "Development Key"},
            ip_address="192.168.1.10",
            created_at=now - timedelta(days=5, hours=2),
        ),
        # Day 4
        AdminAuditORM(
            action="VIEW_OPS_SUMMARY",
            target_type="system", target_id=None,
            details={"source": "admin_dashboard"},
            ip_address="10.0.0.5",
            created_at=now - timedelta(days=4, hours=8),
        ),
        # Day 3
        AdminAuditORM(
            action="VIEW_SECURITY_ALERTS",
            target_type="system", target_id=None,
            details={"filter": "last_7d"},
            ip_address="10.0.0.5",
            created_at=now - timedelta(days=3, hours=5),
        ),
        AdminAuditORM(
            action="REVOKE_SESSION",
            target_type="session", target_id=generate_id(),
            details={"user_email": "member@smartvault.dev", "reason": "suspicious_activity"},
            ip_address="192.168.1.10",
            created_at=now - timedelta(days=3, hours=2),
        ),
        # Day 2
        AdminAuditORM(
            action="VIEW_OPS_SUMMARY",
            target_type="system", target_id=None,
            details={"source": "admin_dashboard"},
            ip_address="192.168.1.10",
            created_at=now - timedelta(days=2, hours=6),
        ),
        AdminAuditORM(
            action="VIEW_BUSINESS_OVERVIEW",
            target_type="system", target_id=None,
            details={"source": "admin_dashboard"},
            ip_address="10.0.0.5",
            created_at=now - timedelta(days=2, hours=1),
        ),
        # Day 1
        AdminAuditORM(
            action="REVOKE_API_KEY",
            target_type="api_key", target_id="2",
            details={"key_name": "Expired Integration Key", "reason": "expired"},
            ip_address="192.168.1.10",
            created_at=now - timedelta(days=1, hours=3),
        ),
        AdminAuditORM(
            action="VIEW_SECURITY_ALERTS",
            target_type="system", target_id=None,
            details={"filter": "last_24h"},
            ip_address="10.0.0.5",
            created_at=now - timedelta(days=1, hours=1),
        ),
        # Today
        AdminAuditORM(
            action="VIEW_OPS_SUMMARY",
            target_type="system", target_id=None,
            details={"source": "admin_dashboard"},
            ip_address="192.168.1.10",
            created_at=now - timedelta(hours=4),
        ),
        AdminAuditORM(
            action="VIEW_SECURITY_ALERTS",
            target_type="system", target_id=None,
            details={"filter": "last_24h", "alerts_found": 2},
            ip_address="192.168.1.10",
            created_at=now - timedelta(hours=2),
        ),
        AdminAuditORM(
            action="VIEW_BUSINESS_OVERVIEW",
            target_type="system", target_id=None,
            details={"source": "admin_dashboard"},
            ip_address="10.0.0.5",
            created_at=now - timedelta(hours=1),
        ),
    ]

    db.add_all(audit_logs)
    print(f"  Created {len(audit_logs)} admin audit logs")

    db.commit()
    db.close()

    print("\nSeed complete!")
    print("\n  Test Credentials:")
    print("  ─────────────────────────────────────────")
    print("  owner@smartvault.dev   / smartvault123!  (Owner)")
    print("  admin@smartvault.dev   / smartvault123!  (Admin)")
    print("  member@smartvault.dev  / smartvault123!  (Member)")
    print("  viewer@smartvault.dev  / smartvault123!  (Viewer)")
    print("  ─────────────────────────────────────────")
    print("  Vault 1 PIN: 482916")
    print("  Dev API Key: sv_dev_key_001")


def seed_redis():
    """Seed Redis with fake sessions, rate limits, and email counters."""
    from redis import Redis
    from app.core.settings import settings

    r = Redis.from_url(settings.REDIS_URL, decode_responses=False)
    r.ping()
    print("\nSeeding Redis...")

    now = datetime.now(timezone.utc)

    # ── Fake refresh tokens (active sessions) ─────────
    fake_users = [
        ("owner-session", "owner-user-id"),
        ("admin-session-1", "admin-user-id"),
        ("admin-session-2", "admin-user-id"),
        ("member-session", "member-user-id"),
        ("viewer-session", "viewer-user-id"),
    ]
    for token_id, user_id in fake_users:
        r.setex(f"refresh:{token_id}", 604800, user_id.encode())
    print(f"  Created {len(fake_users)} fake refresh tokens (sessions)")

    # ── Fake rate limit entries ───────────────────────
    rate_limits = [
        ("rate_limit:pin:unlock:192.168.1.50", 4, 300),
        ("rate_limit:pin:unlock:10.0.0.99", 7, 180),
        ("rate_limit:login:192.168.1.50", 3, 600),
        ("rate_limit:login:172.16.0.33", 9, 120),
        ("rate_limit:api:10.0.0.5", 15, 60),
    ]
    for key, count, ttl in rate_limits:
        r.setex(key, ttl, str(count).encode())
    print(f"  Created {len(rate_limits)} fake rate limit entries")

    # ── Email counters ────────────────────────────────
    for days_ago in range(7):
        date_str = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        sent_key = f"email:sent:{date_str}"
        failed_key = f"email:failed:{date_str}"
        sent_count = max(1, 12 - days_ago * 2)
        failed_count = 1 if days_ago < 3 else 0
        r.setex(sent_key, 604800, str(sent_count).encode())
        if failed_count:
            r.setex(failed_key, 604800, str(failed_count).encode())
    print("  Created 7 days of email send/fail counters")

    r.close()
    print("Redis seed complete!")


if __name__ == "__main__":
    seed()
    if "--redis" in sys.argv:
        seed_redis()
