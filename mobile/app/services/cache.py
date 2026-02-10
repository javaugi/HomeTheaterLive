# mobile/app/services/cache.py
import json
from pathlib import Path
from typing import Optional, Any
import aiosqlite
import time

class CacheService:
    """Mobile cache service for offline storage"""

    def __init__(self, cache_dir: Path, max_size: int = 100):
        self.cache_dir = cache_dir
        self.max_size = max_size
        self.db_path = cache_dir / "mobile_cache.db"
        self.conn: Optional[aiosqlite.Connection] = None

    async def initialize(self):
        """Initialize cache database"""
        print(f"DEBUG: Initializing cache at {self.db_path}")

        # Ensure directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Create SQLite connection
        self.conn = await aiosqlite.connect(self.db_path)

        # Create cache table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT,
                timestamp INTEGER,
                expires INTEGER,
                tags TEXT
            )
        """)

        # Create index
        await self.conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)")
        await self.conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires)")

        await self.conn.commit()
        print(f"DEBUG: Cache initialized with max size: {self.max_size}")

    async def set(self, key: str, value: Any, ttl: Optional[int] = None, tags: Optional[list] = None):
        """Store item in cache"""
        if not self.conn:
            await self.initialize()

        expires = None
        if ttl:
            import time
            expires = int(time.time()) + ttl

        tags_json = json.dumps(tags) if tags else None
        value_json = json.dumps(value)

        await self.conn.execute("""
            INSERT OR REPLACE INTO cache (key, value, timestamp, expires, tags)
            VALUES (?, ?, ?, ?, ?)
        """, (key, value_json, int(time.time()), expires, tags_json))

        await self.conn.commit()

        # Clean up if over size limit
        await self._cleanup()

    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if not self.conn:
            await self.initialize()

        cursor = await self.conn.execute("""
            SELECT value FROM cache
            WHERE key = ? AND (expires IS NULL OR expires > ?)
        """, (key, int(time.time())))

        row = await cursor.fetchone()
        await cursor.close()

        if row:
            return json.loads(row[0])
        return None

    async def _cleanup(self):
        """Clean up old entries"""
        # Remove expired items
        await self.conn.execute("DELETE FROM cache WHERE expires IS NOT NULL AND expires <= ?",
                               (int(time.time()),))

        # If still over limit, remove oldest
        cursor = await self.conn.execute("SELECT COUNT(*) FROM cache")
        count = (await cursor.fetchone())[0]
        await cursor.close()

        if count > self.max_size:
            to_remove = count - self.max_size
            cursor = await self.conn.execute("""
                SELECT key FROM cache
                ORDER BY timestamp ASC
                LIMIT ?
            """, (to_remove,))

            old_keys = [row[0] for row in await cursor.fetchall()]
            await cursor.close()

            for key in old_keys:
                await self.conn.execute("DELETE FROM cache WHERE key = ?", (key,))

            await self.conn.commit()

    async def cleanup(self):
        """Cleanup resources"""
        if self.conn:
            await self.conn.close()
        print("DEBUG: Cache service cleaned up")


async def init_cache_service(max_size: int) -> CacheService:
    """Initialize cache service"""
    from mobile.app.core.config import settings

    cache_dir = settings.CACHE_DIR or Path.home() / ".hometheaterlive" / "cache"
    service = CacheService(cache_dir, max_size)
    await service.initialize()
    return service# -*- coding: utf-8 -*-

