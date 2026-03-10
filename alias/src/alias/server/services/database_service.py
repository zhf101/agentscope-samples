# -*- coding: utf-8 -*-
"""
数据库服务层（新手教学注释版）

职责：
1) 管理数据库引擎与会话
2) 负责迁移（升级/降级/初始化 Alembic）
3) 初始化表结构并创建首个管理员账号
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
from loguru import logger

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


from alias.server.core.config import settings
from alias.server.core.database.database_manager import DatabaseManager
from alias.server.core.database.migration_manager import MigrationManager


class DatabaseService:
    """数据库统一服务入口。"""

    def __init__(self) -> None:
        # 从全局配置读取数据库 URI。
        db_uri = settings.SQLALCHEMY_DATABASE_URI
        # SQLite 同步 URI -> 异步 URI（aiosqlite）。
        if db_uri and db_uri.startswith("sqlite:///"):
            db_uri = db_uri.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        self.db_uri = db_uri

        # DatabaseManager 负责 engine/session 的底层管理。
        self.database_manager = DatabaseManager(
            db_uri=self.db_uri,
            connection_args=settings.DB_CONNECTION_ARGS,
        )
        # 迁移配置路径（alembic.ini + alembic 脚本目录）。
        server_path = Path(__file__).parent.parent
        alembic_cfg_path = server_path / "alembic.ini"
        script_location = server_path / "alembic"

        self.migration_manager = MigrationManager(
            alembic_config_path=alembic_cfg_path,
            script_location=script_location,
            db_uri=self.db_uri,
            engine=self.database_manager.engine,
        )

    async def dispose(self) -> None:
        """Dispose database connections"""
        await self.database_manager.dispose()

    @property
    def engine(self) -> AsyncEngine:
        """Get database engine"""
        return self.database_manager.engine

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session as async context manager"""
        # 统一通过 context manager 提供会话，自动提交/回滚/关闭。
        async with self.database_manager.session() as session:
            yield session

    async def has_alembic_version_table(self) -> bool:
        """Check if alembic_version table exists and has data"""
        try:
            async with self.engine.connect() as conn:
                # 先检查表是否存在。
                result = await conn.run_sync(
                    lambda sync_conn: inspect(sync_conn).get_table_names(),
                )
                if "alembic_version" not in result:
                    logger.info("alembic_version table does not exist")
                    return False

                result = await conn.scalar(
                    text("SELECT COUNT(*) FROM alembic_version"),
                )
                if result == 0:
                    logger.info("alembic_version table exists but is empty")
                    return False

                logger.info(
                    f"alembic_version table exists with {result} row(s)",
                )
                return True

        except Exception as e:
            logger.error(f"Error checking alembic_version table: {e}")
            return False

    async def init_alembic(self) -> None:
        """Initialize alembic version control"""
        # 只有在版本表不存在/为空时才初始化。
        if not await self.has_alembic_version_table():
            logger.info("Initializing alembic version control...")
            await self.migration_manager.init_alembic_version()

    async def init_database(self) -> None:
        """Initialize database (create tables and check connection)"""
        try:
            # Check database connection first
            if not await self.database_manager.check_connection():
                raise ValueError("Database connection failed")

            # Create tables
            await self.database_manager.create_tables()
            logger.info("✅ Database initialization completed")

        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise

    async def create_migration(
        self,
        message: str,
        autogenerate: bool = True,
    ) -> bool:
        """Create new migration"""
        return await self.migration_manager.create(
            message=message,
            autogenerate=autogenerate,
        )

    async def upgrade(self, revision: str = "head") -> bool:
        """Upgrade migration with protection and logging"""
        try:
            logger.info(f"🔄 Starting database upgrade to revision: {revision}")

            # Check database connection first
            if not await self.database_manager.check_connection():
                logger.error(
                    "❌ Database connection failed, "
                    "cannot proceed with upgrade",
                )
                raise ValueError("Database connection failed")

            # Initialize alembic if needed
            await self.init_alembic()

            # Perform upgrade
            result = await self.migration_manager.upgrade(revision=revision)

            if result:
                logger.info(
                    f"✅ Database upgrade to {revision} completed successfully",
                )
            else:
                logger.warning(
                    f"⚠️ Database upgrade to {revision} returned False",
                )

            return result

        except Exception as e:
            logger.error(f"❌ Database upgrade failed: {e}")
            raise

    async def downgrade(self, steps: int = 1) -> bool:
        """Downgrade migration with protection and logging"""
        try:
            logger.info(f"🔄 Starting database downgrade by {steps} step(s)")

            # Check database connection first
            if not await self.database_manager.check_connection():
                logger.error(
                    "❌ Database connection failed, "
                    "cannot proceed with downgrade",
                )
                raise ValueError("Database connection failed")

            # Initialize alembic if needed
            await self.init_alembic()

            # Perform downgrade
            result = await self.migration_manager.downgrade(steps=steps)

            if result:
                logger.info(
                    f"✅ Database downgrade by {steps} step(s) "
                    f"completed successfully",
                )
            else:
                logger.warning(
                    f"⚠️ Database downgrade by {steps} step(s) returned False",
                )

            return result

        except Exception as e:
            logger.error(f"❌ Database downgrade failed: {e}")
            raise

    async def create_superuser(self) -> None:
        """Create the first super user based on configuration"""
        try:
            superuser_email = settings.FIRST_SUPERUSER_EMAIL
            superuser_password = settings.FIRST_SUPERUSER_PASSWORD
            superuser_username = settings.FIRST_SUPERUSER_USERNAME
            if not superuser_email and not superuser_password:
                logger.info(
                    "⚠️ FIRST_SUPERUSER_EMAIL and "
                    "FIRST_SUPERUSER_PASSWORD is not set, "
                    "skipping super user creation",
                )
                return

            if superuser_username is None:
                superuser_username = superuser_email.split("@")[0]

            logger.info("🔄 Checking for existing super user...")
            from alias.server.services.user_service import UserService

            async with self.get_session() as session:
                user_service = UserService(session=session)
                # 先按邮箱查是否已存在，避免重复创建。
                super_user = await user_service.get_user_by_email(
                    settings.FIRST_SUPERUSER_EMAIL,
                )
                if super_user:
                    logger.info(
                        f"✅ Super user already exists: "
                        f"{super_user.username} ({super_user.email})",
                    )
                else:
                    super_user = await user_service.create_user(
                        email=settings.FIRST_SUPERUSER_EMAIL,
                        username=settings.FIRST_SUPERUSER_USERNAME,
                        password=settings.FIRST_SUPERUSER_PASSWORD,
                        is_superuser=True,
                    )
                    logger.info(
                        f"✅ Super user created successfully: "
                        f"{super_user.username} ({super_user.email})",
                    )

        except Exception as e:
            logger.error(f"❌ Failed to create admin user: {e}")
            raise
