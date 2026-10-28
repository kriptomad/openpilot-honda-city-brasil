# Reference sources (read-only upstream clones)

These repositories are cloned locally under `02_REFERENCE/` as read-only consultation
sources (firmware, hardware, software). They are **not** committed to this repository
(see `.gitignore`); re-create them with the commands below to reproduce the exact state
used during the reverse-engineering work.

| Folder | Upstream | Pinned commit |
|---|---|---|
| `hardware` | https://github.com/commaai/hardware.git | `a42a475` |
| `harness_tester_challenge` | https://github.com/commaai/harness_tester_challenge.git | `069f724` |
| `neo` | https://github.com/commaai/neo.git | `9869dee` |
| `opendbc` | https://github.com/commaai/opendbc.git | `c395575` |
| `openpilot` | https://github.com/commaai/openpilot.git | `ff47f484e` |
| `openpilot-docs` | https://github.com/commaai/openpilot-docs.git | `8a00765` |
| `panda` | https://github.com/commaai/panda.git | `408e14d` |
| `panda_full` | https://github.com/commaai/panda.git (full history) | `f62adf72` |
| `panda_jungle` | https://github.com/commaai/panda_jungle.git | `b80539f` |
| `panda_legacy_f4` | https://github.com/commaai/panda.git (last STM32F4 / black panda firmware) | `f849893b` |

## Re-clone

```powershell
cd 02_REFERENCE
git clone https://github.com/commaai/hardware.git                  ; git -C hardware                  checkout a42a475
git clone https://github.com/commaai/harness_tester_challenge.git  ; git -C harness_tester_challenge  checkout 069f724
git clone https://github.com/commaai/neo.git                       ; git -C neo                       checkout 9869dee
git clone https://github.com/commaai/opendbc.git                   ; git -C opendbc                   checkout c395575
git clone https://github.com/commaai/openpilot.git                 ; git -C openpilot                 checkout ff47f484e
git clone https://github.com/commaai/openpilot-docs.git            ; git -C openpilot-docs            checkout 8a00765
git clone https://github.com/commaai/panda.git                     ; git -C panda                     checkout 408e14d
git clone https://github.com/commaai/panda.git panda_full          ; git -C panda_full                checkout f62adf72
git clone https://github.com/commaai/panda_jungle.git              ; git -C panda_jungle              checkout b80539f
git clone https://github.com/commaai/panda.git panda_legacy_f4     ; git -C panda_legacy_f4           checkout f849893b
```

`datasheets/` (STM32H725 DS13313 + extracted text) is committed.

## Tools not committed

- `05_SCRIPTS/tools/freerouting/freerouting-2.5.0.jar` (GPL) — download from
  https://github.com/freerouting/freerouting/releases/tag/v2.5.0 ; requires Java 25.
