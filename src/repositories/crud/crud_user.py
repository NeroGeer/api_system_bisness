from fastapi import HTTPException
from sqlalchemy import select

from src.core.security import hash_password as hsp
from src.database.config import settings
from src.database.database import SessionDep
from src.logger.logger import logger
from src.models.model_team import Team, TeamMember
from src.models.model_user import Role, User
from src.scheme.schemas_team import InviteTeamSchema, TeamRole
from src.scheme.schemas_user import CreateUserScheme, UpdateUserScheme


async def get_user_by_id(session: SessionDep, user_id) -> User | None:
    """
    Author: NeroGeer
    GitHub: https://github.com/NeroGeer
    License: MIT

    Fetch user by ID.

    Args:
        session: DB session
        user_id: user identifier

    Returns:
        User | None
    """
    logger.info(f"Fetching user by ID: {user_id}")
    stmt = select(User).where(User.id == user_id)

    result = await session.scalar(stmt)
    if result:
        logger.debug(f"User found: {result.id} - {result.email}")
    else:
        logger.warning(f"No user found with ID: {user_id}")
    return result


async def get_user_by_email(session: SessionDep, email) -> User | None:
    """
    Fetch user by email.

    Args:
        session: DB session
        email: user email

    Returns:
        User | None
    """
    logger.info(f"Fetching user by email: {email}")
    stmt = select(User).where(User.email == email)

    result = await session.scalar(stmt)
    if result:
        logger.debug(f"User found: {result.id} - {result.email}")
    else:
        logger.warning(f"No user found with email: {email}")
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

    role = await session.scalar(
        select(Role).where(Role.id == settings.app.default_role_id)
    )

    new_user = User(
        **user_create.model_dump(exclude={"password", "roles"}),
        hashed_password=hashed_password,
        roles=[role],
    )

    session.add(new_user)

    await session.commit()
    await session.refresh(new_user)

    logger.debug(f"New user created with ID: {new_user.id}")

    return new_user


async def update_user(
    session: SessionDep, current_user: User, update_data: UpdateUserScheme
) -> User:
    """
    Update current user data.

    Args:
        session: DB session
        current_user: authenticated user
        update_data: update payload

    Returns:
        User
    """
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
    """
    Delete current user.

    Args:
        session: DB session
        current_user: user to delete
    """
    logger.warning(f"Deleting user: id={current_user.id}")
    await session.delete(current_user)
    await session.commit()
    logger.info(f"User deleted: id={current_user.id}")


async def user_team_invite_by_code(
    session: SessionDep, data: InviteTeamSchema, current_user: User
):
    """
    Join a team via invite code.

    Args:
        session: DB session
        data: invite schema
        current_user: authenticated user

    Returns:
        Team
    """

    logger.info(f"User joining team via invite code: user_id={current_user.id}")
    result = await session.execute(
        select(Team).where(Team.invite_code == data.invite_code)
    )
    team = result.scalar_one_or_none()

    if not team:
        logger.warning(f"Invalid invite code used: user_id={current_user.id}")
        raise HTTPException(status_code=404, detail="Team not found")

    existing_member = await session.execute(
        select(TeamMember).where(
            TeamMember.user_id == current_user.id, TeamMember.team_id == team.id
        )
    )

    if existing_member.scalar_one_or_none():
        logger.warning(
            f"User already in team: user_id={current_user.id}, team_id={team.id}"
        )
        raise HTTPException(status_code=204, detail="the member is on a team")

    team_member = TeamMember(
        user_id=current_user.id, team_id=team.id, role=TeamRole.employee
    )

    session.add(team_member)
    await session.commit()

    logger.info(f"User joined team: user_id={current_user.id}, team_id={team.id}")

    return team
