# Alembic Cheat Sheet

**🐳 Docker Users:**
- **Manual:** Prefix commands with `docker compose exec api`
- **Easy Mode:** Use the Makefile commands (requires the file below).

## Command Reference

| Action               | Local (venv)                               | Docker (manual)                                                    | Makefile (easy)            |
| -------------------- | ------------------------------------------ | ------------------------------------------------------------------ | -------------------------- |
| **Create migration** | `alembic revision --autogenerate -m "msg"` | `docker compose exec api alembic revision --autogenerate -m "msg"` | `make migration msg="msg"` |
| **Apply all**        | `alembic upgrade head`                     | `docker compose exec api alembic upgrade head`                     | `make migrate`             |
| **Rollback last**    | `alembic downgrade -1`                     | `docker compose exec api alembic downgrade -1`                     | `make rollback`            |
| **Rollback to rev**  | `alembic downgrade <rev>`                  | `docker compose exec api alembic downgrade <rev>`                  | `make downgrade rev=<rev>` |
| **Current rev**      | `alembic current`                          | `docker compose exec api alembic current`                          | `make current`             |
| **History**          | `alembic history`                          | `docker compose exec api alembic history`                          | `make history`             |
