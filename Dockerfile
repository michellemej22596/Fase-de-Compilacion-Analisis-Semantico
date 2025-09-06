FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

# Paquetes base
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    bash-completion \
    openjdk-17-jdk \
    fontconfig \
    fonts-dejavu-core \
    software-properties-common \
    python3-pip \
    python3-venv \
 && rm -rf /var/lib/apt/lists/*

# (Opcional) si de verdad necesitas el PPA:
# RUN add-apt-repository -y ppa:deadsnakes/ppa && apt-get update

# ANTLR
COPY antlr-4.13.1-complete.jar /usr/local/lib/antlr-4.13.1-complete.jar
COPY ./commands/antlr /usr/local/bin/antlr
RUN chmod +x /usr/local/bin/antlr
COPY ./commands/antlr /usr/bin/antlr
RUN chmod +x /usr/bin/antlr

COPY ./commands/grun /usr/local/bin/grun
RUN chmod +x /usr/local/bin/grun
COPY ./commands/grun /usr/bin/grun
RUN chmod +x /usr/bin/grun

# Copia primero lo que el script usará
COPY requirements.txt .
COPY python-venv.sh /usr/local/bin/python-venv.sh
RUN chmod +x /usr/local/bin/python-venv.sh

# Crea y prepara el venv (el script debe usar /opt/venv)
RUN /usr/local/bin/python-venv.sh

# Usa siempre el pip/python del venv
ENV PATH="/opt/venv/bin:${PATH}"

# (Si el script NO instala requirements, entonces:
# RUN pip install --upgrade pip && pip install -r requirements.txt
# )

# Usuario no root
ARG USER=appuser
ARG UID=1001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/${USER}" \
    --no-create-home \
    --uid "${UID}" \
    "${USER}"

USER ${UID}
WORKDIR /program
