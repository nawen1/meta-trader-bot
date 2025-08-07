#!/bin/bash

# BTCUSD Trading Bot Setup Script

echo "Setting up BTCUSD Trading Bot..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your exchange credentials and preferences"
else
    echo ".env file already exists"
fi

# Make main script executable
chmod +x main.py

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your exchange credentials"
echo "2. Run 'source venv/bin/activate' to activate the virtual environment"
echo "3. Run 'python main.py --demo' to start in demo mode"
echo "4. Run 'python main.py --stats' to view performance statistics"
echo ""
echo "For more information, see README.md"