FROM python:3.7.1-slim
ENV PYTHONIOENCODING utf-8

COPY . /code/

# install gcc to be able to build packages - e.g. required by regex, dateparser, also required for pandas
RUN apt-get update && apt-get install -y build-essential

RUN pip install flake8
# process dependency links to install kds-team.keboola-util library
RUN pip install --process-dependency-links -r /code/requirements.txt

WORKDIR /code/


CMD ["python", "-u", "/code/src/component.py"]
