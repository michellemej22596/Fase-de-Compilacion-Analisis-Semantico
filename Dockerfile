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

# Copiar todo el proyecto al contenedor
COPY . /program

# Copia primero lo que el script usará
COPY requirements.txt .
COPY python-venv.sh /usr/local/bin/python-venv.sh
RUN chmod +x /usr/local/bin/python-venv.sh

# Crear y preparar el venv (el script debe usar /opt/venv)
RUN /usr/local/bin/python-venv.sh

# Usa siempre el pip/python del venv
ENV PATH="/opt/venv/bin:${PATH}"

# Configuración de PYTHONPATH para que reconozca los módulos
ENV PYTHONPATH="/program:${PYTHONPATH}"

# Crear un alias para ejecutar ANTLR usando Java
RUN echo 'alias antlr="java -jar /usr/local/lib/antlr-4.13.1-complete.jar"' >> /etc/bash.bashrc
RUN echo "alias antlr='java -jar /usr/local/lib/antlr-4.13.1-complete.jar'" >> ~/.bashrc

# Crear un usuario no root
ARG USER=appuser
ARG UID=1001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/${USER}" \
    --no-create-home \
    --uid "${UID}" \
    "${USER}"

# Añadir permisos al directorio home
RUN mkdir -p /home/appuser && chown -R appuser:appuser /home/appuser

# Usuario root para instalar streamlit
USER root
RUN pip install streamlit  # Instalar paquetes como root

# Cambiar al usuario no root después de la instalación
USER ${UID}

# Establecer el directorio de trabajo
WORKDIR /program

# Exponer el puerto
EXPOSE 8501

# Comando por defecto para iniciar Streamlit
CMD ["streamlit", "run", "program/ide/app.py"]
