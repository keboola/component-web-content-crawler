FROM selenium/standalone-chrome:latest
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /code
COPY pyproject.toml .
COPY uv.lock .

RUN uv sync --all-groups --frozen

COPY . /code/

WORKDIR /code/

CMD ["uv", "run", "python3", "-u", "/code/src/component.py"]
