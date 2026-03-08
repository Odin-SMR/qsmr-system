ARG FM="2"
ARG INVMODE="stnd"

## Build and install arts
FROM ubuntu:noble AS build-arts
RUN apt-get update
RUN apt-get install -y \
    build-essential \
    cmake \
    libblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    zlib1g-dev \
    git
RUN git clone https://github.com/atmtools/arts.git
WORKDIR /arts
RUN git reset --hard e5d1c95
WORKDIR /arts/build
RUN cmake -DCMAKE_BUILD_TYPE=Release -DNO_DOCSERVER=1 -DCMAKE_INSTALL_PREFIX=/opt ..
RUN make -j4 arts
RUN make install

## matlab runtime
FROM ubuntu:noble AS install-qsmr-runtime
RUN apt update && \
    apt install -y --no-install-recommends ca-certificates unzip
COPY qsmrInstaller /qsmrInstaller
COPY installer_input.txt /qsmrInstaller
WORKDIR /qsmrInstaller
RUN ./qsmrInstaller.install -inputfile installer_input.txt

## runtime image
FROM ubuntu:noble AS runtime
RUN apt update \
    && apt-get install -y --no-install-recommends \
    libxt6t64 \
    ca-certificates \
    curl \
    libblas3 liblapack3 libgomp1 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build-arts /opt /opt
COPY --from=install-qsmr-runtime /opt/MATLAB /opt/MATLAB

## run precalc
FROM runtime AS qsmr-data
COPY precalcstandaloneApplication /precalc
COPY qsmr-data/DataInput /QsmrData/DataInput
COPY qsmr-data/DataPrecalced /QsmrData/DataPrecalced
RUN mkdir -p /QsmrData/AbsLookup/Meso
RUN mkdir -p /QsmrData/AbsLookup/Stnd
ARG FM
ARG INVMODE
RUN /precalc/run_precalc.sh /opt/MATLAB/R2024b /QsmrData/ ${INVMODE} ${FM}

## final image
FROM runtime AS final
ENV DEBIAN_FRONTEND=noninteractive
ENV UV_INSTALL_DIR=/usr/local/bin
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
COPY --from=qsmr-data /QsmrData /QsmrData
COPY qsmrstandaloneApplication /qsmr

RUN uv venv --python 3.12 /venv
WORKDIR /venv
COPY dist/qsmr_system-1.0.0-py3-none-any.whl /qsmrsystem/
RUN /usr/local/bin/uv pip install /qsmrsystem/qsmr_system-1.0.0-py3-none-any.whl

ENTRYPOINT [ "uv", "run", "/qsmr/run_qsmr.sh", "/opt/MATLAB/R2024b/" ]
CMD []

# .devcontainer/Dockerfile
FROM runtime AS dev
RUN apt update \
    && apt-get install -y --no-install-recommends \
        git sudo
ENV DEBIAN_FRONTEND=noninteractive
ENV UV_INSTALL_DIR=/usr/local/bin
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
COPY --from=qsmr-data /QsmrData /QsmrData
COPY qsmrstandaloneApplication /qsmr
# --- create dev user ---
ARG USERNAME=ubuntu
RUN  echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 440 /etc/sudoers.d/$USERNAME

USER ${USERNAME}
WORKDIR /workspaces/qsmr-system
ENTRYPOINT []
CMD [ "sleep", "infinity" ]
