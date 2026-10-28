import os, sys
HERE = os.path.abspath(".")
REPO = os.path.join(HERE, "flowpilot"); os.environ["FP_REPO"] = REPO
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(HERE, "tests_windows")); os.chdir(REPO)
import fp_shims; fp_shims.install()
from selfdrive.car.docs import generate_cars_md, get_all_car_info, CARS_MD_TEMPLATE, CARS_MD_OUT
md = generate_cars_md(get_all_car_info(), CARS_MD_TEMPLATE)
os.makedirs(os.path.dirname(CARS_MD_OUT), exist_ok=True)
with open(CARS_MD_OUT, "wb") as f:
    f.write(md.replace("\r\n", "\n").encode("utf-8"))
print("wrote", CARS_MD_OUT, len(md))
