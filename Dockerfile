FROM python:3.7

LABEL maintainer="Ladybug Tools" email="info@ladybug.tools"

# Create non-root user
RUN adduser ladybugbot --uid 1000
USER ladybugbot
WORKDIR /home/ladybugbot
RUN mkdir ladybug_tools && touch ladybug_tools/config.json


# Install ladybug cli
ENV PATH="/home/ladybugbot/.local/bin:${PATH}"
COPY . ladybug
RUN pip3 install setuptools wheel\
    && pip3 install ./ladybug

# Set up working directory
RUN mkdir -p /home/ladybugbot/run/simulation
WORKDIR /home/ladybugbot/run
