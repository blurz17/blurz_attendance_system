import pytest
from core.db.models import SystemAdmin
from sqlmodel import SQLModel

def test_system_admin_metadata():
    print(f"\nTables in metadata: {list(SQLModel.metadata.tables.keys())}")
    assert "system_admins" in SQLModel.metadata.tables
