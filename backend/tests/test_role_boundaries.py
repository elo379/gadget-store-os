from dataclasses import dataclass


@dataclass
class RoleCase:
    role: str
    is_owner: bool
    expected_admin_access: bool


def role_has_admin_access(case: RoleCase) -> bool:
    return case.is_owner or case.role.lower() in {"owner", "manager"}


def test_owner_has_admin_access():
    case = RoleCase("owner", True, True)
    assert role_has_admin_access(case) is True


def test_manager_has_admin_access():
    case = RoleCase("manager", False, True)
    assert role_has_admin_access(case) is True


def test_staff_does_not_have_admin_access():
    case = RoleCase("staff", False, False)
    assert role_has_admin_access(case) is False
