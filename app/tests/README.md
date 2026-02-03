# 🧪 Tests in Docker — Command Cheat Sheet
| Goal                                     | Docker Command                                                                             | Makefile    |
| ---------------------------------------- | ------------------------------------------------------------------------------------------ | ----------- |
| Run all tests (quiet)                    | `docker compose exec api pytest -q`                                                        | `make test` |
| Run all tests (verbose)                  | `docker compose exec api pytest -vv`                                                       | `-`         |
| Run tests with output (show prints/logs) | `docker compose exec api pytest -s`                                                        | `-`         |
| Run a single test file                   | `docker compose exec api pytest app/tests/api/test_create_user.py -q`                      | `-`         |
| Run a single test by keyword             | `docker compose exec api pytest -k "create_user" -q`                                       | `-`         |
| Run only API tests                       | `docker compose exec api pytest app/tests/api -q`                                          | `-`         |
| Run only application/unit tests          | `docker compose exec api pytest app/tests/application -q`                                  | `-`         |
| Stop on first failure                    | `docker compose exec api pytest -x`                                                        | `-`         |
| Re-run last failures                     | `docker compose exec api pytest --lf -q`                                                   | `-`         |
| Show slowest tests                       | `docker compose exec api pytest --durations=10`                                            | `-`         |
| Run with warnings shown                  | `docker compose exec api pytest -q -W default`                                             | `-`         |
| Run specific test function               | `docker compose exec api pytest app/tests/api/test_create_user.py::test_post_users_201 -q` | `-`         |
| Open a shell in api container            | `docker compose exec api sh`                                                               | `-`         |
| Tail API logs while testing              | `docker compose logs -f api`                                                               | `make logs` |

