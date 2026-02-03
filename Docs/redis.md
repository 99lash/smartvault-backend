# Redis Command Cheat Sheet
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
