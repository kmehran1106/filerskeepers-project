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

## Python version and dependencies

1. We are using `uv` to manage dependencies
2. We are using `docker` and `docker compose` to run the project
3. Python version is >=3.13
4. We are using ruff for formatting and linting
5. We are using mypy for type checking
6. We are using pytest for tests through testcontainers
7. We are using arq with redis for workers and schedulers


## Project and tests structure

1. The `filerskeepers` folder is the source directory
2. The `tests` holds all our tests and is a mirror of the source directory - if there are applicable tests
3. The `web` module has the REST Api endpoints and the corresponding tests only test the happy path
4. The other modules are tested through the services or tasks which hold the behavior details
5. Since we are using FastAPI, swagger docs are available at `http://localhost:8600/docs`


## Design philosophy

1. We have three logical modules - auth, crawler, and books
2. `auth` is responsible for creating user with tokens, and verifying tokens
3. `crawler` holds the scheduled task to crawl all books and store in metadata
4. `books` holds all book related data and methods to expose data to api
5. `crawler` task fetches books and calls another task in `books` to process it
6. This task based approach gives clean separation between modules and ensures loose coupling
7. The `web` module stores all the entrypoints
8. The `queue` module holds the application code for arq and workers
9. The `db` module holds the application code for mongo and redis
