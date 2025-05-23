#!/bin/bash

# Setup script for OpenAI Image MCP Server

set -e

echo "🚀 Setting up OpenAI Image MCP Server..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.9+ first."
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "📦 Poetry not found. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install dependencies
echo "📦 Installing dependencies with Poetry..."
poetry install

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "🔧 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your OpenAI API key"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit the .env file and add your OpenAI API key:"
echo "   nano .env"
echo ""
echo "2. Test the server:"
echo "   poetry run python -m src.openai_image_mcp.server"
echo ""
echo "3. Add to Claude Desktop configuration:"
echo "   Copy the contents of mcp-config.json to your Claude Desktop MCP configuration"
echo "   Remember to update the path and API key in the configuration"
echo ""
echo "📖 For more information, see README.md"