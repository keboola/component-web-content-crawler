FROM python:3.7.1
ENV PYTHONIOENCODING utf-8

COPY . /code/

# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

## install chrome webdriver
RUN wget https://chromedriver.storage.googleapis.com/73.0.3683.20/chromedriver_linux64.zip
RUN apt-get install unzip
RUN unzip chromedriver_linux64.zip
RUN mv chromedriver /usr/local/bin/
RUN chown root:root /usr/local/bin/
RUN chmod 755 /usr/local/bin/chromedriver

RUN apt-get install -y xvfb
# set display port to avoid crash
ENV DISPLAY=:99

RUN pip3 install pyvirtualdisplay

# COPY to code
COPY . /code/

# set display port to avoid crash
ENV DISPLAY=:99

RUN pip3 install flake8
# process dependency links to install kds-team.keboola-util library
RUN pip3 install -r /code/requirements.txt


WORKDIR /code/


CMD ["python3", "-u", "/code/src/component.py"]
