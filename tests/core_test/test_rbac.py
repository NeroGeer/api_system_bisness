import pytest

from src.core.security.rbac import has_role, has_permission
from src.scheme.schemas_user import UserRole


class DummyRole:
    def __init__(self, name):
        self.name = name


class DummyUser:
    def __init__(self, roles):
        self.id = 1
        self.roles = roles


def test_has_role_true():
    user = DummyUser(roles=[DummyRole("admin")])

    result = has_role(user, [UserRole.admin])

    assert result is True


def test_has_role_false():
    user = DummyUser(roles=[DummyRole("user")])

    assert has_role(user, [UserRole.admin]) is False


def test_has_role_multiple_roles():
    user = DummyUser(roles=[DummyRole("user"), DummyRole("admin")])

    assert has_role(user, [UserRole.admin]) is True


class DummyPermission:
    def __init__(self, name):
        self.name = name


class DummyRoleWithPermissions:
    def __init__(self, permissions):
        self.permissions = permissions


class DummyUserWithPermissions:
    def __init__(self, roles):
        self.id = 1
        self.roles = roles


def test_has_permission_true():
    user = DummyUserWithPermissions(
        roles=[
            DummyRoleWithPermissions(
                permissions=[DummyPermission("task_edit")]
            )
        ]
    )

    assert has_permission(user, "task_edit") is True


def test_has_permission_false():
    user = DummyUserWithPermissions(
        roles=[
            DummyRoleWithPermissions(
                permissions=[DummyPermission("task_view")]
            )
        ]
    )

    assert has_permission(user, "task_edit") is False


def test_has_permission_multiple_roles():
    user = DummyUserWithPermissions(
        roles=[
            DummyRoleWithPermissions(
                permissions=[DummyPermission("task_view")]
            ),
            DummyRoleWithPermissions(
                permissions=[DummyPermission("task_edit")]
            )
        ]
    )

    assert has_permission(user, "task_edit") is True