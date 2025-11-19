#!/bin/bash

echo "========================================="
echo "Starting Booking Service (FastAPI)"
echo "========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "✓ Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "========================================="
echo "✓ Starting FastAPI server on port 5003"
echo "========================================="
echo ""
echo "📚 API Documentation:"
echo "   - Swagger UI: http://localhost:5003/docs"
echo "   - ReDoc:      http://localhost:5003/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 app.py
