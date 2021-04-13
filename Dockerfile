FROM binkhq/python:3.9

WORKDIR /app
ADD . .

RUN pip --no-cache install pipenv && \
    pipenv install --system --deploy --ignore-pipfile
