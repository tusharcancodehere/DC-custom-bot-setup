from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base

class UserXP(Base):
    __tablename__ = "user_xp"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_xp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_user_xp_guild_xp", "guild_id", "xp"),
    )
