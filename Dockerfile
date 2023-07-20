FROM python:3.11-slim-bookworm

LABEL MAINTAINER="Chris Reinking (chris [a][t] reinking.me)"

ENV GROUP_ID=1000 \
    USER_ID=1000 \
    PYTHONUNBUFFERED=1

WORKDIR /tmp/

ADD . /tmp/
RUN pip install -r requirements.txt

CMD ["python3", "monitor.py"]