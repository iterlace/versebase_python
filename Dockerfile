FROM python:3.11.6-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive
RUN ln -s $(which python3.11) /bin/python

RUN python3.11 -m pip install poetry==1.6.1
RUN python3.11 -m poetry config virtualenvs.create false

WORKDIR /versebase
ENV PYTHONPATH=$PYTHONPATH:/versebase
COPY src/poetry.lock src/pyproject.toml ./

# Currently there is no use of the DEBUG flag, but it can become handy in the future
ARG DEBUG=false
RUN bash -c "\
cd /versebase; \
if [ $DEBUG == 'true' ] ; \
    then python3.11 -m poetry install --with dev --no-root --verbose; \
    else python3.11 -m poetry install --no-root --verbose; \
fi"

COPY src/ ./
VOLUME /versebase

EXPOSE 8000
