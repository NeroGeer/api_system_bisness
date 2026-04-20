from src.database.database import SessionDep
from src.logger.logger import logger
from src.models.model_team import Team
from src.scheme.schemas_admin import AdminTeamCrateSchema


async def create_team(session: SessionDep, data: AdminTeamCrateSchema) -> Team:
    """
    Author: NeroGeer
    GitHub: https://github.com/NeroGeer
    License: MIT

    Creates a new team in the system.

    Args:
        session (SessionDep): Database session.
        data (AdminTeamCrateSchema): Input data for team creation.

    Returns:
        Team: Created team instance.

    Raises:
        IntegrityError: If team name or invite code violates uniqueness constraints.
    """
    logger.info(f"Creating new team: {data.name}")
    new_team = Team(**data.model_dump())

    session.add(new_team)
    await session.commit()
    await session.refresh(new_team)

    logger.debug(f"New team created with ID: {new_team.id}")

    return new_team
