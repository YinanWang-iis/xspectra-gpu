#!/bin/bash
#SBATCH -J qe_scf
#SBATCH -p <partition>
#SBATCH -N 1
#SBATCH -n 64
#SBATCH -c 1
#SBATCH --time=12:00:00
# Example: XCH SCF on a CPU node (recommended), then run XSpectra on a GPU with run_xspectra_gpu.sh
# using the same outdir. Load your compiler/MPI environment and set QE_BIN to the CPU build's bin/.
#   sbatch --export=ALL,QE_BIN=/path/to/build_cpu/bin,NK=8 run_scf_cpu.slurm
set -uo pipefail
: "${QE_BIN:?set QE_BIN}"
export OMP_NUM_THREADS=1
ts=$(date +%s)
mpirun -np ${SLURM_NTASKS} $QE_BIN/pw.x -nk ${NK:-1} -in pw.in > pw.out 2>&1
echo "wall pw.x $(( $(date +%s) - ts )) s (np=${SLURM_NTASKS}, -nk ${NK:-1})"
