"""
bootstrap_db.py
Helper script to initialize the PostgreSQL database, run migrations, and seed the admin user.
"""
import os
import subprocess
import sys

def run_command(cmd, env=None):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, env=env)
    if result.returncode != 0:
        print(f"Error executing: {cmd}")
        return False
    return True

def main():
    # 1. Check if DATABASE_URL is set
    from backend.core.config import SQLALCHEMY_DATABASE_URI
    print(f"Target Database: {SQLALCHEMY_DATABASE_URI}")

    # 2. Run migrations
    print("\n[1/2] Running migrations...")
    env = os.environ.copy()
    env["FLASK_APP"] = "backend.app"
    if not run_command(r"venv\Scripts\flask db upgrade", env=env):
        print("Migration failed. Ensure PostgreSQL is running and the database exists.")
        return

    # 3. Seed Admin
    print("\n[2/2] Seeding admin user...")
    env["PYTHONPATH"] = "."
    if not run_command(r"venv\Scripts\python.exe seed_admin.py", env=env):
        print("Seeding failed.")
        return

    print("\nSuccess! Database is initialized and admin user is ready.")

if __name__ == "__main__":
    main()
