# Docker Commands Reference

| Category | Purpose | Command |
|----------|---------|---------|
| **Lifecycle** | Start services | `docker compose up -d` |
| | Start + rebuild images | `docker compose up -d --build` |
| | Stop services (keep data) | `docker compose stop` |
| | Stop & remove containers | `docker compose down` |
| | Stop & remove containers + volumes (⚠️ data loss) | `docker compose down -v` |
| **Status** | List running containers | `docker ps` |
| | List all containers | `docker ps -a` |
| | List images | `docker images` |
| | Show compose services | `docker compose ps` |
| **Logs** | View service logs | `docker compose logs api` |
| | Tail logs | `docker compose logs api --tail 100` |
| | Follow logs | `docker compose logs -f api` |
| **Exec** | Shell into container | `docker compose exec api sh` |
| | Run command in container | `docker compose exec api <cmd>` |
| **Restart** | Restart service | `docker compose restart api` |
| | Restart all services | `docker compose restart` |
| **Cleanup** | Remove stopped containers | `docker container prune` |
| | Remove unused images | `docker image prune` |
| | Remove unused volumes | `docker volume prune` |
| **Build** | Build images | `docker compose build` |
| **Inspect** | Inspect container | `docker inspect smartvault-api` |
| **Networking** | List networks | `docker network ls` |
| | Inspect network | `docker network inspect <network>` |
| **Exit** | Stop all running containers | `docker stop $(docker ps -q)` |


| Goal                       | Command      |
| -------------------------- | ------------ |
| Start dev environment      | `make dev`   |
| Tail API logs              | `make logs`  |
| Run tests                  | `make test`  |
| Open Postgres shell        | `make psql`  |
| Open Redis CLI             | `make redis` |
| Stop services              | `make stop`  |
| Full teardown              | `make down`  |
| Dev reset (⚠️ destructive) | `make reset` |
