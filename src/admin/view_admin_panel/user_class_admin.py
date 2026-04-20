from sqladmin import ModelView
from sqladmin.filters import BooleanFilter
from starlette.requests import Request
from wtforms import PasswordField
from wtforms.validators import Optional

from src.core.security.hash_password import hash_password
from src.models.model_user import Permission, Role, User


class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"

    column_list = [
        User.id,
        User.email,
        User.is_active,
        User.roles,
    ]

    form_overrides = {"hashed_password": PasswordField}

    form_args = {
        "hashed_password": {
            "validators": [Optional()],
            "render_kw": {"placeholder": "Оставьте пустым, чтобы не менять"},
        }
    }

    column_details_exclude_list = [
        User.hashed_password,
    ]

    column_searchable_list = [
        User.email,
    ]

    column_filters = [
        BooleanFilter(User.is_active),
    ]

    def column_format(self, model, name):
        if name == "roles":
            return ", ".join(r.name for r in model.roles)

    async def on_model_change(
        self, data: dict, model: User, is_created: bool, request: Request
    ):
        password = data.get("hashed_password")

        if password:
            hashed = hash_password(password)
            model.hashed_password = hashed
            data["hashed_password"] = hashed
        elif is_created:
            raise ValueError("Password is required when creating user")
        else:

            data["hashed_password"] = model.hashed_password


class PermissionAdmin(ModelView, model=Permission):
    name = "Permission"
    name_plural = "Permissions"
    column_list = [
        Permission.id,
        Permission.name,
    ]

    column_searchable_list = [
        Permission.name,
    ]


class RoleAdmin(ModelView, model=Role):
    name = "Role"
    name_plural = "Roles"
    column_list = [
        Role.id,
        Role.name,
        Role.permissions,
    ]

    column_searchable_list = [
        Role.name,
    ]

    def column_format(self, model, name):
        if name == "permissions":
            return ", ".join(p.name for p in model.permissions)
