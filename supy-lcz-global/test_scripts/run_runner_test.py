import os
os.environ['USE_PYGEOS'] = '0'

import argparse
from pathlib import Path
from runner.runner import main as run_supy

run_supy(['KL-KualaLumpurTest2',
        '--run-type', 'grid',
        '--grid-size', '1000',
        '--grid-boxes', '20',
        '--metforc-src', 'era5land',
        '--urbdesc-src', 'lcz_updated',
        '--sitelist', 'sitelist_custom',
        '--download-era5'])