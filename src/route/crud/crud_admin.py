from src.database.database import SessionDep
from src.core.models.model_team.models import Team
from src.core.scheme.admin_scheme.schemas_admin import AdminTeamCrateSchema
from src.logger.logger import logger


async def create_team(session: SessionDep, data: AdminTeamCrateSchema) -> Team:
    logger.info(f"Creating new team: {data.name}")
    new_team = Team(**data.model_dump())

    session.add(new_team)
    await session.commit()
    await session.refresh(new_team)

    logger.debug(f"New team created with ID: {new_team.id}")

    return new_team
