from sqlmodel import Field, col, select, update
from sqlalchemy import Column, String, Integer, UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from gsuid_core.logger import logger
from gsuid_core.utils.database.base_models import (
    BaseBotIDModel,
    with_session,
    with_read_session,
)

# 已确认存在的表：插件热重载不会重跑框架的 create_all，首次读写前自己补一次
_ensured_tables: set[str] = set()


async def _ensure_table(model: type[BaseBotIDModel]) -> None:
    """首次读写前确保这张表存在。

    框架的 create_all 在 core 启动时跑，插件单独热重载（或更新完没重启 core）不会重跑；
    这里做一次针对性建表，避免首次命令直接撞上 `no such table`。
    """
    table_name = getattr(model, "__tablename__", model.__name__.lower())
    if table_name in _ensured_tables:
        return
    try:
        from gsuid_core.utils.database.base_models import engine

        async with engine.begin() as conn:
            await conn.run_sync(
                model.metadata.create_all,
                tables=[model.metadata.tables[table_name]],
                checkfirst=True,
            )
    except Exception as exc:
        logger.warning(f"[PokeEmoji] 数据表 {table_name} 检查失败: {exc}")
        return
    _ensured_tables.add(table_name)


class PokeEmojiSetting(BaseBotIDModel, table=True):
    """按会话保存的戳一戳角色，scope_id 形如 group_123 / user_456。"""

    __table_args__ = (
        UniqueConstraint("bot_id", "scope_id", name="ux_pokeemoji_setting_scope"),
        {"extend_existing": True},
    )

    scope_id: str = Field(default="", title="会话")
    # 沿用旧列名 filter_key：字段语义从「分类筛选」改成「角色」，但不改列名，
    # 老库升级时 CLI 建表不会补列，改列名会让已有表直接查不动。
    character: str = Field(
        default="",
        title="角色",
        sa_column=Column("filter_key", String, nullable=False, server_default=""),
    )

    @classmethod
    async def get_character(cls, bot_id: str, scope_id: str) -> str:
        await _ensure_table(cls)
        return await cls._get_character(bot_id, scope_id)

    @classmethod
    @with_read_session
    async def _get_character(
        cls,
        session: AsyncSession,
        bot_id: str,
        scope_id: str,
    ) -> str:
        stmt = select(cls).where(col(cls.bot_id) == bot_id).where(col(cls.scope_id) == scope_id)
        result = await session.execute(stmt)
        row = result.scalars().first()
        return row.character if row else ""

    @classmethod
    async def set_character(cls, bot_id: str, scope_id: str, character: str) -> None:
        await _ensure_table(cls)
        await cls._set_character(bot_id, scope_id, character)

    @classmethod
    @with_session
    async def _set_character(
        cls,
        session: AsyncSession,
        bot_id: str,
        scope_id: str,
        character: str,
    ) -> None:
        stmt = select(cls).where(col(cls.bot_id) == bot_id).where(col(cls.scope_id) == scope_id)
        result = await session.execute(stmt)
        row = result.scalars().first()
        if row is None:
            session.add(cls(bot_id=bot_id, scope_id=scope_id, character=character))
        else:
            row.character = character


class PokeEmojiStat(BaseBotIDModel, table=True):
    """按角色累加的戳一戳计数：bot_id + 角色唯一，成功回一张表情就 +1。

    只统计「真的回到了一张表情」的戳一戳：被概率、冷却拦下或取图失败的不计入。
    角色名的归一（忽略大小写与「·」一类的装饰字符）放在读取侧做，避免同一个角色
    因为写法差异被拆成多行。
    """

    __table_args__ = (
        UniqueConstraint("bot_id", "character", name="ux_pokeemoji_stat_character"),
        {"extend_existing": True},
    )

    character: str = Field(default="", title="角色")
    count: int = Field(default=0, title="戳一戳次数", sa_column=Column(Integer, nullable=False, server_default="0"))

    @classmethod
    async def add_count(cls, bot_id: str, character: str, delta: int = 1) -> None:
        """给某个角色的计数 +delta；表建好后再进会话，避免在会话里做 DDL。"""
        await _ensure_table(cls)
        await cls._add_count(bot_id, character, delta)

    @classmethod
    @with_session
    async def _add_count(
        cls,
        session: AsyncSession,
        bot_id: str,
        character: str,
        delta: int = 1,
    ) -> None:
        """给某个角色的计数 +delta，行不存在就新建。"""
        stmt = (
            update(cls)
            .where(col(cls.bot_id) == bot_id)
            .where(col(cls.character) == character)
            .values(count=col(cls.count) + delta)
        )
        result = await session.execute(stmt)
        if result.rowcount:
            return

        # 首次插入走 INSERT；并发下唯一约束可能被另一个请求抢先，冲突后回滚改成累加，
        # 免得这次戳一戳被静默吞掉。
        session.add(cls(bot_id=bot_id, character=character, count=delta))
        try:
            await session.flush()
        except IntegrityError:
            await session.rollback()
            await session.execute(stmt)

    @classmethod
    async def get_counters(cls) -> list[tuple[str, int]]:
        """全部 (角色, 次数)；跨 bot / 同一角色的写法差异交给调用方合并。"""
        await _ensure_table(cls)
        return await cls._get_counters()

    @classmethod
    @with_read_session
    async def _get_counters(cls, session: AsyncSession) -> list[tuple[str, int]]:
        result = await session.execute(select(cls.character, cls.count))
        return [(str(character or ""), int(count or 0)) for character, count in result.all()]
