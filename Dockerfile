FROM ubuntu:16.04

MAINTAINER Joel David Hernandez Cruz <jdavidhc1710@gmail.com>

RUN apt-get update -y && \
    apt-get install -y python-pip python-dev

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT [ "python" ]

CMD [ "main.py" ]