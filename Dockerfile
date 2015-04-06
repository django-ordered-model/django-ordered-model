FROM python:2.7
WORKDIR /code
ADD requirements.txt /code/requirements.txt
RUN pip install -r requirements.txt
ADD . /code
