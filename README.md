# qsmr-system

The pupose of this repo is to build docker images with a compiled version of qsmr with precompile data from qsmr-data.

The reason to do this is to be able to run qmsr on any computer, without Matlab installed.

## Build instructions

Requirements to build the qsmr image:

 1. Docker
 1. Matlab with Matlab compiler

The repo consists of two submodules. To update the submodules i.e if qsmr or qsmr-data have changes to be incorporated in the build.
```
git submodule update --recursive
```

### Detailed instructions

 1. Run the `compile_precalc.m` script:
    ```
    matlab -r compile_precalc.m
    ```
 1. Run the `compile_qsmr.m` script:
    ```
    matlab -r compile_qsmr.m
    ```
 1. Build docker images:
    ```
    docker build --build-arg FM=13 --build-arg INVMODE=meso -t qsmr:meso13 .
    ```
