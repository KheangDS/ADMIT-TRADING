#!/usr/bin/env python3
"""
AgriTrade - Standalone Admin Seeding Script
Seeds or resets the Superadministrator account from .env configuration.
Before seeding, all existing admin and superadmin accounts are purged to ensure clean state.

Usage:
    python seed_admin.py
    python seed_admin.py --email admin@agritrade.gov.kh --password YourSecretPassword --name "Super Administrator"
"""
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

# 1. Automatically load backend/.env if available
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# 2. Import database and models
try:
    from sqlalchemy import select, delete, update
    from app.config import settings
    from app.db import SessionLocal
    from app.models.accounts import User, AuthSession, SessionCredential, AuditEvent
    from app.services.auth_service import hash_password, audit
except ImportError as e:
    print(f"Error importing app modules: {e}")
    print("Please make sure you are in the backend directory and your virtualenv is activated.")
    sys.exit(1)


def seed_admin(email: str | None = None, password: str | None = None, name: str | None = None, role: str = "superadmin"):
    """
    Purges existing admin/superadmin accounts and seeds a fresh Superadministrator from .env.
    """
    email = (email or settings.ADMIN_EMAIL or "").strip().casefold()
    password = password or settings.ADMIN_PASSWORD or ""
    name = (name or settings.ADMIN_NAME or "AgriTrade Super Administrator").strip()
    role = "superadmin"

    if not email:
        print("❌ Error: Admin email is required. Configure ADMIN_EMAIL in .env or pass --email.")
        sys.exit(1)
    if len(password) < 8:
        print("❌ Error: Admin password must be at least 8 characters long. Configure ADMIN_PASSWORD in .env or pass --password.")
        sys.exit(1)

    db_target = settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "Database"
    print(f"Connecting to database: {db_target}")

    try:
        with SessionLocal.begin() as db:
            # 1. Locate and remove all existing admin and superadmin users to avoid conflicts
            existing_admins = db.scalars(select(User).where(User.role.in_(["admin", "superadmin"]))).all()
            if existing_admins:
                print(f"🧹 Purging {len(existing_admins)} existing admin/superadmin account(s) to avoid conflicts...")
                for old_admin in existing_admins:
                    # Clear audit foreign key references to this user
                    db.execute(update(AuditEvent).where(AuditEvent.actor_id == old_admin.id).values(actor_id=None))

                    # Remove sessions & credentials
                    session_ids = db.scalars(select(AuthSession.id).where(AuthSession.user_id == old_admin.id)).all()
                    if session_ids:
                        db.execute(delete(SessionCredential).where(SessionCredential.session_id.in_(session_ids)))
                        db.execute(delete(AuthSession).where(AuthSession.id.in_(session_ids)))

                    # Remove membership, receipt, and payment records if any
                    try:
                        from app.models.membership import Membership, PaymentRequest, Receipt
                        db.execute(delete(Membership).where(Membership.user_id == old_admin.id))
                        db.execute(delete(Receipt).where(Receipt.user_id == old_admin.id))
                        db.execute(delete(PaymentRequest).where(PaymentRequest.user_id == old_admin.id))
                    except Exception:
                        pass

                    db.delete(old_admin)
                db.flush()

            # 2. Check if a user with the target email already exists (e.g. member account) and remove it
            conflict_user = db.scalar(select(User).where(User.email == email))
            if conflict_user:
                db.execute(update(AuditEvent).where(AuditEvent.actor_id == conflict_user.id).values(actor_id=None))
                session_ids = db.scalars(select(AuthSession.id).where(AuthSession.user_id == conflict_user.id)).all()
                if session_ids:
                    db.execute(delete(SessionCredential).where(SessionCredential.session_id.in_(session_ids)))
                    db.execute(delete(AuthSession).where(AuthSession.id.in_(session_ids)))
                try:
                    from app.models.membership import Membership, PaymentRequest, Receipt
                    db.execute(delete(Membership).where(Membership.user_id == conflict_user.id))
                    db.execute(delete(Receipt).where(Receipt.user_id == conflict_user.id))
                    db.execute(delete(PaymentRequest).where(PaymentRequest.user_id == conflict_user.id))
                except Exception:
                    pass
                db.delete(conflict_user)
                db.flush()

            # 3. Create the fresh superadmin user
            user = User(
                email=email,
                name=name,
                role=role,
                password_hash=hash_password(password),
                google_sub=None,
                disabled=False,
            )
            db.add(user)
            db.flush()

            audit(db, None, "account.seed_admin", "user", user.id, {"provisioned_by": "seed_admin_script", "role": role})
            print(f"✅ Created fresh {role} account:")
            print(f"   • Name:     {name}")
            print(f"   • Email:    {email}")
            print(f"   • Role:     {role}")

        print("\n🎉 Superadministrator account is seeded successfully! You can log in at http://localhost:5174\n")
    except Exception as e:
        print(f"\n❌ Database error while seeding admin: {e}")
        print("   Make sure the database is running and migrations are applied (python -m alembic upgrade head).")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Seed fresh Superadministrator account from .env in AgriTrade PostgreSQL")
    parser.add_argument("--email", default=None, help="Admin email address (defaults to ADMIN_EMAIL in .env)")
    parser.add_argument("--password", default=None, help="Admin password (defaults to ADMIN_PASSWORD in .env)")
    parser.add_argument("--name", default=None, help="Admin full name (defaults to ADMIN_NAME in .env)")
    parser.add_argument("--role", default="superadmin", help="Role: superadmin (default)")

    args = parser.parse_args()
    seed_admin(args.email, args.password, args.name, args.role)


if __name__ == "__main__":
    main()
