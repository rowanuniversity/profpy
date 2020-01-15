FROM rowanuniversity/meinheld-gunicorn-docker-interactive
LABEL maintainer="Rowan University <support@rowan.edu>"

## Set up directory structure
RUN mkdir -p /opt/rowan/dependencies
RUN mkdir -p /tmp/essays/
WORKDIR /opt/rowan/dependencies

## Updates and Dependencies
RUN apt-get update && apt-get install libaio1 && apt-get install tzdata

## Get Oracle InstantClient from local server
RUN curl https://nsscdn.rowan.edu/public/asa/docker/oracle/instantclient-basiclite-linux.x64-18.5.0.0.0dbru.zip -o "oracle-instantclient-basic.zip"

## Install InstantClient
## cribbed from https://github.com/asg1612/alpine-oracle-instantclient/blob/master/Dockerfile
RUN unzip ./oracle-instantclient-basic.zip && \
    mv ./instantclient_18_5 /usr/lib/ && \
    rm ./oracle-instantclient-basic.zip && \
    ln /usr/lib/instantclient_18_5/libclntsh.so.18.1 /usr/lib/libclntsh.so && \
    ln /usr/lib/instantclient_18_5/libocci.so.18.1 /usr/lib/libocci.so && \
    ln /usr/lib/instantclient_18_5/libnnz18.so /usr/lib/libnnz18.so

ENV ORACLE_HOME /usr/lib/instantclient_18_5
ENV ORACLE_BASE /usr/lib/instantclient_18_5
ENV LD_LIBRARY_PATH /usr/lib/instantclient_18_5
ENV PATH $PATH:$ORACLE_HOME

ENV TNS_ADMIN $ORACLE_HOME/network/admin
RUN mkdir -p $TNS_ADMIN
ADD https://nsscdn.rowan.edu/public/asa/docker/oracle/sqlnet.ora $TNS_ADMIN
ADD https://nsscdn.rowan.edu/public/asa/docker/oracle/ldap.ora $TNS_ADMIN

## Install Python dependencies
ADD requirements.txt .
RUN pip install -r requirements.txt
HEALTHCHECK --interval=2m --timeout=3s CMD curl -f http://127.0.0.1/ || exit 1