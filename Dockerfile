FROM python:3.9.12-bullseye AS base

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN mkdir /app
RUN mkdir /app/src
WORKDIR /app
COPY ./src ./src

CMD python3 src/QueueProcessor.py

