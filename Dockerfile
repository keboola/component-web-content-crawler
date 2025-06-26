FROM selenium/standalone-chrome:latest
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# chown selenium base image's cache & venv directory so that uv can install packages there
USER root
RUN chown 1000:1000 /home/seluser/.cache
RUN chown 1000:1000 /opt/venv

RUN mkdir /userdata
RUN chown 1000:1000 /userdata

WORKDIR /code
COPY pyproject.toml .
COPY uv.lock .

RUN uv sync --all-groups --frozen --active

COPY scripts/ scripts
COPY src/ src
COPY tests/ tests
COPY deploy.sh .
COPY flake8.cfg .

CMD ["python3", "-u", "src/component.py"]
