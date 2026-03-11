# LangGraph Sandbox

## Prerequisites

### PostgreSQL

A PostgreSQL instance is used to persist agent memory. Run it with Docker:

```bash
docker run -p 5432:5432 -e POSTGRES_PASSWORD=password -d postgres
```
