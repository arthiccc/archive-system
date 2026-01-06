#!/bin/bash
set -e

echo "=========================================="
echo "College Document Archive System"
echo "=========================================="
echo ""

# Navigate to project directory
cd "$(dirname "$0")"
cd /workspaces/archive-system

# Check if .env exists, create from example if not
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

# Build and start containers
echo ""
echo "Starting Docker containers..."
docker compose up -d --build

# Wait for database to be ready
echo ""
echo "Waiting for database to be ready..."
for i in {1..30}; do
    if docker compose exec -T db pg_isready -U archive_admin -d archive_db > /dev/null 2>&1; then
        echo "✅ Database is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Database failed to start. Check logs with: docker compose logs"
        exit 1
    fi
    echo "   Waiting... ($i/30)"
    sleep 1
done

# Initialize database if needed
echo ""
echo "Initializing database..."
docker compose exec -T web python scripts/init-db.py

echo ""
echo "=========================================="
echo "✅ Application is running!"
echo ""
echo "📝 Next steps:"
echo "   1. Open the 'Ports' tab in Codespaces"
echo "   2. Click the link for port 5000 (Flask App)"
echo "   3. Create your admin account at /auth/login"
echo ""
echo "🔗 Commands:"
echo "   View logs:    docker compose logs web -f"
echo "   Stop app:     docker compose down"
echo "   Restart:      docker compose restart web"
echo "=========================================="
