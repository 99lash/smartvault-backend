"""
Database Seeder for SmartVault

Seeds the database with test data for development:
- 4 users (owner, admin, member, viewer)
- 2 vaults (1 locked with PIN, 1 unlocked)
- 3 vault authorizations (admin, member, viewer on vault 1)
- 3 access log entries

All users have password: smartvault123!
Vault 1 PIN: 482916

Usage: python seed.py
"""

import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import text

from app.infrastructure.db.session import SessionLocal
from app.application.services.password_hasher_service import PBKDF2PasswordHasher


def generate_id() -> str:
    return str(uuid.uuid4())


def seed():
    db = SessionLocal()
    hasher = PBKDF2PasswordHasher()

    # Check if already seeded
    result = db.execute(text("SELECT COUNT(*) FROM users"))
    if result.scalar() > 0:
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
        {
            "id": user_owner_id,
            "email": "owner@smartvault.dev",
            "password_hash": password_hash,
            "full_name": "John Owner",
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": user_admin_id,
            "email": "admin@smartvault.dev",
            "password_hash": hasher.hash("smartvault123!"),
            "full_name": "Jane Admin",
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": user_member_id,
            "email": "member@smartvault.dev",
            "password_hash": hasher.hash("smartvault123!"),
            "full_name": "Mike Member",
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": user_viewer_id,
            "email": "viewer@smartvault.dev",
            "password_hash": hasher.hash("smartvault123!"),
            "full_name": "Vera Viewer",
            "created_at": now,
            "updated_at": now,
        },
    ]

    for u in users:
        db.execute(
            text(
                "INSERT INTO users (id, email, password_hash, full_name, created_at, updated_at) "
                "VALUES (:id, :email, :password_hash, :full_name, :created_at, :updated_at)"
            ),
            u,
        )
    print(f"  Created {len(users)} users")

    # ── Vaults ─────────────────────────────────────────────
    vault1_id = generate_id()
    vault2_id = generate_id()
    pin_hash = hasher.hash("482916")

    vaults = [
        {
            "id": vault1_id,
            "owner_id": user_owner_id,
            "hardware_uuid": "ESP32-SV-001-ABCDEF",
            "vault_name": "Home Vault",
            "status": "LOCKED",
            "last_seen_at": now - timedelta(minutes=5),
            "pin_hash": pin_hash,
            "pin_set_at": now - timedelta(days=3),
            "created_at": now - timedelta(days=7),
            "updated_at": now,
        },
        {
            "id": vault2_id,
            "owner_id": user_owner_id,
            "hardware_uuid": "ESP32-SV-002-GHIJKL",
            "vault_name": "Office Vault",
            "status": "UNLOCKED",
            "last_seen_at": now - timedelta(minutes=1),
            "pin_hash": None,
            "pin_set_at": None,
            "created_at": now - timedelta(days=3),
            "updated_at": now,
        },
    ]

    for v in vaults:
        db.execute(
            text(
                "INSERT INTO vaults (id, owner_id, hardware_uuid, vault_name, status, "
                "last_seen_at, pin_hash, pin_set_at, created_at, updated_at) "
                "VALUES (:id, :owner_id, :hardware_uuid, :vault_name, :status, "
                ":last_seen_at, :pin_hash, :pin_set_at, :created_at, :updated_at)"
            ),
            v,
        )
    print(f"  Created {len(vaults)} vaults")

    # ── Vault Authorizations ───────────────────────────────
    authorizations = [
        {
            "id": generate_id(),
            "vault_id": vault1_id,
            "user_id": user_admin_id,
            "role": "ADMIN",
            "granted_by": user_owner_id,
            "granted_at": now - timedelta(days=5),
        },
        {
            "id": generate_id(),
            "vault_id": vault1_id,
            "user_id": user_member_id,
            "role": "MEMBER",
            "granted_by": user_owner_id,
            "granted_at": now - timedelta(days=4),
        },
        {
            "id": generate_id(),
            "vault_id": vault1_id,
            "user_id": user_viewer_id,
            "role": "VIEWER",
            "granted_by": user_admin_id,
            "granted_at": now - timedelta(days=2),
        },
    ]

    for a in authorizations:
        db.execute(
            text(
                "INSERT INTO vault_authorizations (id, vault_id, user_id, role, granted_by, granted_at) "
                "VALUES (:id, :vault_id, :user_id, :role, :granted_by, :granted_at)"
            ),
            a,
        )
    print(f"  Created {len(authorizations)} vault authorizations")

    # ── Access Logs ────────────────────────────────────────
    logs = [
        {
            "id": generate_id(),
            "vault_id": vault1_id,
            "user_id": user_owner_id,
            "action": "VAULT_UNLOCKED",
            "method": "PIN",
            "metadata": '{"ip": "192.168.1.10"}',
            "created_at": now - timedelta(hours=6),
        },
        {
            "id": generate_id(),
            "vault_id": vault1_id,
            "user_id": user_owner_id,
            "action": "MEMBER_ADDED",
            "method": "COMMAND",
            "metadata": '{"added_user_id": "' + user_member_id + '", "role": "MEMBER"}',
            "created_at": now - timedelta(days=4),
        },
        {
            "id": generate_id(),
            "vault_id": vault1_id,
            "user_id": user_member_id,
            "action": "VAULT_UNLOCK_FAILED",
            "method": "PIN",
            "metadata": '{"reason": "invalid_pin"}',
            "created_at": now - timedelta(hours=2),
        },
    ]

    for l in logs:
        db.execute(
            text(
                "INSERT INTO access_logs (id, vault_id, user_id, action, method, metadata, created_at) "
                "VALUES (:id, :vault_id, :user_id, :action, :method, CAST(:metadata AS jsonb), :created_at)"
            ),
            l,
        )
    print(f"  Created {len(logs)} access logs")

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


if __name__ == "__main__":
    seed()
