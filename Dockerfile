FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update 
RUN apt-get install -y python3.10 python3-pip libmagic1

WORKDIR /app

COPY . .

VOLUME /app/sessions

RUN python3 -m pip install -r requirements.txt

CMD ["python3", "main.py"]