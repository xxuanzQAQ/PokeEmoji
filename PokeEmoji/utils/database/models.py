from sqlmodel import Field, col, select
from sqlalchemy import Column, String, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncSession

from gsuid_core.utils.database.base_models import (
    BaseBotIDModel,
    with_session,
    with_read_session,
)


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
