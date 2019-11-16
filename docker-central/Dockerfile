FROM python:3.6-stretch

WORKDIR /usr/src/screen-central

RUN apt-get update && apt-get install -y \
  unixodbc-dev \
  freetds-dev \
  freetds-bin \
  tdsodbc

COPY requeriments.txt ./
RUN pip3 install --no-cache-dir -r requeriments.txt

CMD [ "python3", "-u", "./run.py" ]
