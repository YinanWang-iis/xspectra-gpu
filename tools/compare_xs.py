#!/usr/bin/env python
"""Compare two XSpectra runs (reference vs test) for xanes_dipole save/spectrum files.
Usage: compare_xs.py REF_DIR TEST_DIR [pol ...]   (default pols x y z)
Reports per k-point: xnorm rel diff, ncalcv, max rel diff of a,b over the first
N iterations (N = 10, 50, 100, all common), and spectrum max|diff|/max(ref)."""
import sys, os
import numpy as np

def read_sav(fn):
    L = open(fn).read().split('\n')
    hdr = [l for l in L[:6]]
    tok = ' '.join(L[6:]).split()
    p = 0
    def take(n, typ=float):
        nonlocal p
        v = tok[p:p + n]; p += n
        return [typ(x) if typ is not str else x for x in v]
    lsda, nspin = take(1, str)[0], int(take(1)[0])
    xang, nk, nmax = [int(float(x)) for x in take(3)]
    ncmax = int(float(take(1)[0]))
    E, ef = take(2)
    xk = take(3); eps = take(3)
    kind = hdr[1]
    nl = int(hdr[3].split('=')[1])
    out = []
    for il in range(nl):
        if 'unfinished' in kind:
            take(nk)
        xnorm = np.array(take(nk))
        nc = np.array([int(float(x)) for x in take(nk)])
        a = np.array(take(ncmax * nk)).reshape(nk, ncmax)
        b = np.array(take(ncmax * nk)).reshape(nk, ncmax)
        out.append(dict(xnorm=xnorm, nc=nc, a=a, b=b, ef=ef))
    return out

def read_dat(fn):
    d = np.loadtxt(fn, comments='#')
    return d[:, 0], d[:, 1:]

def main():
    ref, tst = sys.argv[1], sys.argv[2]
    pols = sys.argv[3:] or ['x', 'y', 'z']
    worst = {}
    for p in pols:
        R = read_sav(os.path.join(ref, f'xanes_{p}.sav'))
        T = read_sav(os.path.join(tst, f'xanes_{p}.sav'))
        for il, (r, t) in enumerate(zip(R, T)):
          print(f'=== {p}  lanczos chain {il+1}/{len(R)}   Ef ref/test = {r["ef"]:.10f} / {t["ef"]:.10f}')
          print('  ik  ncalcv(ref,test)  xnorm_rel   |da/a|,|db/b| max over first N iters: N=10        N=50        N=100       all-common')
          for ik in range(len(r['nc'])):
            nr, nt = r['nc'][ik], t['nc'][ik]
            if nr == 0 or nt == 0:
                print(f'  {ik+1:2d}  {nr:5d} {nt:5d}   (skipped: zero initial vector)'); continue
            xr = abs(t['xnorm'][ik] - r['xnorm'][ik]) / abs(r['xnorm'][ik])
            row = f'  {ik+1:2d}  {nr:5d} {nt:5d}        {xr:9.2e}  '
            for N in (10, 50, 100, min(nr, nt)):
                key = N if N in (10, 50, 100) else 'all'
                N = min(N, nr, nt)
                ra = np.max(np.abs(t['a'][ik, :N] - r['a'][ik, :N]) / np.abs(r['a'][ik, :N]))
                rb = np.max(np.abs(t['b'][ik, :N] - r['b'][ik, :N]) / np.abs(r['b'][ik, :N]))
                row += f' {max(ra, rb):9.2e}  '
                worst[key] = max(worst.get(key, 0), ra, rb)
            worst['xnorm'] = max(worst.get('xnorm', 0), xr)
            print(row)
        er, sr = read_dat(os.path.join(ref, f'xanes_{p}.dat'))
        et, st = read_dat(os.path.join(tst, f'xanes_{p}.dat'))
        assert np.allclose(er, et)
        d = np.max(np.abs(st - sr)) / np.max(np.abs(sr))
        worst['spec'] = max(worst.get('spec', 0), d)
        print(f'  spectrum: max|diff|/max(ref) = {d:.3e}   (max ref = {np.max(sr):.6f})')
    print('WORST:', {str(k): f'{v:.2e}' for k, v in worst.items()})

if __name__ == '__main__':
    main()
