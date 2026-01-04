#!/bin/bash
# Clean restart script for Flask app

echo "🛑 Stopping Flask..."
pkill -f "flask run" || true
sleep 2

echo "🗑️  Cleaning cache..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
rm -f instance/finance.db-journal instance/finance.db-wal instance/finance.db-shm 2>/dev/null || true

echo "✅ Verifying database schema..."
sqlite3 instance/finance.db "PRAGMA table_info(project_invite);" | grep -E "(email|token|status)" && echo "  ✓ Columns exist" || echo "  ✗ Missing columns!"

echo ""
echo "🚀 Ready to start! Run:"
echo "   flask run --host=0.0.0.0 --port=5000"
