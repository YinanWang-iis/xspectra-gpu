#!/bin/bash
# Build pw.x and xspectra.x from dm_qe with the patches of this repository applied (NVHPC toolchain).
#
#   SRC=/path/to/dm_qe BLD=/path/to/build FFTW3_ROOT=/path/to/fftw bash build_xspectra.sh
#
# Environment variables:
#   SRC, BLD      patched dm_qe source tree and build directory (required)
#   FFTW3_ROOT    FFTW3 install prefix for the host-side FFTs (required)
#   NVHPC_ROOT    NVIDIA HPC SDK, default /opt/nvidia/hpc_sdk/Linux_x86_64/26.3 (tested with 26.3)
#   FLAVOR        gpu (default) or cpu (same source, no GPU: the CPU reference build)
#   GPU_ARCHS     CUDA architectures, default "sm_80;sm_89;sm_120" (A100; RTX 6000 Ada; RTX PRO Blackwell)
#   HOST_TP       host target for -tp, e.g. x86-64-v3 when the build host has AVX-512 but the
#                 GPU host does not (nvfortran's default is -tp=host)
#   JOBS          parallel build jobs, default 16
# Can also be submitted as a Slurm batch job (CPU only, no GPU needed for building).
set -euo pipefail
: "${SRC:?set SRC to the patched dm_qe source}"; : "${BLD:?set BLD to the build directory}"
: "${FFTW3_ROOT:?set FFTW3_ROOT}"
NVHPC_ROOT=${NVHPC_ROOT:-/opt/nvidia/hpc_sdk/Linux_x86_64/26.3}
FLAVOR=${FLAVOR:-gpu}; JOBS=${JOBS:-16}
export PATH=$NVHPC_ROOT/compilers/bin:$NVHPC_ROOT/comm_libs/mpi/bin:$PATH
export LD_LIBRARY_PATH=$NVHPC_ROOT/compilers/lib:$NVHPC_ROOT/cuda/lib64:$NVHPC_ROOT/math_libs/lib64:${LD_LIBRARY_PATH:-}
OPTS=()
[ "$FLAVOR" = gpu ] && OPTS+=("-DQE_GPU=openacc;cuda" "-DQE_GPU_ARCHS=${GPU_ARCHS:-sm_80;sm_89;sm_120}")
[ -n "${HOST_TP:-}" ] && OPTS+=("-DCMAKE_Fortran_FLAGS=-tp=$HOST_TP" "-DCMAKE_C_FLAGS=-tp=$HOST_TP")
cmake -S "$SRC" -B "$BLD" \
  -DCMAKE_BUILD_TYPE=Release -DQE_ENABLE_TEST=OFF \
  -DCMAKE_Fortran_COMPILER=mpif90 -DCMAKE_C_COMPILER=mpicc "${OPTS[@]}" \
  -DQE_ENABLE_MPI=ON -DQE_ENABLE_OPENMP=ON \
  -DQE_FFTW_VENDOR=FFTW3 -DFFTW3_ROOT="$FFTW3_ROOT" \
  -DBLAS_LIBRARIES="$NVHPC_ROOT/compilers/lib/libblas.so" \
  "-DLAPACK_LIBRARIES=$NVHPC_ROOT/compilers/lib/liblapack.so;$NVHPC_ROOT/compilers/lib/libblas.so"
cmake --build "$BLD" -j "$JOBS" --target pw qe_xspectra_exe
echo "built: $BLD/bin/pw.x $BLD/bin/xspectra.x (flavor=$FLAVOR, git $(git -C "$SRC" rev-parse --short HEAD))"
