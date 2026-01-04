#!/usr/bin/env python3
"""Test if ProjectInvite model can see the new columns"""
import sys
sys.path.insert(0, '/Users/pond-dev/Documents/python-line-Income-expenses')

from app import create_app, db
from app.models.project import ProjectInvite

app = create_app()

with app.app_context():
    # Check if columns exist in model
    print("ProjectInvite columns:")
    for col in ProjectInvite.__table__.columns:
        print(f"  - {col.name}: {col.type}")

    # Try to query
    print("\nTrying to query invites...")
    try:
        invites = db.session.query(ProjectInvite).filter_by(status='pending').all()
        print(f"✅ Query successful! Found {len(invites)} pending invites")
    except Exception as e:
        print(f"❌ Query failed: {e}")
