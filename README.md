# Filerskeepers - Backend for Project

## Setup

1. The first thing to do is to clone the repository:

```shell
$ git clone https://github.com/kmehran1106/filerskeepers-project.git
```

2. Commands to setup local development
```shell
$ uv pip install -e .
$ uv sync
$ docker compose -f docker/docker-compose.yml up --build -d
```

3. Commands for local development
```shell
$ docker exec -it filerskeepers-app /bin/bash  # to attach to shell
$ uv run pytest tests -svv  # to run tests
$ ./local/autoformat.sh  # ruff formatter
$ ./local/static_analysis.sh   # mypy + ruff
```

