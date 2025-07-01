FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt -y update
RUN apt install -y chromium chromium-driver

# Create user to correctly set the $HOME env variable and create the home folder
ARG USERNAME=keboola
RUN adduser --uid 1000 --disabled-password ${USERNAME}

USER 1000:1000

WORKDIR /code
COPY pyproject.toml .
COPY uv.lock .

RUN uv sync --all-groups --frozen

COPY scripts/ scripts
COPY src/ src
COPY tests/ tests
COPY deploy.sh .
COPY flake8.cfg .

CMD ["uv", "run", "python3", "-u", "src/component.py"]
