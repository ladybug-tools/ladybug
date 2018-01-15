FROM python:2.7
MAINTAINER Ladybug Tools "info@ladybug.tools"

WORKDIR /usr/local/lib/python2.7/dist-packages

# copy ladybug
COPY ./ladybug ./ladybug
