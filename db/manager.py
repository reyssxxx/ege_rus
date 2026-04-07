"""Менеджер базы данных с одним долгоживущим соединением."""

import logging

import aiosqlite

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Управляет единственным соединением с SQLite.
    
    WAL режим для конкурентных записей.
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None
    
    async def connect(self):
        """Открыть соединение и настроить."""
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        
        # WAL для конкурентных записей
        await self._db.execute("PRAGMA journal_mode=WAL")
        # Баланс скорости и безопасности
        await self._db.execute("PRAGMA synchronous=NORMAL")
        await self._db.commit()
        logger.info("Database connected (WAL mode)")
    
    async def close(self):
        """Закрыть соединение."""
        if self._db:
            await self._db.close()
            self._db = None
            logger.info("Database closed")
    
    @property
    def connection(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._db
