from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps.activity import get_log_activity_uc
from app.api.deps.common import get_db_session
from app.application.ports.pin_attempt_tracker import PINAttemptTracker
from app.application.ports.pin_hasher import PINHasher
from app.application.ports.vault_authorization_repository import VaultAuthorizationRepository
from app.application.ports.vault_repository import VaultRepository
from app.application.use_cases.add_vault_member import AddVaultMember
from app.application.use_cases.check_vault_access import CheckVaultAccess
from app.application.use_cases.list_vault_members import ListVaultMembers
from app.application.use_cases.list_user_vaults import ListUserVaults
from app.application.use_cases.generate_provisioning_token import GenerateProvisioningToken
from app.application.use_cases.log_activity import LogActivity
from app.application.use_cases.register_device import RegisterDevice
from app.application.use_cases.remove_vault_member import RemoveVaultMember
from app.application.use_cases.remove_vault_pin import RemoveVaultPIN
from app.application.use_cases.reset_vault import ResetVault
from app.application.use_cases.send_unlock_command import SendUnlockCommand
from app.application.use_cases.set_vault_pin import SetVaultPIN
from app.application.use_cases.unlock_vault_with_pin import UnlockVaultWithPIN
from app.infrastructure.db.repositories.sqlalchemy_activity_log_repository import (
    SqlAlchemyActivityLogRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.infrastructure.db.repositories.sqlalchemy_vault_authorization_repository import (
    SqlAlchemyVaultAuthorizationRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_vault_repository import SqlAlchemyVaultRepository
from app.infrastructure.messaging.websocket_manager import WebSocketManager
from app.infrastructure.security.pin_attempt_tracker import RedisPINAttemptTracker
from app.infrastructure.security.pin_hasher import PBKDF2PINHasher

_pin_hasher = PBKDF2PINHasher()
_pin_attempt_tracker = RedisPINAttemptTracker()
_ws_manager = WebSocketManager()


def get_vault_repo(db: Session = Depends(get_db_session)) -> VaultRepository:
    return SqlAlchemyVaultRepository(db)


def get_vault_auth_repo(
    db: Session = Depends(get_db_session),
) -> VaultAuthorizationRepository:
    return SqlAlchemyVaultAuthorizationRepository(db)


def get_check_vault_access_uc(
    vault_repo: VaultRepository = Depends(get_vault_repo),
    auth_repo: VaultAuthorizationRepository = Depends(get_vault_auth_repo),
) -> CheckVaultAccess:
    return CheckVaultAccess(vault_repo, auth_repo)


def get_add_vault_member_uc(
    vault_repo: VaultRepository = Depends(get_vault_repo),
    auth_repo: VaultAuthorizationRepository = Depends(get_vault_auth_repo),
    log_activity: LogActivity = Depends(get_log_activity_uc),  # NEW
) -> AddVaultMember:
    return AddVaultMember(vault_repo, auth_repo, log_activity)


def get_remove_vault_member_uc(
    vault_repo: VaultRepository = Depends(get_vault_repo),
    auth_repo: VaultAuthorizationRepository = Depends(get_vault_auth_repo),
    log_activity: LogActivity = Depends(get_log_activity_uc),  # NEW
) -> RemoveVaultMember:
    return RemoveVaultMember(vault_repo, auth_repo, log_activity)


def get_list_vault_members_uc(
    auth_repo: VaultAuthorizationRepository = Depends(get_vault_auth_repo),
    check_access: CheckVaultAccess = Depends(get_check_vault_access_uc),
) -> ListVaultMembers:
    return ListVaultMembers(auth_repo, check_access)


def get_list_user_vaults_uc(
    vault_repo: VaultRepository = Depends(get_vault_repo),
) -> ListUserVaults:
    return ListUserVaults(vault_repo)


def get_send_unlock_command_uc(
    vault_repo: VaultRepository = Depends(get_vault_repo),
    check_access: CheckVaultAccess = Depends(get_check_vault_access_uc),
) -> SendUnlockCommand:
    return SendUnlockCommand(
        repo=vault_repo,
        check_access=check_access,
        ws_manager=_ws_manager,
    )


def get_pin_hasher() -> PINHasher:
    return _pin_hasher


def get_pin_attempt_tracker() -> PINAttemptTracker:
    return _pin_attempt_tracker


def get_set_vault_pin_uc(
    vault_repo: VaultRepository = Depends(get_vault_repo),
    hasher: PINHasher = Depends(get_pin_hasher),
    log_activity: LogActivity = Depends(get_log_activity_uc),  # NEW
) -> SetVaultPIN:
    return SetVaultPIN(vault_repo, hasher, log_activity)


def get_remove_vault_pin_uc(
    vault_repo: VaultRepository = Depends(get_vault_repo),
    log_activity: LogActivity = Depends(get_log_activity_uc),  # NEW
) -> RemoveVaultPIN:
    return RemoveVaultPIN(vault_repo, log_activity)


def get_unlock_with_pin_uc(
    vault_repo: VaultRepository = Depends(get_vault_repo),
    hasher: PINHasher = Depends(get_pin_hasher),
    tracker: PINAttemptTracker = Depends(get_pin_attempt_tracker),
    log_activity: LogActivity = Depends(get_log_activity_uc),  # NEW
) -> UnlockVaultWithPIN:
    return UnlockVaultWithPIN(vault_repo, hasher, tracker, log_activity)


def get_user_repo(db: Session = Depends(get_db_session)) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(db)


def get_activity_log_repo(db: Session = Depends(get_db_session)) -> SqlAlchemyActivityLogRepository:
    return SqlAlchemyActivityLogRepository(db)


def get_generate_provisioning_token_uc(
    user_repo=Depends(get_user_repo),
) -> GenerateProvisioningToken:
    return GenerateProvisioningToken(user_repo)


def get_register_device_uc(
    user_repo=Depends(get_user_repo),
    vault_repo: VaultRepository = Depends(get_vault_repo),
) -> RegisterDevice:
    return RegisterDevice(user_repo, vault_repo)


def get_reset_vault_uc(
    vault_repo: VaultRepository = Depends(get_vault_repo),
    log_repo=Depends(get_activity_log_repo),
) -> ResetVault:
    return ResetVault(vault_repo, log_repo, _ws_manager)
