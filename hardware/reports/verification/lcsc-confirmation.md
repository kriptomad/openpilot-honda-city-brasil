# Hybrid Panda - LCSC code confirmation (software-only)

Status: verified by software only. Nothing was physically verified. No order was placed, no JLCPCB quote was run.

Machine-readable result: `lcsc-confirmation.csv` (one row per BOM line = unique LCSC code + MPN + footprint; 50 rows, 119 refs, fiducials excluded).

## Scope and method

- Input BOM: `docs/hardware/bom.csv` (authoritative; 125 rows incl. FID1-6; 119 component refs, 117 with an LCSC code, 48 unique codes). Cross-checked against `hardware/reports/bom-real/BOM_HYBRIDPANDA_v1.csv` and `hardware/fabrication/assembly/BOM_JLC.csv` (consistent, see notes).
- Footprint per ref taken from the PCB snapshot `work/snapshot.kicad_pcb` (copy of `hardware/hybrid-panda/HybridPanda.kicad_pcb`, SHA-256 `BB274802...63AD`, mtime 2026-10-28 15:36) parsed with KiCad 10 pcbnew Python (`hardware/reports/footprint-audit/footprint_dump.py`), output `work/board_dump.json`.
- Catalog source: offline jlcparts dataset (yaqwsx/jlcparts, table `jlc_components`, `present = 1`), snapshot fetched 2026-10-15. Raw rows in `work/jlc_rows.json`. Stock, Basic/Extended class and price are as of that date and will drift.
- For codes missing from the cache: one web search per code (JLCPCB part page). jlcpcb.com and lcsc.com direct fetches are blocked by the corporate proxy (TLS), so stock/class could not be refreshed online.
- Match logic: `OK` = code exists, catalog MPN equals BOM MPN (whitespace/case-insensitive, suffix tolerant) and catalog package family corresponds to the PCB footprint; `MPN mismatch` = code exists but is a different part; `package mismatch` = package family differs; `not found` = code absent; `exists (web only)` = absent from cache but confirmed on the web; `no LCSC code` = BOM has no code.

## Counts

| Result | BOM lines | Refs |
|---|---:|---:|
| OK | 45 | 112 |
| MPN mismatch (wrong code in BOM) | 2 | 3 |
| exists (web only; stock/class not verified) | 1 | 2 |
| package mismatch | 0 | 0 |
| not found | 0 | 0 |
| no LCSC code | 2 | 2 |
| Total | 50 | 119 |

Basic parts (no extended-part fee): 16 lines (C307331, C1555, C15195, C23630, C1530, C15850, C52923, C19666, C23733, C1002, C25804, C11702, C25744, C25076, C25092, C9006). All other lines are Extended.

## Items that need action

| Refs | BOM MPN | LCSC in BOM | Problem | Suggested fix |
|---|---|---|---|---|
| C23, C24 | 0402CG180J500NT (18 pF) | C1555 | C1555 is 0402CG220J500NT = 22 pF. Wrong value for the 25 MHz crystal load caps. | Use C1549 (0402CG180J500NT, Fenghua, Basic, stock ~914k). Human to confirm the 18 pF choice against Y1 CL. |
| C64 | CL05A225MP5NSNC (2.2 uF 10 V) | C23733 | C23733 is CL05A475MP5NRNC = 4.7 uF 10 V. | Use C444845 (CL05A225MP5NSNC, Extended, ~203k) or C12530 (CL05A225MQ5NSNC 6.3 V, Basic) if 6.3 V rating is acceptable for that net. |
| C4, C12 | CL21A106KBYQNNE (10 uF 50 V 0805) | C2932476 | Not in the offline cache (2026-10-15). Web search confirms the part page exists (0805, 10 uF, 50 V, X5R). Stock and Basic/Extended class not verified. | Keep, or switch to C15850 CL21A106KAYNNNE (25 V, Basic, already used for C42) if the net allows 25 V. |
| U1 | AP22615AWU-7 (Diodes, SOT-23-6 load switch) | none | Former code C2680357 is no longer in the JLC catalog; no AP22615 row at all in the cache. | Human decision: source via LCSC/other distributor as consigned part, or select a pin-compatible SOT-23-6 load switch available at JLC. Not resolved here. |
| JP1 | solder jumper | none | No part; expected. | None. |
| D1 | SMAJ16CA (Littelfuse in BOM) | C148217 | Code resolves to SMAJ16CA-13-F, Diodes Inc. Function/package equal; BOM manufacturer field is inconsistent. | Update BOM manufacturer/MPN to the Diodes part or pick a Littelfuse code. |

Low stock at cache date (risk for a 5-10 board run, re-check before ordering): U7 STM32H725ZGT6 C730156 = 132; Q1/Q2 DDTA143ECA-7-F C460029 = 187 (unbranded alternatives C52205285/C52205286 exist, not verified); J1 C150517 = 809; D2 C22648 = 984; D15 C571379 = 1174; L5 C337891 = 1351; P1 C129018 = 1956.

Other notes: U12 C74193 catalog package is plain SOP-8 (no exposed pad) while the footprint `Diodes_PSOP-8` carries four copper-only EP pads (no mask/paste opening) - harmless, see footprint report. U8-U11 C131480 has an empty manufacturer field in the cache (MPN TJA1042TK/3/1J, NXP).

## Critical parts - catalog record and datasheet link

The link is the one stored in the catalog record. JLC-hosted links (`jlcpcb.com/api/file/...`) could not be fetched from this network; TI and NXP links were fetched (TI) or are blocked (NXP 403/404). "exists" means the field is present in the record, not that the file was opened.

| Refs | BOM MPN | LCSC | Catalog package | Stock | Class | USD @10 | Datasheet link in catalog |
|---|---|---|---|---:|---|---:|---|
| U7 | STM32H725ZGT6 | C730156 | LQFP-144(20x20) | 132 | Extended | 15.74 | exists (JLC file id 8588907820838); local copy `hardware/reference/datasheets/DS13313_STM32H725_ae.pdf` |
| U8-U11 | TJA1042TK/3/1J | C131480 | HVSON-8-EP(3x3) | 14645 | Extended | 0.73 | https://www.nxp.com/docs/en/data-sheet/TJA1042.pdf (exists; fetch blocked from this network) |
| U6 | TPS5450DDAR | C114425 | SOP-8-EP-150mil | 32560 | Extended | 1.86 | https://www.ti.com/cn/lit/ds/symlink/tps5450.pdf (fetched, `work/ds/tps5450.pdf`) |
| U12 | XL1509-3.3E1 | C74193 | SOP-8 | 34166 | Extended | 0.30 | exists (JLC file id 8586176010706) |
| L5 | DFE201610E-2R2M=P2 | C337891 | 0806 | 1351 | Extended | 0.14 | exists (JLC file id 8588918748858); Murata PDF fetched from murata.com |
| Y1 | X322525MOB4SI | C9006 | SMD3225-4P | 216729 | Basic | 0.10 | exists (JLC file id 8756945091237) |
| P1 | TYPE-C-31-M-04 | C129018 | SMD | 1956 | Extended | 0.60 | exists (JLC file id 8588899357030); drawing PNGs in `hardware/reports/footprint-audit/datasheets/png/` |
| U3 | 10.0 QHHTZB6.3 (USB-A) | C668591 | SMD | 49952 | Extended | 0.07 | exists (JLC file id 8588914402913); not opened |
| D1 | SMAJ16CA(-13-F) TVS | C148217 | DO-214AC(SMA) | 9805 | Extended | 0.13 | exists (JLC file id 8586185844097) |
| D5-D9 | PESD2CAN,215 | C75176 | SOT-23 | 34023 | Extended | 0.08 | exists (JLC file id 8586180091767) |
| U13 | USBLC6-2SC6 | C7519 | SOT-23-6L | 32269 | Extended | 0.18 | exists (JLC file id 8579714554416) |
| D13/D14 | BAT54S,215 | C47546 | SOT-23 | 177396 | Extended | 0.03 | exists |
| D11 | B340A-13-F | C85098 | SMA | 28458 | Extended | 0.08 | exists; Diodes PDF fetched (`work/ds/diodes_b340a2.pdf`) |
| D12 | B540C-13-F | C72264 | SMC | 75486 | Extended | 0.22 | exists; manufacturer PDF not obtained (wrong file fetched, discarded for comparison) |
| Q4 | HY12P03C2 | C358006 | PPAK5x6-8L | 2741 | Extended | 0.24 | exists |
| L3 | SMMS0650-470M | C149588 | SMD 7.1x6.6 | 41297 | Extended | 0.17 | exists |
| L4 | MWSA1004S-150MT | C151872 | SMD 11x10 | 6391 | Extended | 0.27 | exists |
| J1 | 20021121-00010C4LF | C150517 | SMD P=1.27 | 809 | Extended | 0.44 | exists |
| SW1 | SKQGAFE010 | C202424 | SMD-4P 5.2x5.2 | 24076 | Extended | 0.14 | exists |
| U5 | FM-B1921RGBA-SH | C727904 | SMD-4P 2.2x2.1 | 9385 | Extended | 0.04 | exists; drawing PNG in footprint-audit |
| U1 | AP22615AWU-7 | none | - | - | - | - | not in catalog |

## Consistency between BOM files

- `BOM_JLC.csv` / `CPL_JLC.csv` (118 refs) match `bom.csv` codes; FID1-6 and JP1 are not in the CPL (correct for JLC). U1 is listed without a code.
- `BOM_HYBRIDPANDA_v1.csv` marks U1 as `UNRESOLVED-JLC`; otherwise identical codes.
- Both files inherit the C1555 and C23733 errors above.

## Limitations

- Stock/class/price are a 2026-10-15 snapshot of the jlcparts mirror, not live JLCPCB data.
- Package match is a family-level check (string on the catalog record vs PCB footprint name); physical land-pattern dimensions are covered in `footprint-vs-datasheet.md`.
- No JLC datasheet PDFs were opened from the catalog links (network blocked); existence of the link field only.

## Resumo (pt-BR)

Verificacao por software dos 48 codigos LCSC da BOM (119 refs). 45 linhas OK (codigo existe, MPN e familia de pacote batem com o footprint). Dois codigos errados na BOM: C1555 e 22 pF e nao 18 pF (usar C1549 para C23/C24); C23733 e 4,7 uF e nao 2,2 uF (usar C444845 ou C12530 para C64). C2932476 (C4/C12) nao esta no cache offline, mas existe no site da JLC; estoque nao verificado. U1 AP22615AWU-7 nao existe mais no catalogo JLC (decisao humana). JP1 e jumper de solda, sem peca. Estoque baixo em U7 (132), Q1/Q2 (187), J1, D2, D15, L5, P1. Nada foi verificado fisicamente nem cotado na JLC.
