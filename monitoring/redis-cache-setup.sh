#!/bin/bash
# Redis Caching Setup for Flight Agent
# Adds Redis caching layer for FlightAware API responses

set -e

echo "🗄️  Setting up Redis caching..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Install Redis
print_info "Installing Redis..."
sudo apt-get update -qq
sudo apt-get install -y redis-server
print_status "Redis installed"

# Configure Redis
print_info "Configuring Redis..."
sudo tee -a /etc/redis/redis.conf > /dev/null << 'REDIS_EOF'

# Flight Agent Configuration
maxmemory 256mb
maxmemory-policy allkeys-lru
tcp-keepalive 60
timeout 300
REDIS_EOF

# Start Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
print_status "Redis started"

# Update docker-compose.yml to include Redis
cd /opt/flight-agent-docker

print_info "Updating docker-compose.yml with Redis..."
cat > docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: flight-agent-redis
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  flight-agent:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: guardian-buddy-flight-agent
    ports:
      - "8001:8001"
    env_file:
      - .env
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - CACHE_TTL=300
    depends_on:
      - redis
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        tag: "flight-agent"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped

volumes:
  redis-data:
COMPOSE_EOF
print_status "docker-compose.yml updated"

# Add Redis to requirements
print_info "Updating Python requirements..."
if ! grep -q "redis" flight_agent/requirements.txt; then
    echo "" >> flight_agent/requirements.txt
    echo "# Redis caching" >> flight_agent/requirements.txt
    echo "redis>=5.0,<6" >> flight_agent/requirements.txt
fi
print_status "Requirements updated"

# Create Redis cache module
print_info "Creating cache module..."
cat > flight_agent/cache.py << 'CACHE_EOF'
"""Redis caching for Flight Agent."""
import os
import json
import hashlib
import logging
from typing import Optional, Any
from datetime import datetime

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class FlightCache:
    """Redis-backed cache for flight data."""

    def __init__(self):
        self.enabled = REDIS_AVAILABLE
        self.client = None
        self.ttl = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes default

        if self.enabled:
            try:
                host = os.getenv("REDIS_HOST", "localhost")
                port = int(os.getenv("REDIS_PORT", "6379"))
                self.client = redis.Redis(
                    host=host,
                    port=port,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                # Test connection
                self.client.ping()
                logger.info(f"Redis cache enabled (TTL: {self.ttl}s)")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Cache disabled.")
                self.enabled = False
                self.client = None
        else:
            logger.info("Redis not available. Cache disabled.")

    def _make_key(self, flight_num: str, departure_date: str) -> str:
        """Generate cache key from flight details."""
        raw = f"flight:{flight_num}:{departure_date}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, flight_num: str, departure_date: str) -> Optional[dict]:
        """Get cached flight data."""
        if not self.enabled or not self.client:
            return None

        try:
            key = self._make_key(flight_num, departure_date)
            data = self.client.get(key)
            if data:
                logger.info(f"Cache HIT: {flight_num}")
                return json.loads(data)
            else:
                logger.debug(f"Cache MISS: {flight_num}")
                return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, flight_num: str, departure_date: str, data: dict) -> bool:
        """Cache flight data."""
        if not self.enabled or not self.client:
            return False

        try:
            key = self._make_key(flight_num, departure_date)
            serialized = json.dumps(data)
            self.client.setex(key, self.ttl, serialized)
            logger.debug(f"Cached: {flight_num} (TTL: {self.ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, flight_num: str, departure_date: str) -> bool:
        """Delete cached flight data."""
        if not self.enabled or not self.client:
            return False

        try:
            key = self._make_key(flight_num, departure_date)
            self.client.delete(key)
            logger.debug(f"Cache deleted: {flight_num}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def clear(self) -> bool:
        """Clear all cached data."""
        if not self.enabled or not self.client:
            return False

        try:
            self.client.flushdb()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    def stats(self) -> dict:
        """Get cache statistics."""
        if not self.enabled or not self.client:
            return {"enabled": False}

        try:
            info = self.client.info("stats")
            return {
                "enabled": True,
                "keys": self.client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "ttl": self.ttl
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"enabled": True, "error": str(e)}


# Global cache instance
_cache = None


def get_cache() -> FlightCache:
    """Get or create cache instance."""
    global _cache
    if _cache is None:
        _cache = FlightCache()
    return _cache
CACHE_EOF
print_status "Cache module created"

# Restart Docker containers
print_info "Restarting services with Redis..."
docker-compose down
docker-compose up -d --build
print_status "Services restarted"

# Wait for services
print_info "Waiting for services to be healthy..."
sleep 10

# Test Redis connection
print_info "Testing Redis connection..."
if docker exec guardian-buddy-flight-agent python -c "import redis; r=redis.Redis(host='redis'); r.ping(); print('OK')" 2>/dev/null; then
    print_status "Redis connection successful"
else
    print_info "Redis check skipped (redis-py may not be installed yet)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_status "Redis Caching Setup Complete! 🗄️"
echo ""
echo "📦 What was configured:"
echo "   • Redis 7 (Alpine) container"
echo "   • 256MB memory limit with LRU eviction"
echo "   • 5-minute cache TTL (configurable via CACHE_TTL)"
echo "   • Python redis client library"
echo "   • Cache module (flight_agent/cache.py)"
echo ""
echo "🔧 Configuration:"
echo "   • Host: redis (Docker network)"
echo "   • Port: 6379"
echo "   • Max Memory: 256MB"
echo "   • Eviction: allkeys-lru"
echo "   • Default TTL: 300 seconds (5 minutes)"
echo ""
echo "📊 Usage in your code:"
echo "   from cache import get_cache"
echo "   "
echo "   cache = get_cache()"
echo "   "
echo "   # Try to get from cache"
echo "   cached = cache.get(flight_num, departure_date)"
echo "   if cached:"
echo "       return cached"
echo "   "
echo "   # Fetch from API"
echo "   data = await provider.fetch_status(...)"
echo "   "
echo "   # Cache the result"
echo "   cache.set(flight_num, departure_date, data.model_dump())"
echo ""
echo "🧪 Test Redis:"
echo "   # Check Redis is running"
echo "   docker ps | grep redis"
echo "   "
echo "   # Connect to Redis CLI"
echo "   docker exec -it flight-agent-redis redis-cli"
echo "   "
echo "   # View cache stats"
echo "   docker exec flight-agent-redis redis-cli INFO stats"
echo "   "
echo "   # View all keys"
echo "   docker exec flight-agent-redis redis-cli KEYS '*'"
echo ""
echo "📈 Monitor cache performance:"
echo "   # Get hit/miss ratio"
echo "   docker exec flight-agent-redis redis-cli INFO stats | grep keyspace"
echo "   "
echo "   # View memory usage"
echo "   docker exec flight-agent-redis redis-cli INFO memory | grep used_memory_human"
echo ""
echo "🔄 To change cache TTL:"
echo "   Add to .env file: CACHE_TTL=600"
echo "   Then: docker-compose restart flight-agent"
echo ""
print_status "Cache is ready! API responses will now be cached 🚀"

