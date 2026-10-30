# pandarevive: the black panda on current openpilot master

Short summary of the pandarevive work. The full description, exact commit
hashes and CI results live in the dedicated repository
[kriptomad/pandarevive](https://github.com/kriptomad/pandarevive)
(`README.md`, `STATUS.md`). Portuguese version: `pandarevive.pt-br.md`.

Status: compiles and passes the upstream CI jobs that run on GitHub-hosted
runners. Never executed on a black panda. No upstream pull request.

## What it is

Two fork branches, both named `revive-f4`:

| Component | Branch | Base | Head |
|---|---|---|---|
| panda firmware | [kriptomad/panda `revive-f4`](https://github.com/kriptomad/panda/tree/revive-f4) (also the submodule [../firmware/panda-revive-f4](../firmware/panda-revive-f4)) | commaai/panda master `1305b78c` (2026-10-25) | `a8225ef3` |
| openpilot host side | [kriptomad/openpilot `revive-f4`](https://github.com/kriptomad/openpilot/tree/revive-f4) | commaai/openpilot master `0152aab4` (2026-10-25) | `941cab937` |

The firmware side is described in
[../hardware/research/pandarevive-scope.md](../hardware/research/pandarevive-scope.md)
(sections 1-6). This document covers the openpilot side added on 2026-10-30.

## Why it was needed

- commaai/panda `3d272335` (2025-07) and `1ce986f7` "bye bye f4" (2025-08)
  removed `board/boards/black.h`, `board/stm32f4/*`, bxCAN, the F4 build
  target and `McuType.F4` / `HW_TYPE_BLACK` from the Python library.
- commaai/openpilot `96d1b876b` (2026-02) removed the libusb transport from
  `pandad` (SPI only) and `9aca13cf2` hardcoded the MCU type to H7. The
  black panda is USB only.

## openpilot branch `revive-f4`

| Commit | Subject | Files |
|---|---|---|
| `45b12a352` | panda: point submodule to the revive-f4 fork | `.gitmodules`, `panda` gitlink -> `a8225ef3` |
| `92b862b5e` | pandad: restore USB comms for external pandas | `selfdrive/pandad/panda_comms.h`, `usb.cc` (new, the old `panda_comms.cc`), `spi.cc`, `panda.cc`, `panda.h`, `SConscript` |
| `c1e41b44b` | pandad: flash an external panda through its own bootloader request | `selfdrive/pandad/pandad.py` |
| `941cab937` | pandad: cover the black panda in the host side tests | `tests/test_pandad_canprotocol.cc`, `tests/test_pandad_flash.py` (new) |

What changed in behaviour:

- `pandad` tries USB (`PandaUsbHandle`, VID 0x3801 PID 0xddcc) before SPI;
  `Panda::list()` returns USB and SPI serials.
- On a PC (`COMMA_HARDWARE` false) `flash_panda()` asks the firmware to
  enter the bootstub and then the ST bootloader before `PandaDFU.recover()`
  and `Panda.flash()`; on a comma device the SoM reset lines are used as
  before.
- The panda submodule is the fork, so `scons` builds
  `panda/board/obj/panda.bin.signed` (F4) next to `panda_h7.bin.signed`,
  and the Python library knows `McuType.F4` / `HW_TYPE_BLACK` again.

Nothing was changed in opendbc (shared safety code), in
`common/hardware` (`HardwarePc` is used as is), in cereal
(`blackPanda @3` was never removed) or in the process configuration.

## CI

GitHub does not run workflows on the `kriptomad/openpilot` fork, so the
tree of `941cab937` was pushed to the pandarevive repository
(branch `ci/openpilot-revive-f4`) and run there:
https://github.com/kriptomad/pandarevive/actions/runs/41112766789

build release, build macOS, static analysis, unit tests (957 passed,
49 skipped, 1 xfailed, including the new `test_pandad_flash.py` and the
native `test_pandad_canprotocol`), process replay and Create UI Report:
success. simulator driving: skipped (commaai only). Steps that need commaai
secrets or self-hosted runners do not run on the fork.

## Not done

- No execution on hardware: USB enumeration, bxCAN timing, harness
  detection, DFU entry, F4 self test, MPU regions.
- No upstream pull request.
- `import libusb` in the pandad `SConscript` was only built in the CI
  environment, not inside a comma device image.
- Firmware base `1305b78c` is two firmware-only commits behind the panda
  commit openpilot pinned before (`f38f504f`).

## How to use

```
git clone -b revive-f4 --recurse-submodules https://github.com/kriptomad/openpilot.git
```

To flash a black panda by hand see
[flashing/flash-black-panda-city-g7.md](flashing/flash-black-panda-city-g7.md).

## Relationship to this repository

The Honda City G7 port (tracks A and B) runs on older trees (flowpilot,
openpilot v0.9.9). pandarevive is the path to run the same black panda on
current openpilot master. The Hybrid Panda PCB in
[../hardware/hybrid-panda](../hardware/hybrid-panda) is the hardware
alternative for people without a black panda.
