FROM python:3.7-slim

LABEL maintainer="Ladybug Tools" email="info@ladybug.tools"

ENV HOMEDIR='/home/ladybugbot'
ENV PATH="${HOMEDIR}/.local/bin:${PATH}"
ENV LIBRARYDIR="${HOMEDIR}/lib"
ENV RUNDIR="${HOMEDIR}/run"

RUN apt-get update \
    && apt-get -y install --no-install-recommends git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN adduser ladybugbot --uid 1000 --disabled-password --gecos ""
USER ladybugbot
WORKDIR ${HOMEDIR}
RUN mkdir ladybug_tools && touch ladybug_tools/config.json

# Install ladybug cli
COPY ladybug ${LIBRARYDIR}/ladybug
COPY .git ${LIBRARYDIR}/.git
COPY setup.py ${LIBRARYDIR}
COPY setup.cfg ${LIBRARYDIR}
COPY requirements.txt ${LIBRARYDIR}
COPY README.md ${LIBRARYDIR}
COPY LICENSE ${LIBRARYDIR}

USER root
RUN pip3 install --no-cache-dir setuptools wheel\
    && pip3 install --no-cache-dir ${LIBRARYDIR} \
    && apt-get -y --purge remove git \
    && apt-get -y clean \
    && apt-get -y autoremove \
    && rm -rf ${LIBRARYDIR}/.git

USER ladybugbot
# Set up working directory
RUN mkdir -p ${RUNDIR}/simulation
WORKDIR ${RUNDIR}
