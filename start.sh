#!/bin/bash

# Startup script for Income-Expense Tracker
# Usage: ./start.sh

echo "🚀 Starting Income-Expense Tracker..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Check if database exists
if [ ! -f "instance/finance.db" ]; then
    echo "🗄️  Initializing database..."
    export FLASK_APP=run.py
    flask init-db
fi

# Set environment variables
export FLASK_APP=run.py
export FLASK_ENV=development

# Start the application
echo ""
echo "✅ Starting Flask application..."
echo "📍 Application will be available at: http://localhost:5000"
echo "🔑 LINE Login: http://localhost:5000/auth/line/login"
echo "📊 API Docs: http://localhost:5000/api/v1/"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python run.py
