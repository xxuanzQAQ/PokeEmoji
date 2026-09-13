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

# 统计表是否已确认存在：插件热重载不会重跑框架的 create_all，首次读写前自己补一次
_stat_table_ensured = False


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
    @with_read_session
    async def get_character(
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
    @with_session
    async def set_character(
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
    async def ensure_table(cls) -> None:
        """首次读写前确保表存在。

        框架的 create_all 在 core 启动时跑，插件单独热重载不会重跑；这里做一次
        针对性建表，让「更新完插件没重启 core」也能照常统计。
        """
        global _stat_table_ensured
        if _stat_table_ensured:
            return
        try:
            from gsuid_core.utils.database.base_models import engine

            async with engine.begin() as conn:
                # SQLModel 以小写类名为表名；显式写死绕开 stub 对 __tablename__ 的噪音
                await conn.run_sync(
                    cls.metadata.create_all,
                    tables=[cls.metadata.tables["pokeemojistat"]],
                    checkfirst=True,
                )
        except Exception as exc:
            logger.warning(f"[PokeEmoji] 戳一戳统计表检查失败: {exc}")
        _stat_table_ensured = True

    @classmethod
    async def add_count(cls, bot_id: str, character: str, delta: int = 1) -> None:
        """给某个角色的计数 +delta；表建好后再进会话，避免在会话里做 DDL。"""
        await cls.ensure_table()
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
        await cls.ensure_table()
        return await cls._get_counters()

    @classmethod
    @with_read_session
    async def _get_counters(cls, session: AsyncSession) -> list[tuple[str, int]]:
        result = await session.execute(select(cls.character, cls.count))
        return [(str(character or ""), int(count or 0)) for character, count in result.all()]
