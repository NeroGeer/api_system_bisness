from sqlalchemy import select

from src.database.database import SessionDep
from src.models.model_tasks import Task, TaskComment


class CommentRepository:
    def __init__(self, session: SessionDep):
        self.session = session

    async def validate_task_id(self, task_id: int):
        return await self.session.get(Task, task_id)

    async def get(
        self, team_id: int, task_id: int, comment_id: int
    ):

        stmt = (
            select(TaskComment)
            .join(Task, TaskComment.task_id == Task.id)
            .where(
                TaskComment.id == comment_id,
                TaskComment.task_id == task_id,
                Task.team_id == team_id,
            )
        )

        return await self.session.scalar(stmt)

    async def get_comments(self, task_id: int, team_id: int):
        result = await self.session.execute(
            select(TaskComment)
            .join(Task, TaskComment.task_id == Task.id)
            .where(TaskComment.task_id == task_id,
                   Task.team_id == team_id)
            .order_by(TaskComment.created_at.asc())
        )
        return result.scalars().all()

    async def create(self, comment: TaskComment):
        self.session.add(comment)
        await self.session.commit()
        await self.session.refresh(comment)

    async def update(self, comment: TaskComment):
        await self.session.commit()
        await self.session.refresh(comment)

    async def delete(self, comment: TaskComment):
        await self.session.delete(comment)
        await self.session.commit()
