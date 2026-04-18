from fastapi import HTTPException
from sqlalchemy import select, exists

from src.core.security.rbac import has_role
from src.database.database import SessionDep
from src.models.model_tasks import Task
from src.models.model_team import Team
from src.models.model_user import PermissionResult
from src.repositories.task_repository import has_team_role
from src.scheme.schemas_team import TeamRole
from src.scheme.schemas_user import UserRole


async def require_admin_or_team_manager(
        session: SessionDep,
        current_user,
        team_id: int,
        team_role: set[TeamRole] | None = None,
        check_executor: bool = False,
        task_id: int | None = None,
):
    """
       Permission guard for admin, team roles or task executor access.

       This function verifies whether a user has permission to perform
       actions inside a specific team context.

       Logic:
       - checks if team exists
       - checks if user is admin
       - checks if user has required team role
       - optionally checks if user is task executor

       Args:
           session: Database session dependency.
           current_user: Authenticated user.
           team_id: Target team ID.
           team_role: Allowed team roles (default: manager).
           check_executor: Enable executor permission check.
           task_id: Required if check_executor=True.

       Returns:
           PermissionResult:
               Object containing:
               - is_admin
               - is_team_role
               - is_executor

       Raises:
           HTTPException:
               - 404 if team not found
               - 422 if task_id missing when check_executor=True
               - 403 if user has no required permissions
       """

    team_exists = await session.scalar(
        select(exists().where(Team.id == team_id))

    )
    if not team_exists:
        raise HTTPException(status_code=404, detail="Team not found")

    check_roles: set[TeamRole] = team_role if team_role is not None else {TeamRole.manager}

    is_admin = has_role(user=current_user, roles={UserRole.admin})
    is_team_role = await has_team_role(session=session, user=current_user, team_id=team_id, roles=check_roles)
    is_executor = False

    if check_executor:
        if task_id is None:
            raise HTTPException(
                status_code=422,
                detail="task_id is required when check_executor=True"
            )

        is_executor = bool(await session.scalar(
            select(exists().where(
                Task.id == task_id,
                Task.team_id == team_id,
                Task.executor_user_id == current_user.id
            )
            )
        ))

    if not (is_admin or is_team_role or is_executor):
        raise HTTPException(
            status_code=403,
            detail="No permission to perform this action. "
                   "Admin, team manager or task executor required."
        )

    return PermissionResult(
        is_admin=is_admin,
        is_team_role=is_team_role,
        is_executor=is_executor,
    )
