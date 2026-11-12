#!/usr/bin/env python
"""Bar chart for the README: wall time of SCF + XSpectra (one polarization, Lanczos run to
convergence) for 162-atom SiO2, Si K edge, XCH. Measured values, seconds.
Usage: plot_timing_bar.py SCF_CPU SCF_GPU XS_CPU XS_GPU out.png"""
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

scf_cpu, scf_gpu, xs_cpu, xs_gpu = (float(v) for v in sys.argv[1:5])
out = sys.argv[5]
# (label, SCF time, XSpectra time) -- top to bottom
rows = [('CPU only\n(64 cores)', scf_cpu, xs_cpu),
        ('GPU only\n(1 RTX PRO 5000)', scf_gpu, xs_gpu),
        ('SCF on CPU +\nXSpectra on GPU', scf_cpu, xs_gpu)]
C_SCF, C_XS = '#4C72B0', '#B24A4A'      # passes protan/deutan/tritan OKLab check (dE >= 16)
INK, MUTED, GRID = '#222222', '#555555', '#D8D8D8'

plt.rcParams.update({'font.size': 11, 'axes.labelsize': 12, 'text.color': INK,
                     'axes.labelcolor': INK, 'xtick.color': INK, 'ytick.color': INK,
                     'axes.edgecolor': INK})
fig, ax = plt.subplots(figsize=(6.4, 3.4))
ys = list(range(len(rows)))[::-1]
h = 0.56
for y, (lab, s, x) in zip(ys, rows):
    ax.barh(y, s, height=h, color=C_SCF, edgecolor='white', linewidth=2, zorder=3)
    ax.barh(y, x, left=s, height=h, color=C_XS, edgecolor='white', linewidth=2, zorder=3)
    ax.text(s + x + 60, y, f'{(s + x) / 60:.0f} min', va='center', ha='left', color=INK, fontsize=11)
ax.set_yticks(ys)
ax.set_yticklabels([r[0] for r in rows])
xmax = max(s + x for _, s, x in rows)
ax.set_xlim(0, xmax * 1.18)
ax.set_xlabel('Wall time (s)')
ax.xaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for sp in ax.spines.values():
    sp.set_visible(True)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=C_SCF, label='SCF (pw.x)'), Patch(color=C_XS, label='XSpectra')],
          loc='lower right', frameon=False, fontsize=10)
fig.tight_layout()
fig.savefig(out, dpi=300, facecolor='white')
print('written', out)
