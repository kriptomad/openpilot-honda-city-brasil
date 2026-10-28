import os, sys, runpy
REPO = os.path.abspath(sys.argv[1]); os.environ["FP_REPO"] = REPO
sys.path.insert(0, REPO); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); os.chdir(REPO)
import fp_shims; fp_shims.install()
sys.argv = [sys.argv[2]] + sys.argv[3:]
runpy.run_path(sys.argv[0], run_name="__main__")
