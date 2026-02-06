from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps.common import get_db_session, running_pytest
from app.application.ports.vault_authorization_repository import VaultAuthorizationRepository
from app.application.ports.vault_repository import VaultRepository
from app.application.use_cases.add_vault_member import AddVaultMember
from app.application.use_cases.check_vault_access import CheckVaultAccess
from app.application.use_cases.list_vault_members import ListVaultMembers
from app.application.use_cases.remove_vault_member import RemoveVaultMember
from app.application.use_cases.send_unlock_command import SendUnlockCommand
from app.infrastructure.db.repositories.in_memory_vault_authorization_repository import (
    InMemoryVaultAuthorizationRepository,
)
from app.infrastructure.db.repositories.in_memory_vault_repository import InMemoryVaultRepository
from app.infrastructure.db.repositories.sqlalchemy_vault_authorization_repository import (
    SqlAlchemyVaultAuthorizationRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_vault_repository import SqlAlchemyVaultRepository

_in_memory_vault_repo = InMemoryVaultRepository()
_in_memory_vault_auth_repo = InMemoryVaultAuthorizationRepository()


def get_vault_repo(db: Session = Depends(get_db_session)) -> VaultRepository:
    if running_pytest():
        return _in_memory_vault_repo
    return SqlAlchemyVaultRepository(db)


def get_vault_auth_repo(
    db: Session = Depends(get_db_session),
) -> VaultAuthorizationRepository:
    """Get vault authorization repository."""
    if running_pytest():
        return _in_memory_vault_auth_repo
    return SqlAlchemyVaultAuthorizationRepository(db)


def get_check_vault_access_uc(
    vault_repo: VaultRepository = Depends(get_vault_repo),
    auth_repo: VaultAuthorizationRepository = Depends(get_vault_auth_repo),
) -> CheckVaultAccess:
    return CheckVaultAccess(vault_repo, auth_repo)


def get_add_vault_member_uc(
    vault_repo: VaultRepository = Depends(get_vault_repo),
    auth_repo: VaultAuthorizationRepository = Depends(get_vault_auth_repo),
) -> AddVaultMember:
    return AddVaultMember(vault_repo, auth_repo)


def get_remove_vault_member_uc(
    vault_repo: VaultRepository = Depends(get_vault_repo),
    auth_repo: VaultAuthorizationRepository = Depends(get_vault_auth_repo),
) -> RemoveVaultMember:
    return RemoveVaultMember(vault_repo, auth_repo)


def get_list_vault_members_uc(
    auth_repo: VaultAuthorizationRepository = Depends(get_vault_auth_repo),
    check_access: CheckVaultAccess = Depends(get_check_vault_access_uc),
) -> ListVaultMembers:
    return ListVaultMembers(auth_repo, check_access)


def get_send_unlock_command_uc(
    vault_repo: VaultRepository = Depends(get_vault_repo),
    check_access: CheckVaultAccess = Depends(get_check_vault_access_uc),
) -> SendUnlockCommand:
    return SendUnlockCommand(
        repo=vault_repo,
        check_access=check_access,
    )
