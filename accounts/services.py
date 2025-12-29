from accounts.models import User


def validate_user_active(user: User) -> User:
    if not user.is_active:
        raise PermissionError("Usuário inativo")
    return user


def user_has_role(user: User, role: str) -> bool:
    return user.role == role


def validate_user_organization(user: User, organization) -> User:
    if user.organization_id != getattr(organization, "id", None):
        raise PermissionError("Usuário não pertence à organização informada")
    return user


def user_is_operations(user: User) -> bool:
    return user.role == User.Roles.OPERATIONS


def user_is_academy(user: User) -> bool:
    return user.role in {User.Roles.ACADEMY_ADMIN, User.Roles.ACADEMY_STAFF}


def user_is_weighing_official(user: User) -> bool:
    return user.role == User.Roles.WEIGHING_OFFICIAL


def user_is_table_official(user: User) -> bool:
    return user.role == User.Roles.TABLE_OFFICIAL

