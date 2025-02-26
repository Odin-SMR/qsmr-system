ARG FM="2"
ARG INVMODE="stnd"

## Build and install arts
FROM mathworks/matlab-runtime-deps:R2024b AS build-arts
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

# #matlab runtime
FROM mathworks/matlab-runtime-deps:R2024b AS install-qsmr-runtime
COPY qsmrInstaller /qsmrInstaller
COPY installer_input.txt /qsmrInstaller
WORKDIR /qsmrInstaller
RUN ./qsmrInstaller.install -inputfile installer_input.txt

## run precalc
FROM mathworks/matlab-runtime-deps:R2024b AS qsmr-data
# arts runtime deps
RUN apt update && \
    apt install -y libblas3 liblapack3 libgomp1 && \
    rm -rf /var/lib/apt/lists/*
COPY --from=build-arts /opt /opt
COPY precalcInstaller /precalcInstaller
COPY installer_input.txt /precalcInstaller
WORKDIR /precalcInstaller
RUN ./precalcInstaller.install -inputfile installer_input.txt
COPY precalcstandaloneApplication /precalc
COPY qsmr-data/DataInput /QsmrData/DataInput
COPY qsmr-data/DataPrecalced /QsmrData/DataPrecalced
RUN mkdir -p /QsmrData/AbsLookup/Meso
RUN mkdir -p /QsmrData/AbsLookup/Stnd
ARG FM
ARG INVMODE
RUN /precalc/run_precalc.sh /opt/MATLAB/R2024b /QsmrData/ ${INVMODE} ${FM}

## final image
FROM mathworks/matlab-runtime-deps:R2024b
# arts runtime deps
RUN apt update && \
    apt install -y --no-install-recommends libblas3 liblapack3 libgomp1 python3-boto3 && \
    rm -rf /var/lib/apt/lists/*
# arts
COPY --from=build-arts /opt /opt
# matlab runtime
COPY --from=install-qsmr-runtime /opt/MATLAB /opt/MATLAB
# qsmr data
COPY --from=qsmr-data /QsmrData /QsmrData
# compiled qsmr
COPY qsmrstandaloneApplication /qsmr
WORKDIR /qsmr
COPY batch_qsmr.py .
ENTRYPOINT [ "python3" ]
CMD [ "batch_qsmr.py" ]
