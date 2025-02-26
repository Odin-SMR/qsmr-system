# qsmr-system

The pupose of this repo is to build docker images with a compiled version of qsmr with precompile data from qsmr-data.

The reason to do this is to be able to run qmsr on any computer, without Matlab installed.

## Build requirements

Requirements to build the qsmr image to run in AWS ECS:

 1. Docker
 1. Matlab with Matlab compiler
 1. Credentials to odin on AWS

The repo consists of two submodules. To update the submodules i.e if qsmr or qsmr-data have changes to be incorporated in the build.
```
git submodule update --recursive
```

### Detailed build instructions
```
./deploy.sh
```
