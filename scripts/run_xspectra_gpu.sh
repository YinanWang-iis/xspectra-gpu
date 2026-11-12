#!/bin/bash
# Run xspectra.x on one GPU for one or more inputs, e.g. the x, y, z polarizations:
#
#   XS_BIN=/path/to/build/bin bash run_xspectra_gpu.sh x y z      # runs xspectra_x.in, xspectra_y.in, ...
#
# The SCF save directory named in the inputs (outdir/prefix) may come from a CPU pw.x run.
# Environment variables:
#   XS_BIN       directory with xspectra.x (required)
#   NVHPC_ROOT   NVIDIA HPC SDK, default /opt/nvidia/hpc_sdk/Linux_x86_64/26.3
#   GPU          CUDA device index, default 0
#   OMP          OpenMP threads for the host part, default 8
#   NP           MPI ranks (sharing the GPU), default 1;  XS_ARGS e.g. "-nk 2" (k-point pools)
#   CUDA_COMPAT  1 = use the CUDA forward-compatibility libcuda shipped with the SDK, needed when the
#                driver is older than the SDK's CUDA (data-center GPUs only, e.g. A100 with driver 550)
set -uo pipefail
: "${XS_BIN:?set XS_BIN to the directory containing xspectra.x}"
NVHPC_ROOT=${NVHPC_ROOT:-/opt/nvidia/hpc_sdk/Linux_x86_64/26.3}
export PATH=$XS_BIN:$NVHPC_ROOT/compilers/bin:$NVHPC_ROOT/comm_libs/mpi/bin:$PATH
export LD_LIBRARY_PATH=$NVHPC_ROOT/compilers/lib:$NVHPC_ROOT/cuda/lib64:$NVHPC_ROOT/math_libs/lib64:$NVHPC_ROOT/comm_libs/mpi/lib:${LD_LIBRARY_PATH:-}
[ "${CUDA_COMPAT:-0}" = 1 ] && export LD_LIBRARY_PATH=$NVHPC_ROOT/cuda/$(ls $NVHPC_ROOT/cuda | grep -E '^[0-9]+\.[0-9]+$' | tail -1)/compat:$LD_LIBRARY_PATH
export OPAL_PREFIX=$(readlink -f $NVHPC_ROOT/comm_libs/mpi)
export CUDA_VISIBLE_DEVICES=${GPU:-0} OMP_NUM_THREADS=${OMP:-8}
MPI="mpirun -np ${NP:-1} --oversubscribe --bind-to none -x OMP_NUM_THREADS -x LD_LIBRARY_PATH -x PATH -x CUDA_VISIBLE_DEVICES"
echo "host $(hostname) GPU=$CUDA_VISIBLE_DEVICES np=${NP:-1} ${XS_ARGS:-} OMP=$OMP_NUM_THREADS start=$(date)"
nvidia-smi --query-gpu=index,name,memory.used --format=csv,noheader
for p in "${@:-x}"; do
  ts=$(date +%s.%N)
  $MPI xspectra.x ${XS_ARGS:-} -in xspectra_$p.in > xspectra_$p.out 2>&1 || { echo "xspectra.x ($p) failed"; exit 1; }
  printf "wall xspectra.x %s %.1f s\n" "$p" "$(echo "$(date +%s.%N)-$ts" | bc)" | tee -a timing.txt
done
