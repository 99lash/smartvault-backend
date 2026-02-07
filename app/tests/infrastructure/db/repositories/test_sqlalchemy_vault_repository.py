import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.infrastructure.db.models.base import Base
from app.infrastructure.db.models.vault_orm import VaultORM
from app.infrastructure.db.repositories.sqlalchemy_vault_repository import SqlAlchemyVaultRepository, InvalidVaultStatusError
from app.domain.value_objects.vault_status import VaultStatus

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_get_by_id_invalid_status_raises_error(db_session):
    # Insert a row with an invalid status directly
    invalid_status = "NOT_A_STATUS"
    vault_id = "v1"
    db_session.add(VaultORM(
        id=vault_id,
        owner_id="u1",
        hardware_uuid="hw1",
        vault_name="My Vault",
        status=invalid_status
    ))
    db_session.commit()

    repo = SqlAlchemyVaultRepository(db_session)
    
    with pytest.raises(InvalidVaultStatusError) as excinfo:
        repo.get_by_id(vault_id)
    
    assert "Invalid status 'NOT_A_STATUS' for vault 'v1'" in str(excinfo.value)
    assert excinfo.value.vault_id == vault_id
    assert excinfo.value.invalid_status == invalid_status

def test_get_by_hardware_uuid_invalid_status_raises_error(db_session):
    invalid_status = "NOT_A_STATUS"
    hw_uuid = "hw1"
    db_session.add(VaultORM(
        id="v1",
        owner_id="u1",
        hardware_uuid=hw_uuid,
        vault_name="My Vault",
        status=invalid_status
    ))
    db_session.commit()

    repo = SqlAlchemyVaultRepository(db_session)
    
    with pytest.raises(InvalidVaultStatusError):
        repo.get_by_hardware_uuid(hw_uuid)

def test_get_by_id_valid_status(db_session):
    vault_id = "v1"
    db_session.add(VaultORM(
        id=vault_id,
        owner_id="u1",
        hardware_uuid="hw1",
        vault_name="My Vault",
        status="LOCKED"
    ))
    db_session.commit()

    repo = SqlAlchemyVaultRepository(db_session)
    vault = repo.get_by_id(vault_id)
    
    assert vault.status == VaultStatus.LOCKED