#!/usr/bin/env python
"""CPU vs GPU XSpectra spectrum (same SCF save, same code, Lanczos to convergence).
Usage: plot_cpu_vs_gpu_spectrum.py CPU_xanes.dat GPU_xanes.dat out.png [emin emax]
Both broadened identically: Gaussian exp(-(E/0.2)^2) x Lorentzian HWHM 0.1 eV in total
(XSpectra already contains a Lorentzian of HWHM xgamma = 0.05 eV, so +0.05 eV is added)."""
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def conv(E, I, k):
    dE = E[1] - E[0]; n = int(np.ceil(2.4 / dE)); x = np.arange(-n, n + 1) * dE
    w = k(x); w /= w.sum()
    return np.convolve(np.r_[np.zeros(n), I, np.zeros(n)], w, 'same')[n:-n]
gauss = lambda x: np.exp(-(x / 0.2) ** 2)
lor = lambda x: 0.05 / (x ** 2 + 0.05 ** 2)

c = np.loadtxt(sys.argv[1]); g = np.loadtxt(sys.argv[2]); out = sys.argv[3]
emin, emax = (float(sys.argv[4]), float(sys.argv[5])) if len(sys.argv) > 5 else (-3.0, 40.0)
assert np.allclose(c[:, 0], g[:, 0])
E = c[:, 0]
Ic = conv(E, conv(E, c[:, 1], gauss), lor); Ig = conv(E, conv(E, g[:, 1], gauss), lor)
s = (E >= emin) & (E <= emax)
print(f'max|GPU-CPU|/max(CPU) in [{emin},{emax}] eV: {np.max(np.abs(Ig[s]-Ic[s]))/Ic[s].max():.2e}'
      f'   raw (unbroadened, whole window): {np.max(np.abs(g[:,1]-c[:,1]))/c[:,1].max():.2e}')

plt.rcParams.update({'font.size': 11, 'axes.labelsize': 12, 'axes.edgecolor': '#222222',
                     'text.color': '#222222', 'axes.labelcolor': '#222222',
                     'xtick.color': '#222222', 'ytick.color': '#222222'})
f, ax = plt.subplots(figsize=(4.2, 4.2))
ax.plot(E[s], Ig[s], color='#2F5D50', lw=2.3, label='QE GPU (1× RTX PRO 5000)', zorder=3)
# CPU as open circles every ~0.8 eV, always including the white-line maximum, drawn under the line
Es, Ics = E[s], Ic[s]
step = max(1, int(round(0.80 / (E[1] - E[0]))))
idx = sorted(set(range(0, len(Es), step)) | {int(np.argmax(Ics))})
ax.plot(Es[idx], Ics[idx], ls='none', marker='o', ms=8, mew=2.0,
        mfc='white', mec='#B24A4A', label='QE CPU (64 cores)', zorder=2)
ax.set_xlim(emin, emax); ax.set_ylim(bottom=0)
ax.set_xlabel(r'$E - E_\mathrm{F}$ (eV)'); ax.set_ylabel('Absorption cross section (arb. units)')
ax.set_box_aspect(1)
for sp in ax.spines.values(): sp.set_visible(True)
ax.legend(loc='upper right', frameon=False, fontsize=9)
f.tight_layout(); f.savefig(out, dpi=900, facecolor='white')
print('written', out)
