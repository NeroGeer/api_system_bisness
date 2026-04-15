from src.database.database import SessionDep
from src.models.model_team import Team
from src.scheme.schemas_admin import AdminTeamCrateSchema
from src.logger.logger import logger


async def create_team(session: SessionDep, data: AdminTeamCrateSchema) -> Team:
    logger.info(f"Creating new team: {data.name}")
    new_team = Team(**data.model_dump())

    session.add(new_team)
    await session.commit()
    await session.refresh(new_team)

    logger.debug(f"New team created with ID: {new_team.id}")

    return new_team
