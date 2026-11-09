"""Local original files; never bundled with the public repository."""
import os
from pathlib import Path
ASSETS=Path(os.environ.get('ELMA_DIR',Path(__file__).with_name('assets')))
EXE=os.environ.get('ELMA_EXE',str(ASSETS/'elma.exe'))
RES=os.environ.get('ELMA_RES',str(ASSETS/'elma.res'))
