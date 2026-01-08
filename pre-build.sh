#!/bin/bash
MATLAB=~/mat/bin/matlab

echo "Compiling MATLAB QSMR program..."
$MATLAB -nojvm -nodesktop -batch "compile_qsmr"

echo "Compiling Precalc program..."
$MATLAB -nojvm -nodesktop -batch "compile_qsmr_data"

echo "MATLAB compilation completed."
