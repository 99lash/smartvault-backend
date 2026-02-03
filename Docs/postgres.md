# Postgres Cheat Sheet

## <img src="https://img.icons8.com/?size=100&id=38561&format=png&color=000000" alt="Search Icon" width="25" height="25">  Postgres in Docker — Command Cheat Sheet

| Purpose                                    | Docker Command                                                                                                                                | Makefile        |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| **Open interactive psql (recommended)**    | `docker compose exec postgres psql -U postgres -d smartvault`                                                                                 | `make psql`     |
| **Open interactive psql (container name)** | `docker exec -it smartvault-postgres psql -U postgres -d smartvault`                                                                          | `-`             |
| **Exit psql**                              | `\q`                                                                                                                                          | `-`             |
| **Run one SQL command**                    | `docker compose exec postgres psql -U postgres -d smartvault -c "SELECT now();"`                                                              | `-`             |
| **List databases**                         | `\l`                                                                                                                                          | `-`             |
| **Connect to database**                    | `\c smartvault`                                                                                                                               | `-`             |
| **List schemas**                           | `\dn`                                                                                                                                         | `-`             |
| **List tables**                            | `\dt`                                                                                                                                         | `-`             |
| **Describe table**                         | `\d users`                                                                                                                                    | `-`             |
| **Describe table (verbose)**               | `\d+ users`                                                                                                                                   | `-`             |
| **List indexes**                           | `\di`                                                                                                                                         | `-`             |
| **Check Alembic version**                  | `docker compose exec postgres psql -U postgres -d smartvault -c "SELECT version_num FROM alembic_version;"`                                   | `-`             |
| **List recent users**                      | `docker compose exec postgres psql -U postgres -d smartvault -c "SELECT id, email, created_at FROM users ORDER BY created_at DESC LIMIT 10;"` | `-`             |
| **Check duplicate emails**                 | `docker compose exec postgres psql -U postgres -d smartvault -c "SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1;"`      | `-`             |
| **Inspect Postgres logs**                  | `docker compose logs postgres --tail 100`                                                                                                     | `-`             |
| **Restart Postgres**                       | `docker compose restart postgres`                                                                                                             | `-`             |
| **Show Postgres version**                  | `docker compose exec postgres psql -U postgres -d smartvault -c "SELECT version();"`                                                          | `make db-info`  |
| **Reset DB (DEV ONLY)**                    | `DROP SCHEMA public CASCADE; CREATE SCHEMA public;` (via psql)                                                                                | `make db-reset` |

----
