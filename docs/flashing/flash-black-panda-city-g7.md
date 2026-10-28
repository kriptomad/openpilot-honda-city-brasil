# Flashing a black panda (STM32F413) for the Honda City G7 2023 (Brazil)

Step by step guide to put the forked firmware on a freshly assembled black panda so it
works with the Honda City G7 port. Portuguese version: `flash-black-panda-city-g7.pt-br.md`.

Status: this procedure has NOT been executed on real hardware yet. It was written from the
code in the repositories below and from the PCB files. Treat every step as "expected", not
"verified", until the first board is flashed.

## 0. Quick path for option A (flowpilot APK + Loetkolben black panda)

Windows PowerShell, Python 3.11+ installed. Everything below is explained in detail in the
following sections; this is just the order of operations.

```
git clone -b flowpilot-city-g7-brazil --depth 1 https://github.com/kriptomad/flowpilot-city-g7.git
git clone --depth 1 https://github.com/kriptomad/openpilot-honda-city-brasil.git hub
cd flowpilot-city-g7
pip install libusb1 pyusb

# 1. hold SW1, plug USB-C, release. Zadig: 0483:df11 -> WinUSB
python -c "from panda import PandaDFU; print(PandaDFU.list())"
python -c "from panda import PandaDFU; PandaDFU(None).recover()"

# 2. board comes back as bbaa:ddee. Zadig: WinUSB
python -c "from panda import Panda; Panda().flash(fn=r'..\hub\firmware\prebuilt\flowpilot-black-panda\panda.bin.signed')"

# 3. board comes back as bbaa:ddcc. Zadig: WinUSB
python -c "from panda import Panda; p=Panda(); print(p.get_type(), p.get_version(), p.health()['uptime'])"
# expected: b'\x03' DEV-a2f1983c-DEBUG <number>
```

Then unplug from the PC, plug into the phone with the OTG cable and open the flowpilot app;
it reflashes the application area by itself if the APK carries a newer build.

## 1. What you need

| Item | Notes |
|---|---|
| Black panda PCB | Lukas Loetkolben "Open Source BlackPanda" v2 (OpenpilotHardware/BlackPanda), STM32F413RGT6 (U7). `SW1` pulls `BOOT0` to 3V3 (DFU button), `R14` is the pull-down. `NRST` is not routed to a button. |
| Harness box + car harness | OpenpilotHardware/HarnessBox + Honda Bosch **B** harness (City G7 is radarless Bosch). |
| USB cable | USB-C data cable to a PC for the first flash; USB-C OTG to the phone afterwards. |
| PC | Windows 10/11 or Linux, Python 3.11+ (3.13 works), `pip install libusb1 pyusb`. |
| Windows only | Zadig (https://zadig.akeo.ie) to bind WinUSB to `0483:df11` (STM DFU), `bbaa:ddee` (panda bootstub) and `bbaa:ddcc` (panda app). |
| Linux only | udev rules from the panda README (`/etc/udev/rules.d/11-panda.rules`, VIDs `bbaa`/`3801`, PIDs `ddcc`/`ddee`) plus `0483:df11` for DFU, or run as root. |

## 2. Pick the firmware: three trees, not interchangeable

The City G7 does not need any change inside the panda firmware itself: the car is covered by
`SAFETY_HONDA_BOSCH` with the radarless flag, which every tree below already has. What differs
is the **protocol version** the firmware speaks to the software on the other side of the USB
cable (health packet, CAN packet, USB control requests). Flash the tree that matches the
software you will run.

| Option | Use with | Source | Prebuilt binaries |
|---|---|---|---|
| **A - flowpilot** (phone) | APK from `kriptomad/flowpilot-city-g7` (branch `flowpilot-city-g7-brazil`) | `panda/` directory inside that repo (commaai/panda `abdc4185`, F4 generic target `panda`) | hub repo `firmware/prebuilt/flowpilot-black-panda/` (`panda.bin.signed` SHA256 `A067B0A1...3CB02`, `bootstub.panda.bin` `C3FDFE02...75E76`, version `DEV-a2f1983c-DEBUG`) |
| **B - openpilot 0.9.9 port** (comma-like device or PC) | `kriptomad/openpilot@v0.9.9-cityg7-blackpanda` | `panda` submodule of that branch (commaai/panda `e462c34d`, last upstream with native black panda support) | none here. `scons -j8 panda` at the openpilot root builds `panda/board/obj/`; openpilot's `pandad` also flashes it by itself at startup |
| **C - pandarevive** (this branch `revive-f4`) | future openpilot master + black panda; the openpilot side is still pending (`hardware/research/pandarevive-scope.md` section 7) | `kriptomad/panda@revive-f4` (STM32F4 restored on current panda master, target `panda`) | hub repo `firmware/prebuilt/revive-f4-black-panda/` (`panda.bin.signed` SHA256 `EB07FF3F...991AF`, `bootstub.panda.bin` `3C49135B...EB221`, version `DEV-e78c41e6-DEBUG`) |

Hub repo = `kriptomad/openpilot-honda-city-brasil` (this repository).

Right now the phone/flowpilot path is the one being tested, so **use option A**. Option C
only makes sense for bench tests of the firmware itself (USB enumeration, `health()`, CAN
loopback) until the openpilot side of pandarevive exists. To switch between trees later,
repeat the full DFU procedure (section 5), do not just flash the app.

All trees are signed with comma's public **debug** key (`certs/debug`). Our bootstub accepts
debug-signed apps; a comma release bootstub would not, which is irrelevant here because the
board starts empty.

## 3. (Optional) build the binaries yourself

Skip this if you use the prebuilt files from the table above.

### 3.1 Option A (flowpilot tree)

```
# Linux / WSL2 (needs gcc-arm-none-eabi, scons)
cd flowpilot
scons -j8 panda            # outputs panda/board/obj/{bootstub.panda.bin,panda.bin.signed}

# Windows (PowerShell, arm-none-eabi-gcc in PATH, repo venv active)
cd flowpilot\panda
python -m SCons -f local_build_windows.scons -j8   # helper committed in the flowpilot fork; original in hardware/research/local-build-windows.scons
```

### 3.2 Option B (openpilot 0.9.9 tree)

```
# Linux / WSL2, inside the openpilot clone (submodules checked out, toolchain installed)
scons -j8 panda            # outputs panda/board/obj/{bootstub.panda.bin,panda.bin.signed}
```

### 3.3 Option C (this branch, `revive-f4`)

Requirements: `arm-none-eabi-gcc` in PATH, `scons`, and the `opendbc` package importable
(`pip install -e <opendbc clone>` or `PYTHONPATH=<opendbc clone>`; the safety headers come from
`opendbc.INCLUDE_PATH`).

```
# Linux / WSL2
cd panda
scons -j8                  # builds panda (F4), panda_h7, body_h7 and tests/libpanda

# Windows (PowerShell)
cd panda
$env:PATH = "<toolchain>\bin;" + $env:PATH
$env:PYTHONPATH = "<opendbc clone>"
python -m SCons -j8 board
# The last lines complain that tests/libpanda cannot build a .dll on Windows. That is the
# host-side test library only; the firmware in board\obj\ is complete.
```

Outputs: `board/obj/bootstub.panda.bin` (bootstub, 0x08000000) and `board/obj/panda.bin.signed`
(application, 0x08004000). `board/obj/version` holds the version string
(`DEV-<git>-DEBUG`).

## 4. Set up the Python side on the PC

Each tree ships the `panda` Python package next to the firmware; use the one from the tree
you chose so `FW_PATH` points at the right `board/obj/`.

```
pip install libusb1 pyusb

# Option A: run from the flowpilot repo root (the package is flowpilot/panda)
cd flowpilot

# Option B: run from the openpilot repo root (the package is openpilot/panda)
cd openpilot

# Option C: install this branch in editable mode
cd panda
pip install -e .
```

Sanity check (no board connected yet):

```
python -c "from panda import Panda, PandaDFU; print(Panda.list(), PandaDFU.list())"
# expected: [] []
```

Windows: after the first time each USB identity shows up (`0483:df11`, `bbaa:ddee`,
`bbaa:ddcc`), open Zadig, pick the device, choose **WinUSB**, click Install/Replace Driver.
You will do this up to three times during section 5.

## 5. First flash of an empty board (DFU)

A new STM32F413 has no bootstub, so the only way in is the ST ROM bootloader over USB (DFU).

1. Board unpowered (nothing on USB, harness box not connected).
2. Hold `SW1` (the small tactile switch wired to `BOOT0`).
3. While holding it, plug the USB-C cable into the PC. Release `SW1` after about one second.
4. Confirm the DFU device:
   - Windows: Device Manager shows "STM32 BOOTLOADER" (or an unknown device `0483:df11`).
     Bind WinUSB with Zadig if needed.
   - Linux: `lsusb | grep 0483:df11`.
   - Python: `python -c "from panda import PandaDFU; print(PandaDFU.list())"` prints one serial.
5. Write the bootstub. `recover()` erases sectors 0 and 1, programs `bootstub.panda.bin` at
   0x08000000 and jumps to it. **It does not write the application.**

   ```
   python -c "from panda import PandaDFU; PandaDFU(None).recover()"
   ```

6. The board re-enumerates as the panda bootstub `bbaa:ddee` (Windows: Zadig/WinUSB again).
   Check: `python -c "from panda import Panda; p=Panda(); print(p.bootstub, p.get_type())"`
   -> `True b'\x03'` (`HW_TYPE_BLACK_PANDA`).
7. Write the application from `board/obj/panda.bin.signed` (default path of `flash()`):

   ```
   python -c "from panda import Panda; p=Panda(); p.flash(); print('ok')"
   ```

   To flash a file from somewhere else (for example the prebuilt one from the hub repo):

   ```
   python -c "from panda import Panda; Panda().flash(fn=r'<path>\panda.bin.signed')"
   ```

8. The board resets into the app `bbaa:ddcc` (Windows: Zadig/WinUSB one last time). Verify:

   ```
   python -c "from panda import Panda; p=Panda(); print(p.get_type(), p.get_version(), p.get_signature().hex()[:16], p.health()['uptime'])"
   ```

   Expected: `b'\x03' DEV-a2f1983c-DEBUG ...` for option A, `DEV-<git>-DEBUG` of the openpilot
   panda submodule for option B, or `b'\x03' DEV-e78c41e6-DEBUG ...` for option C (the git
   hash follows whatever commit you built). `health()` must not raise.

Equivalent one-shot scripts on Linux (they run `scons` first, so they need the toolchain):
`python board/recover.py` (DFU -> bootstub) followed by `python board/flash.py` (app).

If the board does not show up as `0483:df11` in step 4: check that `SW1` really was held
during power-up, check 3V3 on the MCU, and check the USB data lines (USB-C cable with data,
not charge-only). An unknown device `bbaa:xxxx` means a bootstub/app is already there and
the button was not held.

## 6. Later updates

- **Option A (phone)**: nothing to do. When the panda is plugged into the phone,
  `ServicePandad` runs `pandaflash`, which compares the running signature with the
  `panda.bin.signed` packed in the APK and reflashes the application area if it differs. It
  never touches the bootstub. So every new APK build (always debug-signed) is accepted.
- **Option B (openpilot 0.9.9)**: nothing to do either. `selfdrive/pandad/pandad.py` checks
  the signature at every start and flashes `panda/board/obj/panda.bin.signed` when it differs
  (it can also recover a board stuck in bootstub).
- **Option C (PC)**: `python board/flash.py` (or `Panda().flash()` after a rebuild).
- **Changing tree (A / B / C)**: put the board back in DFU with `SW1` and redo section 5 so the
  bootstub and the app come from the same tree.
- **Soft re-entry into DFU** when a firmware is already running (no button):
  `python -c "from panda import Panda; p=Panda(); p.reset(enter_bootstub=True); p.reset(enter_bootloader=True)"`.

## 7. First connection to the car (checklist, not executed yet)

1. Harness box in the car, Bosch B harness between camera and car, panda on the harness box,
   phone (option A) on the panda USB-C via OTG. Ignition ON, engine can stay off.
2. Option A: in the flowpilot settings set the car to `HONDA CITY 7G` (param `Mycar`,
   see `../../software/flowpilot-port/port-city-flowpilot.md` section 8.3) or let the CAN fingerprint pick it.
3. Expected panda state once `controlsd` is up (query from a PC with the panda temporarily on
   the PC, or read the flowpilot log): `health()['safety_mode'] == 20`
   (`SAFETY_HONDA_BOSCH` in the flowpilot tree) and `safety_param` with bit 8 set
   (`FLAG_HONDA_RADARLESS`). In the `revive-f4` tree the numeric ids come from opendbc
   (`opendbc/safety`), check them there.
4. Watch `carState` (speed, steering angle, pedals, cruise buttons) before any engagement.
5. Do not engage until the fingerprint says `HONDA CITY 7G`, `canErrorCounter` stays at 0 and
   the alerts are clean for a few minutes of driving with openpilot disengaged.

## 8. References

- `python/constants.py` (`F4Config`: sectors, bootstub 0x08000000, app 0x08004000),
  `python/dfu.py` (`recover()`), `python/__init__.py` (`Panda.flash()`, `get_mcu_type()`).
- `SConscript` (`base_project_f4`, target `panda`).
- flowpilot side: `wrappers/pandaflash.cpp`, `android/.../ServicePandad.java`,
  `panda/python/__init__.py` (`FLAG_HONDA_RADARLESS = 8`).
- PCB: `OpenpilotHardware/BlackPanda/kicad_project/BlackPanda.kicad_pcb` (nets `Net-(U7-BOOT0)`,
  parts `SW1`, `R14`).
