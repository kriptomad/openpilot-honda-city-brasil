"""Insere/atualiza o bloco de changelog do branch no README dos forks (opendbc e openpilot).

Uso: python tools/readme_branch_note.py <opendbc|openpilot> <caminho do README.md>
Idempotente: substitui o bloco entre os marcadores se ja existir.
"""
import re
import sys

OPENDBC = """> [!IMPORTANT]
> **Fork branch `firmwarecityg7-v0.9.9` -- Honda City (Brazil only) 2023 (G7) on openpilot v0.9.9 / black panda.**
> Base: commaai/opendbc `e370a036` (the commit pinned by openpilot v0.9.9, the last release that supports the
> STM32F4 black panda). Upstream added the City after that, so this branch backports **every** upstream change the
> City depends on, byte for byte, without retuning other platforms. Not road tested.
>
> **What is new / modified on this branch (8 commits on top of `e370a036`):**
>
> | Commit | Files | Change |
> |---|---|---|
> | `34dd823b` | `car/honda/values.py`, `fingerprints.py`, `docs/CARS.md`, safety tests | `HONDA_CITY_7G` platform (`HondaBoschPlatformConfig`, `BOSCH_RADARLESS`, harness Bosch B), FW fingerprints, torque params, `STEER_THRESHOLD` 600 -- backport of the upstream City merge |
> | `5f439d78` | `pyproject.toml` (CI only) | pin `ruff==0.11.13` so lint matches the v0.9.9 era |
> | `256ff78c` | `car/honda/tests`, `docs/CARS.md` | City test route and CARS.md line as upstream |
> | `ae690dd7` | `car/honda/carstate.py`, `values.py` | `HondaFlags.HAS_EPB` auto-detection (upstream `6fa346ed`): the City has no `0x1C2 EPB_STATUS`; without this it never engages |
> | `07add98b` | `dbc/generator/honda` | `EPB_STATUS` DBC part of upstream `6fa346ed` |
> | `d42db044` | `car/honda/interface.py` | `steerActuatorDelay` set before per-car tuning (upstream `28a16218`); the generic 0.1 was overwriting the City's 0.15 |
> | `052a515f` | `car/honda/interface.py` | City-only `lateralTuning.torque.ki = 0.3` (upstream `fb5ac6d3` changed the global default; 0.1 kept for every other brand) |
> | `b4125fe6` | `dbc/generator/honda/honda_civic_ex_2022_can.dbc` | `BO_ 401 GEARBOX` now has the upstream `GEARBOX_CVT` layout (`GEAR_SHIFTER` in byte 5, `1 P 2 R 3 N 4 D 7 L 10 S`); D already decoded identically, S/L now decode as upstream. Affects City, HR-V 3G and Civic 2022 exactly as upstream. `pyproject.toml` back to LF |
>
> `opendbc/safety` is unchanged: the City runs the existing `HONDA_BOSCH` + `RADARLESS` path, verified RX/TX-identical to
> upstream. Audit reports, verification tools and the equivalent `git format-patch` series live in
> [kriptomad/PandaH7Openpilot](https://github.com/kriptomad/PandaH7Openpilot/tree/main/09_FIRMWARECITYG7_BLACKPANDA).
> Consumed by [kriptomad/openpilot@v0.9.9-cityg7-blackpanda](https://github.com/kriptomad/openpilot/tree/v0.9.9-cityg7-blackpanda).
"""

OPENPILOT = """> [!IMPORTANT]
> **Fork branch `v0.9.9-cityg7-blackpanda` -- Honda City (Brazil only) 2023 (G7) on openpilot v0.9.9.**
> This branch ports the City support, merged upstream after openpilot 0.9.9, back onto **v0.9.9** -- the last
> release that still supports the STM32F4 **black panda**. Goal: a byte-for-byte faithful port of every upstream
> change the City depends on, plus the follow-up upstream fixes it needs to engage. Two independent code audits
> were run (commit-by-commit over 73 upstream Honda commits, CarParams field by field, TX byte by byte, safety,
> firmware recognition, plus an adversarial second pass with a real-code replay of the City route).
> **Status: port complete, CI green on the fork, not road tested.** CI badge above points at upstream.
>
> **What is new / modified on this branch (11 commits on top of v0.9.9 `8aadf02b`):**
>
> | Commit | Files | Change |
> |---|---|---|
> | `857dee1dc` | `.gitmodules`, `opendbc_repo`, `docs/CARS.md`, `RELEASES.md` | `opendbc_repo` submodule points at the fork branch below; City line in `docs/CARS.md` (same format as upstream `09aa21390`); release note |
> | `4937c6391` | -- | empty commit (workflow indexing on the fork) |
> | `52f261127` | `uv.lock`, `.github/workflows` | CI only: relock `metadrive-simulator` wheel hash (upstream `4d53a26a0`); skip `build release` outside `commaai/openpilot` |
> | `bac73ff1b` | `opendbc_repo` | bump to `07add98b` (EPB_STATUS DBC) |
> | `0a5c06856` | `README.md` | first fork note (replaced by this changelog) |
> | `c3e422ae9` | `selfdrive/car/car_specific.py` | `GearShifter.sport` accepted for Honda (upstream `bae7a610f`); the City CVT has an S position, without this S raises `wrongGear` |
> | `89df27131` | `opendbc_repo` | bump to `052a515f` (City `steerActuatorDelay` 0.15, City-only torque `ki` 0.3) |
> | `8be62bc95` | `selfdrive/locationd/torqued.py` | `ALLOWED_CARS += 'honda'` (upstream `839a77334`): live lateral-accel-factor learning; only active for torque-tuned Hondas, i.e. the City on v0.9.9 |
> | `e841f3cc3` | `opendbc_repo` | bump to `b4125fe6` (`GEARBOX_CVT` layout: S/L decode as upstream) |
>
> Everything car-specific lives in the submodule:
> [kriptomad/opendbc@firmwarecityg7-v0.9.9](https://github.com/kriptomad/opendbc/tree/firmwarecityg7-v0.9.9)
> (8 commits, listed in its README). Known, deliberate differences from upstream that are platform-wide and were
> **not** ported: `common/pid.py` / `latcontrol_torque.py` anti-windup (`455a6a586`, `ab44c9a4f`), `pandad`
> relay/IsOnroad changes, global torque `ki` default. Audit reports, tools and the `git format-patch` series:
> [kriptomad/PandaH7Openpilot](https://github.com/kriptomad/PandaH7Openpilot/tree/main/09_FIRMWARECITYG7_BLACKPANDA).
"""

FLOWPILOT = """> [!IMPORTANT]
> **Branch `flowpilot-city-g7-brazil` -- Honda City (Brazil only) 2023 (G7) on flowpilot (standalone APK) + black panda.**
> Base: a snapshot of [jagheterfredrik/flowpilot](https://github.com/jagheterfredrik/flowpilot) master `9ea918ea`
> (2025-03-04; standalone APK, car layer ~ openpilot 0.9.2-0.9.4, panda flattened at commaai/panda `abdc4185`).
> The snapshot was imported as a tarball, so this repo has no upstream history. Target device: Xiaomi Poco F3 +
> STM32F4 black panda. **Not tested on phone, panda or car. APK not built yet (needs Docker/Linux).**
>
> **What is new / modified on this branch (3 commits on top of the snapshot `43eab22`):**
>
> | Commit | Files | Change |
> |---|---|---|
> | `a2f1983` | `selfdrive/car/honda/{values,interface,carstate,fingerprints}.py`, `opendbc/generator/honda`, `opendbc/*.dbc`, `docs/CARS.md`, routes | `HONDA_CITY_7G` radarless Bosch platform (harness Bosch B), FW + CAN fingerprints (36 msgs checked against a real City route), `STEER_THRESHOLD` 600, `HAS_EPB` auto-detection (City has no `0x1C2 EPB_STATUS`), torque tune `[1.2, 1.2, 0.23]` + `ki` 0.3, `steerActuatorDelay` 0.15, CVT `S` gear accepted, DBC `BO_ 401 GEARBOX` with the upstream `GEARBOX_CVT` layout (`1 P 2 R 3 N 4 D 7 L 10 S`) |
> | `fd9e846` | `panda/` | Windows-only SCons helper to build the black panda firmware from this tree without Docker |
> | `275df51` | `selfdrive/car/*/interface.py`, `selfdrive/car/honda/values.py`, `docs/CARS.md` | fix pre-existing `CarInterface.apply(c, sm, now_nanos)` signature mismatch with `controlsd` in 10 brands; Honda `STEER_*` constants; regenerated `CARS.md` |
>
> Panda firmware: built from this tree (`panda.bin.signed`, version `DEV-a2f1983c-DEBUG`, debug-signed -> the stock
> release bootstub must be replaced once over DFU). `safety_honda.h` is unchanged (`HONDA_BOSCH` + `RADARLESS`),
> `tests/safety/test_honda.py` 209/209 on a mingw-w64 build. Scope research, port report (PT-BR), firmware binaries,
> Poco F3 install and step-by-step flash procedure:
> [kriptomad/PandaH7Openpilot/10_FLOWPILOT](https://github.com/kriptomad/PandaH7Openpilot/tree/main/10_FLOWPILOT).
> Sibling ports of the same car: [opendbc@firmwarecityg7-v0.9.9](https://github.com/kriptomad/opendbc/tree/firmwarecityg7-v0.9.9),
> [openpilot@v0.9.9-cityg7-blackpanda](https://github.com/kriptomad/openpilot/tree/v0.9.9-cityg7-blackpanda).
"""

START = "<!-- fork-branch-note:start -->"
END = "<!-- fork-branch-note:end -->"

kind, path = sys.argv[1], sys.argv[2]
block = {"opendbc": OPENDBC, "openpilot": OPENPILOT, "flowpilot": FLOWPILOT}[kind]
wrapped = f"{START}\n{block}{END}\n"

raw = open(path, "rb").read()
crlf = b"\r\n" in raw
txt = raw.decode("utf-8").replace("\r\n", "\n")

if START in txt:
    txt = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n", wrapped, txt, flags=re.S)
elif kind == "openpilot" and "> [!IMPORTANT]\n> **Fork branch `v0.9.9-cityg7-blackpanda`" in txt:
    # substitui a nota antiga (0a5c06856) pela nova com marcadores
    txt = re.sub(r"> \[!IMPORTANT\]\n> \*\*Fork branch `v0\.9\.9-cityg7-blackpanda`.*?\n\n", wrapped + "\n", txt, count=1, flags=re.S)
elif kind == "flowpilot":
    # README do flowpilot comeca com "# Flowpilot stand alone": insere o bloco logo apos o titulo
    first_nl = txt.index("\n") + 1
    txt = txt[:first_nl] + "\n" + wrapped + txt[first_nl:]
else:
    anchor = "</div>\n\n---\n"
    assert anchor in txt, "anchor not found"
    txt = txt.replace(anchor, "</div>\n\n" + wrapped + "\n---\n", 1)

out = txt.replace("\n", "\r\n") if crlf else txt
open(path, "wb").write(out.encode("utf-8"))
print("ok", path)
