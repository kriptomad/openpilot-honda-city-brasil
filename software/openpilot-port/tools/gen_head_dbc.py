import sys, os
sys.path.insert(0, os.path.join(os.environ["TEMP"], "opendbc_head"))
from opendbc.dbc.generator import generator
import re
src = os.path.join(os.environ["TEMP"], "opendbc_head", "opendbc", "dbc", "generator", "honda")
out = os.path.join(os.environ["TEMP"], "city_route", "head_bosch_radarless.dbc")
txt = generator._create_dbc_content(src, "honda_bosch_radarless.dbc") if hasattr(generator, "_create_dbc_content") else None
if txt is None:
    import inspect; print([n for n in dir(generator) if not n.startswith("__")]); sys.exit(1)
open(out, "w", encoding="utf-8").write(txt)
print("wrote", out, len(txt))
