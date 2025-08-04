#!/bin/bash

# FairnessNSP Streamlit Startup Script

echo "🏥 Starting FairnessNSP Streamlit Web Interface..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run 'uv sync' first."
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Check if streamlit is installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "❌ Streamlit not found. Installing dependencies..."
    uv sync
fi

# Start Streamlit
echo "🚀 Starting Streamlit server..."
echo "📱 Open your browser to: http://localhost:8501"
echo "⏹️  Press Ctrl+C to stop the server"
echo ""

streamlit run streamlit_app.py --server.port 8501 