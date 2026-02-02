# Postgres and Redis Command Cheat Sheet

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
## <img src="https://img.icons8.com/?size=100&id=pHS3eRpynIRQ&format=png&color=000000" alt="Search Icon" width="25" height="25"> Redis Commands (Running Inside Docker)
| Category        | Purpose                   | Command                                      | Makefile           |
| --------------- | ------------------------- | -------------------------------------------- | ------------------ |
| **Connect**     | Open Redis CLI            | `docker compose exec redis redis-cli`        | `make redis`       |
|                 | Open CLI (container name) | `docker exec -it smartvault-redis redis-cli` | `-`                |
| **Health**      | Check Redis is alive      | `PING`                                       | `-`                |
| **Info**        | Server info               | `INFO`                                       | `make redis-info`  |
|                 | Memory usage              | `INFO memory`                                | `-`                |
|                 | Client connections        | `INFO clients`                               | `-`                |
|                 | Keyspace stats            | `INFO keyspace`                              | `-`                |
| **Keys**        | Check if key exists       | `EXISTS key`                                 | `-`                |
|                 | List keys (dev only)      | `KEYS *`                                     | `-`                |
|                 | Scan keys safely          | `SCAN 0`                                     | `-`                |
| **Values**      | Get value                 | `GET key`                                    | `-`                |
|                 | Set value                 | `SET key value`                              | `-`                |
|                 | Set with TTL              | `SET key value EX 600`                       | `-`                |
|                 | Delete key                | `DEL key`                                    | `-`                |
| **TTL**         | Get remaining TTL         | `TTL key`                                    | `-`                |
|                 | Set expiry                | `EXPIRE key 3600`                            | `-`                |
| **Counters**    | Increment counter         | `INCR key`                                   | `-`                |
|                 | Decrement counter         | `DECR key`                                   | `-`                |
| **Rate Limit**  | Increment + TTL           | `INCR key` → `EXPIRE key 3600`               | `-`                |
| **OTP Flow**    | Store OTP                 | `SET otp:user@email.com 123456 EX 600`       | `-`                |
|                 | Verify OTP                | `GET otp:user@email.com`                     | `-`                |
|                 | Remove OTP                | `DEL otp:user@email.com`                     | `-`                |
| **Maintenance** | Clear current DB          | `FLUSHDB`                                    | `make redis-flush` |
|                 | Clear all DBs             | `FLUSHALL`                                   | `-`                |
| **Persistence** | Force save                | `SAVE`                                       | `-`                |
|                 | Background save           | `BGSAVE`                                     | `-`                |
| **Config**      | View config               | `CONFIG GET *`                               | `-`                |
| **Exit**        | Exit CLI                  | `exit`                                       | `-`                |
