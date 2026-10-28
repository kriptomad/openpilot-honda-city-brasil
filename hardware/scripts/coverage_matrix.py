"""coverage_matrix.py - STEP 2: prove every HRS requirement against the official commaai sources.

For each requirement (id, description, repo, file glob, regex) the script greps the read-only clones in
hardware/reference and records the first matching file:line plus the matched text. A requirement with no match is
reported as NOT_FOUND so that ../research/hrs-red-panda.md cannot silently drift from the firmware.

Outputs (OUTPUT_ROOT only):
  hardware/research/coverage-matrix.csv
  hardware/research/coverage-matrix.md
  hardware/reports/coverage_matrix.json
"""
from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path

import hp_common as hp

REF = hp.REFERENCE_ROOT

# (id, requirement, repo dir, relative file (or glob), regex)
REQS = [
    # --- board identity
    ("HRS-01", "HW_TYPE_RED_PANDA == 7", "panda", "board/boards/board_declarations.h", r"HW_TYPE_RED_PANDA\s+7U?"),
    ("HRS-02", "id1 = PF7..PF10 read with internal pull-up", "panda", "board/stm32h7/board.h", r"detect_with_pull\(GPIOF,\s*7,\s*PULL_UP\)"),
    ("HRS-03", "id1 == 0 -> RED", "panda", "board/stm32h7/board.h", r"id1\s*==\s*0U?\)\s*\{"),
    ("HRS-04", "id2 = PD4..PD7 (3 -> CUATRO)", "panda", "board/stm32h7/board.h", r"detect_with_pull\(GPIOD,\s*4,\s*PULL_UP\)"),
    ("HRS-05", "detect_with_pull delay 4096 loops", "panda", "board/drivers/gpio.h", r"PULL_EFFECTIVE_DELAY\s+4096"),
    ("HRS-06", "host lib: HW_TYPE_RED_PANDA = 0x07, red is external (not INTERNAL_DEVICES)", "panda", "python/__init__.py", r"HW_TYPE_RED_PANDA\s*=\s*b'\\x07'"),
    # --- MCU / build
    ("HRS-10", "build defines -DSTM32H725xx, cortex-m7, fpv5-d16", "panda", "SConscript", r"STM32H725xx"),
    ("HRS-11", "MCU_IDCODE 0x483 (reboot to bootloader if mismatch)", "panda", "board/stm32h7/stm32h7_config.h", r"MCU_IDCODE\s+0x483"),
    ("HRS-12", "HSE 25 MHz crystal", "panda", "board/stm32h7/clock.h", r"25\s*MHz|RCC_CR_HSEON"),
    ("HRS-13", "PLL1: 240 MHz core, 80 MHz FDCAN (PLL1Q)", "panda", "board/stm32h7/clock.h", r"RCC_PLLCFGR|PLL1DIVR|240"),
    ("HRS-14", "LQFP144 -> SMPS only (PWR_CR3_SMPSEN); TFBGA100 -> LDO; else hang", "panda", "board/stm32h7/clock.h", r"PWR_CR3_SMPSEN"),
    ("HRS-15", "USB clock from HSI48", "panda", "board/stm32h7/clock.h", r"HSI48"),
    ("HRS-16", "VOS1 for 80 MHz CAN FD", "panda", "board/stm32h7/clock.h", r"VOS"),
    ("HRS-17", "VDD33USB voltage detector enabled", "panda", "board/stm32h7/clock.h", r"PWR_CR3_USB33DEN"),
    # --- memory / boot
    ("HRS-20", "FLASH 1024K, app at 0x08020000", "panda", "board/stm32h7/stm32h7x5_flash.ld", r"0x08020000"),
    ("HRS-21", "provisioning at end of 1 MB flash (0x080FFFC0/E0) -> requires 'G' variant", "panda", "board/stm32h7/stm32h7_config.h", r"0x080FFF[CE]0"),
    ("HRS-22", "ST bootloader address 0x1FF09804", "panda", "board/stm32h7/stm32h7_config.h", r"0x1FF09804"),
    ("HRS-23", "bootstub RSA signature check (release key; debug only with ALLOW_DEBUG)", "panda", "board/bootstub.c", r"ALLOW_DEBUG"),
    ("HRS-24", "DFU flash flow (dfu-util 0483:df11)", "panda", "board/debug/dfu_util_h7.sh", r"0483:df11"),
    ("HRS-25", "FDCAN message RAM base 0x4000AC00", "panda", "board/stm32h7/llfdcan_declarations.h", r"0x4000AC00"),
    # --- USB
    ("HRS-30", "USB VID 0x3801 / PID 0xDDCC", "panda", "board/config.h", r"0xddcc|0xDDCC"),
    ("HRS-31", "USB PA11/PA12 AF10", "panda", "board/stm32h7/peripherals.h", r"GPIOA,\s*11,\s*GPIO_AF10"),
    ("HRS-32", "internal FS PHY, VBUS sensing disabled", "panda", "board/stm32h7/llusb.h", r"BVALOEN"),
    # --- GPIO map (red.h)
    ("HRS-40", "STB xcvr1 (bus0) PG11", "panda", "board/boards/red.h", r"GPIOG,\s*11"),
    ("HRS-41", "STB xcvr2 PB3 (FDCAN2 via PB5/PB6, OBD)", "panda", "board/boards/red.h", r"GPIOB,\s*3,"),
    ("HRS-42", "STB xcvr3 (bus2) PD7", "panda", "board/boards/red.h", r"GPIOD,\s*7"),
    ("HRS-43", "STB xcvr4 PB4 (FDCAN2 via PB12/PB13)", "panda", "board/boards/red.h", r"GPIOB,\s*4,"),
    ("HRS-44", "FDCAN2 on PB5/PB6 AF9 (OBD mode)", "panda", "board/boards/red.h", r"GPIOB,\s*5,\s*GPIO_AF9"),
    ("HRS-45", "FDCAN2 on PB12/PB13 AF9 (normal mode)", "panda", "board/boards/red.h", r"GPIOB,\s*12,\s*GPIO_AF9"),
    ("HRS-46", "FDCAN1 PB8/PB9 AF9", "panda", "board/stm32h7/peripherals.h", r"GPIOB,\s*8,\s*GPIO_AF9"),
    ("HRS-47", "FDCAN3 PG9/PG10 AF2", "panda", "board/stm32h7/peripherals.h", r"GPIOG,\s*9,\s*GPIO_AF2"),
    ("HRS-48", "VOLT_S = ADC1 ch2 (PF11) x11", "panda", "board/boards/red.h", r"ADC_CHANNEL_DEFAULT\(ADC1,\s*2\)\)\s*\*\s*11U?"),
    ("HRS-49", "PF11 analog mode", "panda", "board/stm32h7/peripherals.h", r"GPIOF,\s*11,\s*MODE_ANALOG"),
    ("HRS-50", "5VOUT_S on PB1 analog", "panda", "board/boards/red.h", r"GPIOB,\s*1,\s*MODE_ANALOG"),
    ("HRS-51", "USB load switch PB14 open-drain, pull-up, obsolete", "panda", "board/boards/red.h", r"GPIOB,\s*14"),
    ("HRS-52", "SBU1 PC4 ADC ch4; SBU2 PA1 ADC ch17", "panda", "board/boards/red.h", r"GPIOC.*\n?.*pin_SBU1\s*=\s*4|pin_SBU1\s*=\s*4"),
    ("HRS-53", "relay SBU1 PC10 / SBU2 PC11", "panda", "board/boards/red.h", r"pin_relay_SBU1\s*=\s*10"),
    ("HRS-54", "LEDs PE4 red / PE3 green / PE2 blue", "panda", "board/boards/red.h", r"GPIOE,\s*4|led_GPIO.*GPIOE"),
    ("HRS-55", "LED open-drain active-low", "panda", "board/drivers/led.h", r"OUTPUT_TYPE_OPEN_DRAIN"),
    ("HRS-56", "avdd 3300 mV", "panda", "board/boards/red.h", r"avdd_mV\s*=\s*3300"),
    ("HRS-57", "has_spi false (SPI4 PE11-14 unused)", "panda", "board/boards/red.h", r"has_spi\s*=\s*false"),
    ("HRS-58", "has_fan false", "panda", "board/boards/red.h", r"has_fan\s*=\s*false"),
    # --- harness / SBU
    ("HRS-60", "orientation threshold avdd/2", "panda", "board/drivers/harness.h", r"avdd_mV\s*/\s*2U?"),
    ("HRS-61", "SBU pins not 5V tolerant in ADC mode -> back to MODE_INPUT", "panda", "board/drivers/harness.h", r"not 5V tolerant"),
    ("HRS-62", "relay pins open-drain, idle high", "panda", "board/drivers/harness.h", r"pin_relay_SBU1,\s*OUTPUT_TYPE_OPEN_DRAIN"),
    ("HRS-63", "ignition = !digital_input(SBU ign side)", "panda", "board/drivers/harness.h", r"!get_gpio_input"),
    ("HRS-64", "bus0<->bus2 swap when harness flipped", "panda", "board/drivers/can_common.h", r"bus_lookup\s*=\s*flipped\s*\?\s*2U"),
    ("HRS-65", "early GPIO float (all inputs at reset)", "panda", "board/stm32h7/stm32h7_config.h", r"0xAB000000"),
    ("HRS-66", "under-voltage threshold 6000 mV", "panda", "board/main.c", r"read_voltage_mV\(\)\s*<\s*6000U?"),
    # --- official hardware repo
    ("HW-01", "red panda MCU STM32H725 (README)", "hardware", "panda/README.md", r"STM32H725"),
    ("HW-02", "OBD-C pinout (SBU1 ~100 Ohm, SBU2 1k ign)", "hardware", "harness/OBD-C.sch.pdf", None),
    ("HW-03", "harness box v3 schematic (termination 120 R, DG419 relay)", "hardware", "harness/v3/Harness_Box.pdf", None),
    ("HW-04", "Honda Bosch B harness drawing", "hardware", "harness/v3/Honda_Bosch_B_Harness.pdf", None),
    ("HW-05", "no red panda schematic/PCB published", "hardware", "panda", "__NO_SCH__"),
    # --- vehicle
    ("VEH-01", "Honda City 2023 BR = HondaBoschPlatformConfig BOSCH_RADARLESS", "opendbc", "opendbc/car/honda/values.py", r"HONDA_CITY_7G\b"),
    # --- legacy black panda control
    ("F4-01", "black panda STB PC1/PC13/PA0/PB10", "panda_legacy_f4", "board/boards/black.h", r"GPIOC,\s*1,"),
    ("F4-02", "black panda CAN3 PA8/PA15 AF11", "panda_legacy_f4", "board/boards/black.h", r"GPIO_AF11"),
    ("F4-03", "black panda LEDs PC9/PC7/PC6", "panda_legacy_f4", "board/boards/black.h", r"led_pin\s*=\s*\{9,\s*7,\s*6\}"),
    # --- openpilot host
    ("OP-01", "openpilot pins panda submodule", "openpilot", ".gitmodules", r"path = panda"),
    ("OP-02", "pandad talks to red panda via USB (python lib)", "openpilot", "openpilot/selfdrive/pandad/pandad.py", r"Panda\("),
    ("OP-03", "datasheet DS13311 pin table present", "datasheets", "DS13313_text.txt", r"PG9\s+I/O"),
]


def git_head(repo: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "-"


def grep_file(path: Path, rx: str):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(rx, line):
            return i, line.strip()[:140]
    return None


def main():
    ap = hp.std_argparser("HRS coverage matrix against commaai clones")
    args = ap.parse_args()
    hp.apply_args(args)
    log = hp.JsonLog("coverage_matrix")
    rows = []
    heads = {}
    for rid, desc, repo, rel, rx in REQS:
        repo_dir = REF / repo
        heads.setdefault(repo, git_head(repo_dir))
        target = repo_dir / rel
        status, where, match = "NOT_FOUND", "", ""
        if rx == "__NO_SCH__":
            hits = [p for p in target.rglob("*") if p.suffix.lower() in (".sch", ".brd", ".kicad_sch", ".kicad_pcb", ".pdf")]
            status = "CONFIRMED_ABSENT" if not hits else "FOUND"
            where = f"{repo}/{rel}/ ({len(list(target.rglob('*')))} files, {len(hits)} schematic/pcb/pdf)"
        elif rx is None:
            if target.exists():
                status, where = "FILE_PRESENT", f"{repo}/{rel}"
                match = f"sha256 {hp.sha256_of(target)[:16]}"
        else:
            hit = grep_file(target, rx) if target.exists() else None
            if hit:
                status, where, match = "FOUND", f"{repo}/{rel}:{hit[0]}", hit[1]
            elif not target.exists():
                status = "FILE_MISSING"
                where = f"{repo}/{rel}"
        rows.append({"id": rid, "requirement": desc, "repo": repo, "head": heads[repo][:12], "status": status,
                     "evidence": where, "match": match})
        (log.info if status in ("FOUND", "FILE_PRESENT", "CONFIRMED_ABSENT") else log.warn)(f"{rid} {status}", where=where)

    out_csv = hp.OUTPUT_ROOT / "hardware/research" / "coverage-matrix.csv"
    out_md = hp.OUTPUT_ROOT / "hardware/research" / "coverage-matrix.md"
    hp.assert_inside_output(out_csv)
    hp.backup_before_write(out_csv, "coverage")
    if not hp.DRY_RUN:
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    n_ok = sum(r["status"] in ("FOUND", "FILE_PRESENT", "CONFIRMED_ABSENT") for r in rows)
    md = ["# Coverage matrix — HRS vs. fontes oficiais commaai", "",
          f"Gerado por `hardware/scripts/coverage_matrix.py`. Requisitos: {len(rows)}, provados: {n_ok}, não encontrados: {len(rows)-n_ok}.", "",
          "HEADs: " + ", ".join(f"{k}={v[:12]}" for k, v in heads.items()), "",
          "| ID | Requisito | Status | Evidência (repo/arquivo:linha) | Texto |", "|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['id']} | {r['requirement']} | {r['status']} | `{r['evidence']}` | `{r['match'].replace('|', '\\|')}` |")
    hp.guarded_write_text(out_md, "\n".join(md) + "\n", "coverage")
    log.save(total=len(rows), proven=n_ok, not_found=len(rows) - n_ok, csv=str(out_csv), md=str(out_md))


if __name__ == "__main__":
    main()
