#!/bin/bash
# CPU-only build of the same patched source with Intel oneAPI (ifort + Intel MPI + MKL DFTI/BLAS).
# Useful as a CPU reference / for the SCF on Intel CPU nodes.
#
#   SRC=/path/to/dm_qe BLD=/path/to/build_cpu_intel bash build_xspectra_intel_cpu.sh
#
# Load the Intel compiler, MPI and MKL environment first (e.g. setvars.sh or your site modules).
set -euo pipefail
: "${SRC:?set SRC to the patched dm_qe source}"; : "${BLD:?set BLD to the build directory}"
JOBS=${JOBS:-16}
cmake -S "$SRC" -B "$BLD" \
  -DCMAKE_BUILD_TYPE=Release -DQE_ENABLE_TEST=OFF \
  -DCMAKE_Fortran_COMPILER=mpiifort -DCMAKE_C_COMPILER=mpiicc \
  -DQE_ENABLE_MPI=ON -DQE_ENABLE_OPENMP=OFF \
  -DQE_FFTW_VENDOR=Intel_DFTI -DBLA_VENDOR=Intel10_64lp_seq
cmake --build "$BLD" -j "$JOBS" --target pw qe_xspectra_exe
echo "built: $BLD/bin/pw.x $BLD/bin/xspectra.x"
