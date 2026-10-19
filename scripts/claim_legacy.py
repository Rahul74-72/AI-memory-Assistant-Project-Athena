"""Local administrator-only migration of original single-owner data.

Requires the destination user's password and an explicit ownership assertion.
Never expose this command as an API. Make a backup before invoking.
"""
import argparse
import getpass
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    from dotenv import load_dotenv
    load_dotenv(ROOT/".env")
    from sqlalchemy import select, update
    from app.auth import verify_password
    from app.database.database import SessionLocal
    from app.database.models import User, Memory, Conversation
    parser=argparse.ArgumentParser()
    parser.add_argument("--username",required=True)
    parser.add_argument("--i-own-all-legacy-data",action="store_true")
    args=parser.parse_args()
    if not args.i_own_all_legacy_data:
        parser.error("Confirm ownership of ALL old single-user data before claiming it.")
    with SessionLocal() as db:
        user=db.scalar(select(User).where(User.username==args.username.lower()))
        if not user or not verify_password(getpass.getpass("Account password: "),user.password_hash):
            raise SystemExit("Authentication failed")
        legacy=db.scalar(select(User).where(User.username=="__athena_legacy__"))
        if not legacy:
            raise SystemExit("No legacy account exists. Start Athena once to run migrations.")
        for model in (Memory,Conversation):
            result=db.execute(update(model).where(model.user_id==legacy.id).values(user_id=user.id))
            print(f"Assigned {result.rowcount} {model.__tablename__} rows.")
        db.commit()


if __name__ == "__main__":
    main()
