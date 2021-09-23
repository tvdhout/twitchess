FROM python:3.9

WORKDIR /app
ADD requirements.txt /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ADD . /app

CMD ["uwsgi", "app.ini"]
