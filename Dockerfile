FROM python:3.7.1-slim
ENV PYTHONIOENCODING utf-8

COPY . /code/

# install gcc to be able to build packages - e.g. required by regex, dateparser, also required for pandas
RUN apt-get update && apt-get install -y build-essential

RUN pip install flake8
# process dependency links to install kds-team.keboola-util library
RUN pip install --process-dependency-links -r /code/requirements.txt

# install chrome webdriver
RUN wget https://chromedriver.storage.googleapis.com/73.0.3683.20/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip
RUN sudo mv chromedriver /usr/bin/chromedriver
RUN sudo chown root:root /usr/bin/chromedriver
RUN sudo chmod +x /usr/bin/chromedriver

WORKDIR /code/


CMD ["python", "-u", "/code/src/component.py"]
