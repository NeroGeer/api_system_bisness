from typing import Iterable

from src.exceptions import exceptions as c_exp
from src.logger.logger import logger
from src.scheme.schemas_team import TeamRole


class ContextService:
    def __init__(self, repo, context=None):
        self.repo = repo
        self.ctx = context

    async def get_team(self, team_id: int):
        """
        Author: NeroGeer
        GitHub: https://github.com/NeroGeer
        License: MIT

        Returns:
            Team: Team info
        """
        result = await self.repo.get_team(team_id=team_id)
        if not result:
            logger.warning(f"Team no found with ID: {team_id}")
            raise c_exp.TeamNotFoundError()
        return result

    async def has_team_role(
            self, user_id: int, team_id: int, roles: Iterable[TeamRole]
    ) -> bool:
        """
        Checks whether a user has one of the required roles in a specific team.

        Returns:
            bool: True if user has matching role, otherwise False.
        """

        logger.debug(
            f"Checking team role: user_id={user_id}, team_id={team_id}, required_roles={[r.name for r in roles]}"
        )
        role = await self.repo.get_team_role(user_id=user_id, team_id=team_id)
        if role is None:
            logger.warning(f"No team role found: user_id={user_id}, team_id={team_id}")
            raise c_exp.TeamRoleNotFoundError()

        return TeamRole(role) in roles

    async def check_executor(self, task_id: int, team_id: int, user_id: int) -> bool:
        return bool(await self.repo.check_executor(user_id=user_id, team_id=team_id, task_id=task_id))