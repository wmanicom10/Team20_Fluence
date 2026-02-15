Write-Host "🔧 Setting up Fluence Demo API..."

# Check if Node is installed
try {
    $nodeVersion = node -v
    Write-Host "✅ Node detected: $nodeVersion"
} catch {
    Write-Host "❌ Node.js is not installed. Install Node 18+ first."
    exit 1
}

# Initialize npm project if package.json doesn't exist
if (-Not (Test-Path "package.json")) {
    Write-Host "📦 Initializing npm project..."
    npm init -y | Out-Null
} else {
    Write-Host "📦 package.json already exists."
}

# Install dependencies
Write-Host "⬇️ Installing dependencies (express, cors)..."
npm install express cors

Write-Host ""
Write-Host "✅ Setup complete!"
Write-Host "🚀 Run the server with:"
Write-Host "   node fluence_demo_api.js"
