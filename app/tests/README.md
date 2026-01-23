# Tests Documentation

Quick reference for `app/tests` structure.

---

## Test Organization

| Folder | Tests | Coverage |
|--------|-------|----------|
| `api/` | API endpoints | Request/response validation, error handling |
| `application/` | Use cases & services | Business logic workflows |
| `domain/` | Domain layer | Models, value objects, events |

---

## Testing Strategy

**Unit Tests**: Individual component functionality  
**Integration Tests**: Component interactions  
**End-to-End Tests**: Complete workflows (API layer)

---

## Why Testing Matters

- **Reliability**: Ensures components function as expected
- **Quality Assurance**: Catches bugs before production
- **Maintainability**: Safe refactoring with confidence
- **Documentation**: Tests serve as usage examples