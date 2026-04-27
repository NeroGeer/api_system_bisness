from src.core.context.base_context import BaseContext
from src.logger.logger import logger
from src.models.model_team import Team
from src.scheme.schemas_admin import AdminTeamCrateSchema


async def create_team(ctx: BaseContext, data: AdminTeamCrateSchema) -> Team:
    """
    Author: NeroGeer
    GitHub: https://github.com/NeroGeer
    License: MIT

    Creates a new team in the system.

    Args:
        ctx: BaseContext
        ctx.session: DB session
        data (AdminTeamCrateSchema): Input data for team creation.

    Returns:
        Team: Created team instance.

    Raises:
        IntegrityError: If team name or invite code violates uniqueness constraints.
    """
    ctx.require_permission(permission="admin.panel.access")

    logger.info(f"Creating new team: {data.name}")
    new_team = Team(**data.model_dump())

    ctx.session.add(new_team)
    await ctx.session.commit()
    await ctx.session.refresh(new_team)

    logger.debug(f"New team created with ID: {new_team.id}")

    return new_team
