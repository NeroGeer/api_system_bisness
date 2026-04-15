from sqlalchemy import select
from fastapi import HTTPException

from src.database.database import SessionDep
from src.core.config import DEFAULT_ROLE_ID
from src.core.jwt_hash import hash_password as hsp
from src.core.models.model_user.models import User, Role
from src.core.models.model_team.models import Team, TeamMember
from src.core.scheme.scheme_user.schemas_user import CreateUserScheme, UpdateUserScheme
from src.core.scheme.scheme_team.schemas_team import InviteTeamSchema
from src.logger.logger import logger


async def get_user_by_id(session: SessionDep, user_id) -> User | None:
    logger.info(f"Fetching user by ID: {user_id}")
    stmt = select(User).where(User.id == user_id)

    result = await session.scalar(stmt)
    if result:
        logger.debug(f"User found: {result.id} - {result.email}")
    else:
        logger.warning(f"No user found with ID: {user_id}")
    return result


async def get_user_by_email(session: SessionDep, data) -> User | None:
    logger.info(f"Fetching user by email: {data.email}")
    stmt = select(User).where(User.email == data.email)

    result = await session.scalar(stmt)
    if result:
        logger.debug(f"User found: {result.id} - {result.email}")
    else:
        logger.warning(f"No user found with email: {data.email}")
    return result


async def create_user(session: SessionDep, user_create: CreateUserScheme) -> User:
    """
    Create a new user.

    Args:
        session (SessionDep):
            Async SQLAlchemy session dependency.
        user_create (CreateUserScheme):
            Pydantic schema containing name and api_key.

    Returns:
        User:
            The newly created User object.
    """
    logger.info(f"Creating new user with name: {user_create.email}")
    hashed_password = hsp.hash_password(user_create.password)
    new_user = User(**user_create.model_dump(exclude={"password", "roles"}),
                    hashed_password=hashed_password,
                    roles=[Role(id=DEFAULT_ROLE_ID)])
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    logger.debug(f"New user created with ID: {new_user.id}")

    return new_user


async def update_user(session: SessionDep, current_user: User, update_data: UpdateUserScheme) -> User:
    logger.info(f"Update User: {update_data.email}")

    data = update_data.model_dump(exclude_unset=True)

    if not data:
        raise HTTPException(400, "No data to update")

    if "email" in data:
        current_user.email = data["email"]
        logger.info(f"Update User email: {update_data.email}")

    if "password" in data:
        current_user.hashed_password = hsp.hash_password(data["password"])
        logger.info(f"Update User password: {update_data.email}")

    await session.commit()
    await session.refresh(current_user)
    logger.debug(f"Update User success: {current_user.email}")
    return current_user


async def delete_user(session: SessionDep, current_user: User) -> None:
    await session.delete(current_user)
    await session.commit()


async def user_team_invite_by_code(
        session: SessionDep,
        invite_code: InviteTeamSchema,
        current_user: User
):
    result = await session.execute(select(Team).where(Team.invite_code == invite_code))
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    existing_member = await session.execute(
        select(TeamMember).where(
            TeamMember.user_id == current_user.id,
            TeamMember.team_id == team.id
        )
    )

    if existing_member.scalar_one_or_none():
        raise HTTPException(status_code=204, detail="the member is on a team")

    team_member = TeamMember(
        user_id=current_user.id,
        team_id=team.id,
        role='employee'
    )

    session.add(team_member)
    await session.commit()
    await session.refresh(current_user)

    return team
