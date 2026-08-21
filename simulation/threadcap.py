"""Pin every BLAS/OpenMP backend to one thread.

Must be imported BEFORE numpy in any script that uses multiprocessing: the
kernels here are small mat-vecs, so per-worker threading buys nothing and the
oversubscription (workers x threads) costs an order of magnitude in wall clock.
"""

import os

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_var] = "1"
