#!/usr/bin/env python
"""Phase-2 acceptance check: GPU runs judged against the spread of CPU runs.

Usage: ensemble_check.py --pols x y z --cpu D1 D2 ... --gpu G1 G2 ...

Criteria (agreed with the user 2026-11-11: "以 CPU 进程间差异为尺度"):
 C1  Lanczos a,b over the first 50 iterations: max relative GPU-CPU difference
     <= 1e-10 for every k-point / chain and every CPU run (the CPU-CPU value is
     printed for scale); xnorm relative difference <= 1e-12.
 C2  spectrum: for every polarization, max_j d(GPU, CPU_j) <= max_{i<j} d(CPU_i, CPU_j)
     with d(A,B) = max|A-B| / max|A_ref| over all energy points / columns.
 C3  number of Lanczos iterations of every k / chain inside
     [0.9*min_CPU, 1.1*max_CPU].
"""
import argparse, itertools, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare_xs import read_sav, read_dat

def coef_diff(r, t, N):
    """max rel diff of a,b over first N iters, all k / chains; max xnorm rel diff"""
    m, x = 0.0, 0.0
    for cr, ct in zip(r, t):
        for ik in range(len(cr['nc'])):
            nr, nt = cr['nc'][ik], ct['nc'][ik]
            if nr == 0 and nt == 0:
                continue
            n = min(N, nr, nt)
            for key in ('a', 'b'):
                m = max(m, np.max(np.abs(ct[key][ik, :n] - cr[key][ik, :n]) / np.abs(cr[key][ik, :n])))
            x = max(x, abs(ct['xnorm'][ik] - cr['xnorm'][ik]) / abs(cr['xnorm'][ik]))
    return m, x

def spec_d(A, B):
    return np.max(np.abs(A - B)) / np.max(np.abs(A))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pols', nargs='+', required=True)
    ap.add_argument('--cpu', nargs='+', required=True)
    ap.add_argument('--gpu', nargs='+', required=True)
    o = ap.parse_args()
    ok_all = True
    for p in o.pols:
        sav = {d: read_sav(os.path.join(d, f'xanes_{p}.sav')) for d in o.cpu + o.gpu}
        dat = {d: read_dat(os.path.join(d, f'xanes_{p}.dat'))[1] for d in o.cpu + o.gpu}
        print(f'\n=== {p}:  CPU runs {[os.path.basename(d) for d in o.cpu]}   GPU runs {[os.path.basename(d) for d in o.gpu]}')
        # C1
        cc50 = max(coef_diff(sav[i], sav[j], 50)[0] for i, j in itertools.combinations(o.cpu, 2))
        g10 = max(coef_diff(sav[c], sav[g], 10)[0] for c in o.cpu for g in o.gpu)
        g50, gx = 0.0, 0.0
        for c in o.cpu:
            for g in o.gpu:
                m, x = coef_diff(sav[c], sav[g], 50)
                g50, gx = max(g50, m), max(gx, x)
        c1 = g50 <= 1e-10 and gx <= 1e-12
        print(f'  C1 a,b first 10 / 50 iters: GPU-CPU max {g10:.2e} / {g50:.2e}   (CPU-CPU first 50: {cc50:.2e});  xnorm GPU-CPU {gx:.2e}   -> {"PASS" if c1 else "FAIL"}')
        # C2
        dcc = [spec_d(dat[i], dat[j]) for i, j in itertools.combinations(o.cpu, 2)]
        S = max(dcc)
        c2 = True
        for g in o.gpu:
            dg = [spec_d(dat[c], dat[g]) for c in o.cpu]
            ok = max(dg) <= S
            c2 &= ok
            print(f'  C2 spectrum {os.path.basename(g):9s}: d(GPU,CPU_j) max {max(dg):.2e} mean {np.mean(dg):.2e}   vs CPU-CPU max {S:.2e} mean {np.mean(dcc):.2e}  -> {"PASS" if ok else "FAIL"}')
        for g1, g2 in itertools.combinations(o.gpu, 2):
            print(f'     GPU-GPU {os.path.basename(g1)} vs {os.path.basename(g2)}: spectrum {spec_d(dat[g1], dat[g2]):.2e}, a,b first 50 {coef_diff(sav[g1], sav[g2], 50)[0]:.2e}, all-equal={all(np.array_equal(a[k], b[k]) for a, b in zip(sav[g1], sav[g2]) for k in ("a","b"))}')
        # C3
        c3 = True; worst = ''
        nch = len(sav[o.cpu[0]])
        for il in range(nch):
            ncs = np.array([sav[c][il]['nc'] for c in o.cpu])
            lo, hi = 0.9 * ncs.min(0), 1.1 * ncs.max(0)
            for g in o.gpu:
                ng = sav[g][il]['nc']
                bad = (ng < lo) | (ng > hi)
                if bad.any():
                    c3 = False; worst += f' {os.path.basename(g)} chain{il+1} k{np.where(bad)[0]+1}'
        rng = [f'{sav[c][0]["nc"].sum()}' for c in o.cpu]; rgg = [f'{sav[g][0]["nc"].sum()}' for g in o.gpu]
        print(f'  C3 iterations (sum over k, chain 1): CPU {rng}  GPU {rgg}  -> {"PASS" if c3 else "FAIL" + worst}')
        ok_all &= c1 and c2 and c3
    print('\nOVERALL:', 'PASS' if ok_all else 'FAIL')

main()
