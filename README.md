# LangGraph Sandbox

## Prerequisites

### PostgreSQL

A PostgreSQL instance is used to persist agent memory. Run it with Docker:

```bash
docker run -d --name postgres-langgraph \
    -p 5432:5432 \
    -e POSTGRES_PASSWORD=password \
    -v postgres_langgraph:/var/lib/postgresql/data \
    postgres
```

Once already created, you can start it with:
```bash
docker start postgres-langgraph
```
