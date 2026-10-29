# Hybrid Panda PCB - software-only verification of BOM and footprints

Date of snapshot: 2026-10-28 (PCB file mtime 15:36, git HEAD `0b4802a`, uncommitted edits by the PCB agent in progress). Everything in this folder is verified by software only. Nothing was physically verified: no part was ordered, no board was built or measured, no JLCPCB quote or DFM run was executed.

## Deliverables

| File | Content |
|---|---|
| `lcsc-confirmation.md` / `.csv` | Task 1 - every LCSC code in `docs/hardware/bom.csv` checked against the jlcparts offline catalog (existence, MPN, package family vs PCB footprint, stock, Basic/Extended, price, datasheet link). 50 BOM lines, 119 refs. |
| `footprint-vs-datasheet.md` / `.csv` | Task 2 - every footprint on the board (33 footprints, 125 placements) compared with the manufacturer land pattern or the KiCad/IPC standard pattern; DRC `lib_footprint_mismatch` classification; EP parts; connectors; pin-1 / CPL rotation report. |
| `readme.md` | this summary |
| `work/` | evidence: PCB/schematic snapshot (`snapshot.kicad_pcb`, `.kicad_sch`, `.kicad_pro`, `fp-lib-table`, `HybridPanda.pretty` copy), `board_dump.json`, `drc_snapshot.json`, `lib_compare_snapshot.json`, `jlc_rows.json`, fetched datasheets `ds/*.pdf`, helper scripts `gfx_dump.py`, `pdftool.py`, `dl.ps1` |

Follow-up (2026-10-28/29): the PCB-side verification pass that acted on these findings is in [`../verification-pcb/`](../verification-pcb/) (impedance, USB re-route, CPL rotation, DRC cleanup, gerber review with connectivity comparison, hand-assembly review, thermal vias). Open items 1 (C23/C24 -> C1549, C64 -> C12530) and 7 (CPL rotation table) below were done there; item 2 is moot for a bare-PCB order (U1 bought from Mouser/Digi-Key).

## Method

- BOM: `docs/hardware/bom.csv` parsed with Python csv; cross-read against `hardware/reports/bom-real/BOM_HYBRIDPANDA_v1.csv` and `hardware/fabrication/assembly/BOM_JLC.csv` + `CPL_JLC.csv`.
- Catalog: yaqwsx/jlcparts SQLite mirror (snapshot 2026-10-15) queried offline; one web search for the single code missing from the mirror. Live jlcpcb.com / lcsc.com were not reachable through the corporate proxy.
- PCB: KiCad 10 pcbnew Python API and `kicad-cli pcb drc` on a copy of the board (no S-expression regex parsing). The live files in `hardware/hybrid-panda/` and `hardware/fabrication/` were only read, never written.
- Land patterns: existing repo audits reused and cited; `hardware/reference/datasheets/` (STM32H725); 7 manufacturer PDFs fetched (TI, Diodes, Murata); JEDEC packages compared with KiCad 10 library / IPC-7351 nominal values.

## Counts

Task 1 (LCSC codes, 50 BOM lines / 119 refs): 45 lines OK (112 refs); 2 MPN mismatch (C1555 is 22 pF not 18 pF for C23/C24 -> C1549; C23733 is 4.7 uF not 2.2 uF for C64 -> C444845 or C12530); 1 exists only on the web, stock/class not verified (C2932476, C4/C12); 0 package mismatch; 0 not found; 2 without code (JP1 solder jumper - no part; U1 AP22615AWU-7 - no longer in JLC catalog). 16 Basic lines, the rest Extended. Low stock on U7 (132), Q1/Q2 (187), J1, D2, D15, L5, P1.

Task 2 (footprints, 33 / 125 placements): 12 OK (98 refs), 10 OK vs KiCad library only (11), 8 minor deviation (13), 0 MISMATCH, 3 not checked (U3 USB-A, L3, L4 - vendor drawings unreachable). The 73 DRC `lib_footprint_mismatch` hits: ~61 are graphics/3D-model-path only; Q1, Q2, Q3, U5, Y1 are corrected on the board but stale in the project library; P1, U6, U12 have pad-layer/size differences described in the report. CPL rotations equal the raw KiCad rotations for all 118 refs (JLC orientation correction not verified).

## Open items that need a human

1. Fix the two wrong LCSC codes in the BOM (C23/C24 -> C1549; C64 -> C444845 or C12530).
2. Decide U1 AP22615AWU-7 sourcing (consigned part or alternative SOT-23-6 load switch at JLC).
3. Confirm C2932476 stock/class online, or switch C4/C12 to C15850 (25 V) if the net allows.
4. Re-check stock of U7 STM32H725ZGT6 and Q1/Q2 before ordering.
5. Rebuild `CONV_TPS5450DDAR` as a normal SMD footprint (pads on F.Mask, EP paste by pads, attr SMD); add courtyards to P1, U3, U5; sync `HybridPanda.pretty` with the corrected board footprints so DRC becomes clean.
6. Compare U3, L3, L4 against their LCSC drawings (C668591, C149588, C151872).
7. Run JLC's online CPL preview to confirm rotation of polarized/multi-pin parts; the repo CPL has KiCad rotations.
8. Verify the BOM manufacturer field for D1 (Littelfuse vs Diodes SMAJ16CA-13-F at C148217).

## Resumo (pt-BR)

Verificacao somente por software da BOM e das footprints da Hybrid Panda, sobre uma copia da placa de 2026-10-28. Codigos LCSC: 45 de 50 linhas OK; dois codigos errados (C1555 e 22 pF, C23733 e 4,7 uF); C2932476 existe mas estoque nao verificado; U1 sem codigo (peca saiu do catalogo JLC); JP1 sem peca. Footprints: 12 OK, 10 iguais a biblioteca KiCad, 8 com desvio menor, 0 MISMATCH, 3 nao verificadas (U3, L3, L4). Itens para um humano: corrigir os dois codigos, decidir U1, conferir estoque de U7/Q1/Q2, refazer a footprint do TPS5450 como SMD normal, sincronizar a biblioteca do projeto, conferir rotacoes no visualizador da JLC. Nada foi verificado fisicamente.
