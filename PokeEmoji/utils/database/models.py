from sqlmodel import Field, col, select
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncSession

from gsuid_core.utils.database.base_models import (
    BaseBotIDModel,
    with_session,
    with_read_session,
)


class PokeEmojiSetting(BaseBotIDModel, table=True):
    """按会话保存的戳一戳表情筛选，scope_id 形如 group_123 / user_456。"""

    __table_args__ = (
        UniqueConstraint("bot_id", "scope_id", name="ux_pokeemoji_setting_scope"),
        {"extend_existing": True},
    )

    scope_id: str = Field(default="", title="会话")
    filter_key: str = Field(default="", title="筛选")

    @classmethod
    @with_read_session
    async def get_filter(
        cls,
        session: AsyncSession,
        bot_id: str,
        scope_id: str,
    ) -> str:
        stmt = select(cls).where(col(cls.bot_id) == bot_id).where(col(cls.scope_id) == scope_id)
        result = await session.execute(stmt)
        row = result.scalars().first()
        return row.filter_key if row else ""

    @classmethod
    @with_session
    async def set_filter(
        cls,
        session: AsyncSession,
        bot_id: str,
        scope_id: str,
        filter_key: str,
    ) -> None:
        stmt = select(cls).where(col(cls.bot_id) == bot_id).where(col(cls.scope_id) == scope_id)
        result = await session.execute(stmt)
        row = result.scalars().first()
        if row is None:
            session.add(cls(bot_id=bot_id, scope_id=scope_id, filter_key=filter_key))
        else:
            row.filter_key = filter_key
