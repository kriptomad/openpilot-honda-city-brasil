import os, sys
HERE = os.path.abspath(".")
REPO = os.path.join(HERE, "flowpilot"); os.environ["FP_REPO"] = REPO
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(HERE, "tests_windows")); os.chdir(REPO)
import fp_shims; fp_shims.install()
from selfdrive.car.fingerprints import _FINGERPRINTS as F, eliminate_incompatible_cars, all_legacy_fingerprint_cars
from selfdrive.car.tests.test_fingerprints import check_fingerprint_consistency
tb = F["CHEVROLET TRAILBLAZER 2021"]
city = F["HONDA CITY 7G"][0]
print("TB variants:", len(tb), [len(t) for t in tb])
for t in tb:
    print("consistent with city:", check_fingerprint_consistency(t, city), "city in tb:", all(k in t and t[k]==v for k,v in city.items() if k<1800), "tb in city:", all(k in city and city[k]==v for k,v in t.items() if k<1800))
class M:
    def __init__(s,a,n): s.address=a; s.dat=bytes(n)
cands = all_legacy_fingerprint_cars()
print("candidates:", len(cands))
for a,n in list(city.items()):
    cands = eliminate_incompatible_cars(M(a,n), cands)
print("after city msgs:", cands)
