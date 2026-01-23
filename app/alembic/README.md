# Alembic Quick Reference

## Common Commands

| Command | What It Does |
|---------|--------------|
| `alembic init alembic` | Setup: Creates config and folders |
| `alembic revision --autogenerate -m "msg"` | Creates migration from model changes |
| `alembic upgrade head` | Applies all pending migrations |
| `alembic upgrade <rev>` | Applies migrations to specific version |
| `alembic downgrade -1` | Rolls back one migration |
| `alembic downgrade base` | Rolls back all migrations |
| `alembic current` | Shows current DB version |
| `alembic history` | Lists all migrations |
| `alembic stamp head` | Marks DB as current without running migrations |

**Offline Mode**: Add `--sql > file.sql` to generate SQL instead of executing.

---

## Migration Example

### 1. Initial Model
```python
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    section = Column(String)  # Will be removed
```

### 2. Update Model (Remove Column)
```python
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    # section removed
```

### 3. Generate Migration
```bash
alembic revision --autogenerate -m "remove section"
```

**Generated File** (`versions/abc123_*.py`):
```python
def upgrade():
    op.drop_column("students", "section")

def downgrade():
    op.add_column("students", sa.Column("section", sa.String()))
```

### 4. Apply Migration
```bash
# Online (executes on DB)
alembic upgrade head

# Offline (generates SQL file)
alembic upgrade head --sql > migration.sql
```

### 5. Rollback
```bash
alembic downgrade -1  # Restores the section column
```

---

## Notes

**`script.py.mako`**: Template file for generating migration scripts. Customize it to match your project style.

**Online vs Offline**: Online executes SQL directly on DB. Offline generates SQL files for manual review/execution.