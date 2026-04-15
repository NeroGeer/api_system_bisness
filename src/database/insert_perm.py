from sqlalchemy import insert
import src.core.models.model_user.models as md
from src.core.config import BASE_USER_ROLE_NAME


roles_data = [
    {"id": 1, "name": "admin"},
    {"id": 2, "name": BASE_USER_ROLE_NAME},
]

permissions_data = [
    {"id": 1, "name": "admin.panel.access"},
    {"id": 2, "name": "user.create"},
    {"id": 3, "name": "user.view"},
    {"id": 4, "name": "profile.edit"},
]

role_permissions_data = [
    # admin → 2 permissions
    {"role_id": 1, "permission_id": 1},  # admin.panel.access
    {"role_id": 1, "permission_id": 2},  # user.create

    # user → 2 permissions
    {"role_id": 2, "permission_id": 3},  # user.view
    {"role_id": 2, "permission_id": 4},  # profile.edit
]


user_roles_data = [
    {"user_id": 1, "role_id": 1},  # user 1 → admin
    {"user_id": 2, "role_id": 2},  # user 2 → user
]


async def insert_rbac_data(conn):
    await conn.execute(insert(md.Role), roles_data)
    await conn.execute(insert(md.Permission), permissions_data)
    await conn.execute(insert(md.role_permissions), role_permissions_data)
    await conn.execute(insert(md.user_roles), user_roles_data)