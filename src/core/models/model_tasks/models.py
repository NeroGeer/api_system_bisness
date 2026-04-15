from datetime import datetime, UTC
from typing import List

from sqlalchemy import ForeignKey, String, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.model_base import Base
from src.core.scheme.scheme_task.schemas_task import StatusTask


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    executor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[StatusTask] = mapped_column(
        Enum(StatusTask),
        nullable=False,
    )

    grade: Mapped[int] = mapped_column(default=None, description='Grade Complete by task')
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    close_date: Mapped[datetime] = mapped_column(DateTime, nullable=True, default=None)
    comment: Mapped[List["TaskComment"]] = relationship(back_populates='task', cascade='all, delete-orphan',
                                                        lazy="selectin")


class TaskComment(Base):
    __tablename__ = "task_comments"
    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))

    text: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))

    task: Mapped["Task"] = relationship(back_populates='comment', lazy="selectin")
