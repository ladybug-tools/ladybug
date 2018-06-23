FROM python:2.7
MAINTAINER Antoine Dao "antoine.dao@burohappold.com"

WORKDIR /usr/local/lib/python2.7/site-packages

# copy ladybug
COPY ./ladybug ./ladybug
