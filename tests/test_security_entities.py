from application.security.access_service import AccessService
from application.security.history_service import HistoryService
from domain.security.access_scope import AccessScope
from domain.security.default_roles import build_default_roles
from domain.security.permission import Permission
from domain.security.role_name import RoleName
from domain.security.user import User


def test_default_roles_exist():
    roles = build_default_roles()
    assert len(roles) >= 6


def test_direction_has_sensitive_history_permission():
    roles = build_default_roles()
    direction = next(role for role in roles if role.name == RoleName.DIRECTION)
    assert Permission.READ_SENSITIVE_HISTORY in direction.permissions


def test_access_service_checks_permission_and_group_scope():
    roles = build_default_roles()
    rh = next(role for role in roles if role.name == RoleName.RH)
    user = User(username="rh1", display_name="RH 1", role_ids=[rh.id])
    service = AccessService()
    assert service.user_has_permission(user=user, roles=roles, permission=Permission.READ_CONTRACTS) is True

    scope = AccessScope(user_id=user.id, max_group_number=3)
    assert service.can_access_group(scope=scope, group_number=3) is True
    assert service.can_access_group(scope=scope, group_number=4) is False


def test_history_service_records_sensitive_event():
    service = HistoryService()
    event = service.record_event(
        user_id="user-1",
        action_code="READ_CONTRACT",
        object_type="contract",
        object_id="contract-1",
        screen_code="contract_control",
        message="Consultation d'un contrat sensible",
    )
    assert event.user_id == "user-1"
    assert event.object_type == "contract"
