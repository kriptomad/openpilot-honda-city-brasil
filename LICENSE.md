# Licenses

This repository combines original work by Bruno Costa (kriptomad) with material derived
from, or built on top of, several upstream projects. The table below is the license
inventory kept during development (dated 2026-10-23), with the paths adjusted to this
repository's layout. Upstream license texts are in [licenses/](licenses).

## Original work in this repository

Copyright (c) 2026 Bruno Costa. Two licenses apply to the author's own work, by area:

- **Hardware** - the Hybrid Panda design and its outputs ([hardware/hybrid-panda](hardware/hybrid-panda),
  [hardware/fabrication](hardware/fabrication), [hardware/reports](hardware/reports),
  [hardware/research](hardware/research)) are released under the
  **CERN Open Hardware Licence Version 2 - Strongly Reciprocal (CERN-OHL-S-2.0)**,
  text in [licenses/cern-ohl-s-2.0.txt](licenses/cern-ohl-s-2.0.txt). The project is a
  derivative of lukasloetkolben/OpenBlackPanda (MIT); the original MIT notice is kept and
  the MIT-licensed portions remain available under MIT as required by that license.
  Source location for CERN-OHL-S purposes: https://github.com/kriptomad/openpilot-honda-city-brasil
- **Software and documentation** - scripts ([hardware/scripts](hardware/scripts),
  [software/openpilot-port/tools](software/openpilot-port/tools)), port patches, firmware
  branch modifications, prebuilt binaries and all documentation ([docs](docs), readmes,
  reports text) are released under the **MIT License**, text in
  [licenses/license-mit-bruno-costa.txt](licenses/license-mit-bruno-costa.txt).

A file that states a different license keeps that license. Documentation that reproduces
upstream text keeps the upstream notice.

## Inventory of upstream sources

| Source | Where used | Commit | License | Text | Use in this project |
|---|---|---|---|---|---|
| lukasloetkolben/OpenBlackPanda (baseline) | [archive/baseline-original](archive/baseline-original), derived in [hardware/hybrid-panda](hardware/hybrid-panda) | see [archive/manifests](archive/manifests) | MIT (c) 2023 Lukas | [licenses/license-open-black-panda.txt](licenses/license-open-black-panda.txt) | KiCad base (schematic/PCB) the Hybrid Panda derives from; black panda hardware used by the firmware/software tracks |
| commaai/panda | reference clone (not included); forks as submodules [firmware/panda-revive-f4](firmware/panda-revive-f4), [firmware/panda-hybrid-h725](firmware/panda-hybrid-h725) | 408e14d4 (reference); a8225ef3 / 78e37994 (forks) | MIT (c) 2016 Comma.ai, Inc. | [licenses/license-panda-mit.txt](licenses/license-panda-mit.txt) | Firmware = hardware specification; firmware to be flashed; prebuilt binaries in [firmware/prebuilt](firmware/prebuilt) |
| commaai/panda (full history, legacy F4 worktree) | reference clone (not included) | f62adf72 / f849893b | MIT | idem | Black panda F4 control |
| commaai/opendbc | reference clone (not included); fork as submodule [software/opendbc-v0.9.9-city-g7](software/opendbc-v0.9.9-city-g7) | c3955753 (reference); 6cbc8005 (fork) | MIT (c) 2020 Comma.ai, Inc. | [licenses/license-opendbc.txt](licenses/license-opendbc.txt) | Vehicle confirmation (P1); Honda City port |
| commaai/openpilot | reference clone (not included); fork as submodule [software/openpilot-v0.9.9-city-g7](software/openpilot-v0.9.9-city-g7) | ff47f484 (reference); 9ad0dbb08 (fork) | MIT (c) 2018 Comma.ai, Inc. | `LICENSE` inside the submodule | Host software (pandad, hardware/, Honda) - D-06; v0.9.9 City port |
| openpilot submodules: opendbc_repo b3bd79a6, msgq_repo a95f3c1c, rednose_repo 8671c17c, teleoprtc_repo 1aa8fc43 | inside openpilot | - | MIT | each repo | host analysis |
| openpilot tinygrad_repo | inside openpilot | 02e69816 | MIT (c) 2024 the tiny corp | `tinygrad_repo/LICENSE` | not used |
| flowdriveai/flowpilot and jagheterfredrik/flowpilot | fork as submodule [software/flowpilot-city-g7](software/flowpilot-city-g7) | 9ea918ea (base); 94248de (fork) | see `LICENSE` inside the submodule | inside the submodule | Standalone Android APK track |
| commaai/neo | reference clone (not included) | 9869dee9 (archived) | MIT (c) 2016 comma.ai | `LICENSE.neo` | historic comma hardware reference |
| commaai/hardware | reference clone (not included) | a42a4752 | **No LICENSE file**; harness v3 PDFs say "comma.ai - you can copy this!" | - | OBD-C pinout, harness box, Honda Bosch B (P10). Treated as "all rights reserved except where the PDFs grant permission"; **the PDFs are not redistributed** here |
| commaai/panda_jungle | reference clone (not included) | b80539fc (archived) | **No LICENSE** | - | consultation only |
| commaai/harness_tester_challenge | reference clone (not included) | 069f7243 | MIT (c) 2024 comma.ai | repo LICENSE | consultation only |
| commaai/openpilot-docs | reference clone (not included) | 8a007654 | **No LICENSE** | - | consultation only |
| STMicroelectronics DS13313 (STM32H725xE/G) | [hardware/reference/datasheets](hardware/reference/datasheets) | - | (c) ST; public document, redistribution subject to ST terms | - | Pinout/AF/electrical data. Not included in the fabrication package; cited by document number |
| Freerouting 2.5.0 | not included (used as a tool) | - | GPL-3.0 | upstream | Autorouting of the Hybrid Panda board |
| KiCad | not included (used as a tool) | 10.0.7 | GPL-3.0 (application); library licenses apply to bundled footprints | upstream | EDA tool and kicad-cli exports |

## Obligations

- Works derived from the OpenBlackPanda baseline ([hardware/hybrid-panda](hardware/hybrid-panda),
  [hardware/fabrication](hardware/fabrication)) must keep the MIT notice of Lukas Loetkolben
  (2023) and add their own notice.
- Flashed firmware = commaai/panda MIT: keep the notice. The `revive-f4` and `hybrid-h725`
  branches modify the firmware; the modifications are published in the forks under the same
  license.
- Keys: `board/crypto/certs/debug` is public (MIT); the comma release key is **not** public,
  see HRS section 7 (RESTRICTION) in [hardware/research/hrs-red-panda.md](hardware/research/hrs-red-panda.md).

## Note on Git LFS (openpilot)

openpilot's `.lfsconfig` points to `https://huggingface.co/commaai/openpilot-lfs.git`, which
answers 403 to anonymous clients. The reference clone was made with `GIT_LFS_SKIP_SMUDGE=1`
plus `filter.lfs.smudge --skip`; 253 LFS files (images, binaries, models) stayed as pointers.
None of them is needed for the hardware/host analysis (source code is plain text). Recorded
in D-10 of [docs/decisions.md](docs/decisions.md).
