FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install flask waitress flask_cors requests flask_jwt flask_jwt_extended pyjwt
RUN pip install --upgrade flask_jwt_extended 

