#!/bin/bash

echo "🔧 Setting up Fluence Demo API..."

# Check if Node is installed
if ! command -v node >/dev/null 2>&1; then
  echo "❌ Node.js is not installed."
  echo "Install Node 18+ from https://nodejs.org"
  exit 1
fi

NODE_VERSION=$(node -v)
echo "✅ Node detected: $NODE_VERSION"

# Check Node version (must be 18+)
NODE_MAJOR=$(node -v | cut -d. -f1 | sed 's/v//')
if [ "$NODE_MAJOR" -lt 18 ]; then
  echo "❌ Node 18+ required (fetch support)."
  exit 1
fi

# Initialize npm project if needed
if [ ! -f package.json ]; then
  echo "📦 Initializing npm project..."
  npm init -y >/dev/null
else
  echo "📦 package.json already exists."
fi

# Install dependencies
echo "⬇️ Installing dependencies (express, cors)..."
npm install express cors

echo ""
echo "✅ Setup complete!"
echo "🚀 Start the server with:"
echo "   node fluence_demo_api.js"
