# RELATÓRIO FINAL — Hybrid Panda (Black Panda × STM32H725ZGT6 / firmware red panda)

Data: 2026-10-26 (rev. 2026-10-28, campanha de correção §1.1) · Protocolo v3 (`docs\protocol-v3.md`), STEP 1–9 · Raiz: `<repo-root>` · Repositório: github.com/kriptomad/PandaH7Openpilot

## 1. Resumo e estado real

Objetivo: adaptar o projeto KiCad aberto **OpenBlackPanda** (lukasloetkolben, STM32F413, MIT) para correr o **firmware oficial do red panda** (commaai/panda, `stm32h7`, HW_TYPE RED) **sem modificação**, num **STM32H725ZGT6 LQFP-144**, mantendo formato, conectores e harness do Black Panda, para uso com openpilot num Honda City 2023 BR.

Estado em uma frase: **projeto eletrónico completo em análise estática (esquemático, PCB roteada, DRC/ERC, netlist, paridade de pinos com o firmware, pacote de fabricação gerado), com zero validação física.** Não é "pronto para fabricar", não é "validado", não é "funcional". A compatibilidade com o firmware do red panda está demonstrada **só por análise estática (paridade 36/36 pinos), sem compilação local e sem teste em hardware**.

| STEP | Estado | Prova principal |
|---|---|---|
| 1 Ambiente/base | FEITO | `archive\manifests\original_BEFORE.sha256` (377 ficheiros), baseline ERC/DRC em `hardware/reports` |
| 2 Ingestão / HRS | FEITO | `hardware\research\hrs-red-panda.md`, `../hardware/research/coverage-matrix.md` (61/61 requisitos provados), `hardware/reference` (clones só leitura, hashes em `reference_clones.sha256`) |
| 3 Eng. reversa / tabela híbrida | FEITO | `hardware\research\step3-engenharia-reversa-tabela-hibrida.md`, `hardware\scripts\parity_check.py` + `firmware_pins.json` |
| 4 Esquemático | FEITO | `hardware\hybrid-panda\HybridPanda.kicad_sch`, `../hardware/research/step4-esquematico-h725.md`, ERC 0 erros |
| 5 PCB | FEITO + campanha de correção (D-34..D-38) | `HybridPanda.kicad_pcb` (HEAD de main; `.step5_final` obsoleto), `../hardware/research/step5-layout-h725.md`, `hardware\reports\correcoes-aplicadas.md`; DRC final 0 não ligados / 0 clearance / 0 curtos (135 itens herdados: P1 hole 8, lib mismatch 73, silk 9, text 45); via-in-pad 0 |
| 6 Roteamento / impedância | FEITO (analítico) | `../hardware/research/step6-roteamento-impedancia.md` |
| 7 Validação | FEITO — **nenhuma falha** (re-executado 2026-10-28) | `../hardware/research/step7-validacao.md`, `hardware\reports\step7_validation.json`, `hybrid_DRC_final.json`, `hybrid_ERC_final.json` (0 erros / 373 avisos) |
| 8 Fabricação | FEITO — **NÃO FABRICAR** (regenerado 2026-10-28) | `hardware\fabrication\` + `../hardware/fabrication/readme.md`; BOM_JLC.csv com LCSC em 117/119 refs ("a verificar") |
| 9 Bring-up / relatório | FEITO (documental) | `../hardware/research/step9-bringup-e-teste-veiculo.md`, este ficheiro |

### 1.1 Campanha de correção pós-auditoria (2026-10-28)

Três auditorias independentes sobre o snapshot `.step5_final` (`hardware\reports\footprint-audit`, `hardware\reports\si-pi-audit` com 36 itens, `hardware\reports\bom-real`) encontraram erros reais: VFBSMPS separado de VCAP (Direct SMPS inoperante), pads de Q1/Q2/Q3/U5 fora da geometria dos fabricantes, R1 1 k no gate do Q4, USB sem ESD, Cin do TPS5450 subdimensionado, pistas de potência de 0,2 mm, zona GND com thermals famintos. As correções foram aplicadas em seis commits (a8b98a9, a5d60b8, b209b08, eb14492, 9305ef2, 15e11dd, final), cada edição validada por `hardware\scripts\corr_gate.py` (DRC kicad-cli: 0 clearance / 0 unconnected / 0 paridade, nenhuma categoria de erro nova) e ERC 0; esquema e PCB alterados em conjunto. Resultado: DRC 182 -> 135, categorias `copper_edge_clearance`, `starved_thermal`, `drill_out_of_range` e `footprint_type_mismatch` eliminadas; 21 itens aplicados, 6 parciais, 13 deferidos por exigirem relayout (D-37). Tabela item -> estado -> commit -> evidência, delta de BOM e lista do que continua sem verificação física: `hardware\reports\correcoes-aplicadas.md`. **Nada foi testado em hardware.**

## 2. Resultado das premissas P1–P11

| P | Enunciado | Resultado | Fonte |
|---|---|---|---|
| P1 | Honda City 2023 BR usa CAN-FD | **REFUTADA** — `HONDA_CITY_7G = HondaBoschPlatformConfig(..., BOSCH_RADARLESS)`, CAN clássico, harness Bosch B. Decisão do utilizador: prosseguir com H7 na mesma (D-05) | `../hardware/research/p1-veiculo-honda-city-2023.md`; opendbc `car/honda/values.py` |
| P2 | commaai publica o hardware do red panda | **REFUTADA** — só firmware; esquemático/PCB do red panda não publicados | `../hardware/research/p2-hardware-red-panda.md` |
| P3–P6 | Mapa de pinos do firmware red (GPIO, ADC, CAN, USB, clock) | CONFIRMADAS e extraídas com file:line | `../hardware/research/p3-p4-p5-p6-firmware-pinmap.md`, `../hardware/research/p3-tabela-pinos-lqfp144-vs-firmware.md`, HRS §2–§5, §8 |
| P7 | Pacote TFBGA100 serviria | **REFUTADA** — sem PF/PG; `clock.h` exige SMPS para LQFP144 | HRS §2; `../hardware/research/kicad-lib-stm32h723vghx-pins.txt`; D-02 |
| P8 | HW_TYPE por straps | CONFIRMADA — RED = PF7–PF10 a 0 (pull-up interno) | HRS §1; D-08 |
| P9 | Flash 1 MB necessária | CONFIRMADA → H725**ZG** | HRS §6 |
| P10 | Pinout OBD-C / SBU / harness | CONFIRMADA; PC4 = TT_ha, SBU condicionado (D-12, D-16) | `../hardware/research/p10-obdc-harness-sbu.md` |
| P11 | Transceivers do baseline servem para CAN FD | CONFIRMADA — TJA1042TK/3, 5 Mbit/s (D-20) | `../hardware/research/r3v2-componentes-step4.md` |

## 3. HRS e matriz de cobertura
- `hardware\research\hrs-red-panda.md` — requisitos de hardware extraídos do firmware (`board/boards/red.h`, `stm32h7/*`, `board/main.c`, …) com file:line, §1–§10 (inclui controlo F4 do Black Panda).
- `hardware\research\coverage-matrix.md/.csv`, `hardware\reports\coverage_matrix.json` — **61/61 requisitos provados, 0 não encontrados**.
- Controlo do método: perfil `black_f4` do `parity_check.py` sobre a netlist do Black Panda original = 35/35 OK (prova de que o verificador reconhece um projeto sabidamente funcional).

## 4. Tabela híbrida
`hardware\research\step3-engenharia-reversa-tabela-hibrida.md` §(f): periférico × pino F413 (baseline) × pino exigido no H725 × rede × componente. Sem **PIN_PARITY_CONFLICT**. Paridade final (STEP 7, netlist do esquemático atual): **36/36 OK** (`hardware\reports\parity-red-h7-hybrid-hybridpanda-netlist.md`).

## 5. BOM
- Esquemático: 114 referências, 48 linhas agrupadas (`hardware\reports\hybrid_BOM.csv`; JLC: `hardware\fabrication\assembly\BOM_JLC.csv` + `CPL_JLC.csv`, 76 top / 38 bottom).
- Consistência BOM × esquemático × PCB: **0 divergências** (STEP 7).
- **114 referências sem MPN e sem código LCSC** — PROVISÓRIO. Itens com valor definido mas fabricante por confirmar: cristal 25 MHz (CL/15 pF), L5 DFE201610E 2,2 µH, FB1, condensadores VCAP/SMPS (ESR), ver `../hardware/research/r3v2-componentes-step4.md` e `../hardware/research/step4-esquematico-h725.md` §9.

## 6. Esquemático por bloco (`../hardware/research/step4-esquematico-h725.md`)
MCU U7 LQFP-144 (Direct SMPS: L5 + C41/C42; VCAP ×3 interligados, D-19; VDDLDO; VDD33USB = 3V3, D-14) · cristal 25 MHz · straps HW_TYPE (D-08) · 4 transceivers TJA1042 (BUS0/BUS1N/BUS1O/BUS2, STB com pull-up, D-09/D-17; errata normal/OBD D-15) · USB-C P1 (pinagem do baseline, D-13) · OBD-C/harness com SBU → 10 kΩ + BAT54S → PC4/PA1 (D-12/D-16) · alimentação 12 V→5 V→3V3 do baseline · SWD J1 2×5 1,27 mm · LEDs/ventoinha/sensores do baseline. GPS NEO-M8M removido (D-03). Sem terminação 120 Ω (D-04).

## 7. Pinos e conectores
- Mapa dos 144 pads (77 ligados, 67 NC): `../hardware/research/step4-esquematico-h725.md` §4; `../hardware/research/p3-pinos-lqfp144.json`.
- Conectores: P1 USB-C (TYPE-C-31-M-04), OBD-C/harness (A2/A3 CAN0, A10/A11 CAN1, B2/B3 CAN2, B10/B11 CAN3, A8/B8 SBU, VIN/GND), J1 SWD — `STEP4` §5, `../hardware/research/p10-obdc-harness-sbu.md`.

## 8. Regras, stackup, furação, mecânica
- Regras (do baseline, mantidas): trilha/espaço mín 0,1375/0,1 mm; via 0,4/0,3 (vias do baseline 0,45/0,25 permanecem — 1 `drill_out_of_range` herdado); anel mín 0,05; furo mín 0,3.
- Stackup (gravado no ficheiro, **não confirmado com fabricante**): 4 camadas, F.Cu 35 µm / 0,2 mm / In1 17,5 µm / 1,065 mm / In2 17,5 µm / 0,2 mm / B.Cu 35 µm, εr 4,5 — total ≈ 1,59 mm. In2 = GND; In1 = +3V3 só sob o MCU.
- Furação: 242 furos (PTH 26, NPTH 2, vias 214; apos D-33); brocas 0,25–2,5 mm; 6 slots (P1); Excellon = PCB (242 = 242) — `hardware\fabrication\drill_table.md`.
- Mecânica: placa ampliada **+5 mm ao sul** (Edge.Cuts y_max 73,76 → 78,76 mm, D-24) e **+3 mm a leste** (x_max 139,535 → 142,535 mm, D-33) → **50,625 x 46,75 mm**; **as caixas STL do baseline não servem**; U7 em B.Cu (D-21) — altura do lado B aumenta (LQFP 1,6 mm + L5 1,0 mm). P1 (USB-C) e U3 continuam conectores de borda, flush com a borda leste.
- Relayout leste (D-33, 2026-10-27): o bloco de transceptores/protecções (U8–U11, D5–D9, D13, P1, U3, Q1/Q2, R24, C26–C33) foi transladado +3 mm (C30/C31 +2, Q1/Q2 +2,4) para abrir ~1 mm entre o U7 e os transceptores; rerouting completo (5b/5c/5d) + `fix_audit.py` + `fix_drc_relayout.py` + `fix_vip_reroute.py`. O que foi verificado: DRC `kicad-cli` 0 clearance / 0 unconnected / 182 itens (17 `starved_thermal`, resto herdado); `final_audit.py` via-in-pad 0 (centro de via dentro de bbox de pad SMD), 0 curtos, 0 ilhas; `step7_validate.py` sem falhas (ERC 0 erros, netlist sch×pcb 0 divergencias, paridade 0 conflitos). Nao verificado: folgas de courtyard < 1 mm internas ao bloco (herdadas do baseline, nao alteradas), impedancia, qualquer teste fisico.
- Impedância (STEP 6): CAN Zdiff ≈ 122–139 Ω estimados onde há referência In1; USB ≈ estimativa; **só analítico**.

## 9. Comandos executados e códigos de saída
Todos registados nos JSON de `hardware/reports` (campo `commands`/`events` com `cmd`, `exit`, `seconds`) e em `hardware\scripts\readme.md`:

| Fase | Comando | Exit | Log |
|---|---|---|---|
| 5a | `python.exe hardware\scripts\step5_update_pcb.py` | 0 | `step5_update_pcb.json` |
| 5b | `python.exe hardware\scripts\step5b_route.py --passes 60` (Freerouting 2.5.0, Java 25) | 0 | `step5b_route.json`, `step5b_freerouting.log` |
| 5c | `python.exe hardware\scripts\step5c_fix_unrouted.py --rounds 6` | 0 | `step5c_fix.json` |
| 5d | `python.exe hardware\scripts\step5d_silk.py` | 0 (DRC 0) | `step5d_silk.json`, `hybrid_DRC_step5_final.json` |
| 5e+ | `python.exe hardware\scripts\step5e_relayout_east.py` (antes do 5b) → 5b/5c/5d → `fix_audit.py` → `fix_drc_relayout.py` → `step5c_fix_unrouted.py --rounds 3` → `fix_vip_reroute.py` → `final_audit.py` | 0 (DRC 0/0/182; via-in-pad 0) | `step5e_relayout_east.json`, `fix_audit.json`, `fix_drc_relayout.json`, `fix_vip_reroute.json`, `final_audit.json` |
| 6 | `python.exe hardware\scripts\step6_reports.py` | 0 | `step6_reports.json` |
| 7 | `python.exe hardware\scripts\step7_validate.py` → `kicad-cli sch erc` 0, `pcb drc` 0, `sch export netlist` 0, `sch export bom` 0, `parity_check.py` 0, `Make-Manifest.ps1 -Step STEP7 -Original` 0 | 0 | `step7_validation.json`, `step7_*.log` |
| 8 | `python.exe hardware\scripts\step8_fabricate.py` → gerbers 0, drill ×2 0, pdf ×9 0, **step 2** (ficheiro gerado; modelos VRML ignorados), bom 0, pos 0 | 0 | `step8_fabrication.json` |

`python.exe` = `C:\Users\costabr\AppData\Local\Programs\KiCad\10.0\bin\python.exe` (KiCad 10.0.7). Nenhum comando gravou fora da raiz (`hp_common.assert_inside_output`); `ORIGINAL vs BEFORE: IDENTICAL (377 files)` no manifesto STEP7.

## 10. Riscos (ordem de gravidade)
1. **PIN_PARITY_CONFLICT: nenhum.**
2. **Zero validação física** — nenhum protótipo; o firmware red panda nunca correu neste hardware.
3. **Assinatura do bootstub**: o bootstub release só aceita firmware assinado com a chave privada da comma (HRS §7). Placa de terceiros ⇒ compilar e gravar **bootstub + app em DEBUG** (`certs/debug`), via DFU; o openpilot/`pandad` pode recusar firmware não assinado — consequência operacional não verificada.
4. **Toolchain ARM ausente** → sem prova de compilação local (BLOQUEADO).
5. **USB_D± não acoplado** (4 vias, skew 2,5 mm) — FS 12 Mb/s tolera em geral, não validado.
6. **Impedância só estimada**; stackup não confirmado pelo fabricante.
7. **Consumo/térmica do H725** (SMPS, 550 MHz) com o regulador 5 V→3V3 do baseline: NÃO VERIFICADO (g-5).
8. **BOM PROVISÓRIA** (sem MPN/LCSC; ESR dos VCAP/SMPS crítico para o DS13311 §6.3).
9. **P1 refutada**: o City 2023 BR é CAN clássico — o projeto não traz ganho funcional face a um black panda para este veículo (decisão consciente do utilizador, D-05).
10. DRC herdado do baseline (hole_clearance P1 0,144 mm, vias 0,25) e 17 `starved_thermal` (11 do STEP 5 + relayout D-33) — ver `../hardware/research/step5-layout-h725.md` §7. Courtyard D7/U9 resolvido (U9 −0,25 mm, D-33).
11. Caixa mecânica do baseline incompatível (+5 mm ao sul, +3 mm a leste).

## 11. Listas de honestidade
**NÃO VERIFICADO**: impedância/skew reais; consumo e térmica; enumeração USB/HW_TYPE; CAN FD em hardware; comportamento do `pandad` com firmware DEBUG; convenção de rotação do CPL para JLC; corpos 3D dos footprints VRML no STEP; ESR real dos condensadores escolhidos.
**BLOQUEADO**: compilação do firmware (sem `arm-none-eabi-gcc`/`scons`); firmware release assinado (chave privada comma); Git LFS do openpilot (403 — D-10, não necessário).
**BLOQUEADO_MANUAL**: escolha/compra de componentes com MPN/LCSC; confirmação do stackup com o fabricante; revisão visual de gerbers no GerbView; protótipo e bring-up (STEP 9); ligação ao veículo.
**NÃO EXECUTADO**: visualizador de gerber automatizado; TDR; testes de bancada; captura passiva no veículo; análise do host openpilot para D-06.

## 12. Fontes
`docs\reference-sources.md` (proveniência); clones com hash: panda 408e14d4 (+ panda_full f62adf72, legado F4 f849893b), opendbc c3955753, openpilot ff47f484, hardware a42a4752, neo 9869dee9, panda_jungle b80539fc, harness_tester_challenge 069f7243, openpilot-docs 8a007654; ST DS13311 Rev 5 (STM32H725xE/G); OpenBlackPanda (cópia em `archive/baseline-original`). Citações file:line nos documentos de `hardware/research`.

## 13. Licenças
`LICENSE.md`: baseline MIT (Lukas, 2023 — manter aviso nos derivados), commaai/panda, opendbc, openpilot MIT; `commaai/hardware` sem LICENSE (PDFs "you can copy this!" — não redistribuir fora do projeto); datasheet ST não redistribuída no pacote de fabricação.

## 14. Manifestos SHA-256 e índice
`archive\manifests\`: `original_BEFORE.sha256` / `original_AFTER_STEP2…` / `original_AFTER_STEP7…` (ORIGINAL IDENTICAL), `OUTPUT_ROOT_STEP2/3/4/7/9_*.sha256`, `reference_clones.sha256`, `baseline_copy.sha256`. `docs/legacy-index.md` na raiz regenerado pelo `Make-Manifest.ps1`.

## 15. O que o utilizador precisa de fazer manualmente (lista curta)
1. Preencher MPN/LCSC na BOM (cristal CL, L5, FB1, condensadores com ESR) e reexportar (`step8_fabricate.py`).
2. Decidir USB_D±: rerotear manualmente como par acoplado em F.Cu (sem vias) ou aceitar o risco; depois `step7_validate.py` + `step8_fabricate.py`.
3. Confirmar stackup/impedância com o fabricante (4 camadas 1,59 mm, controlo de impedância para 120 Ω CAN / 90 Ω USB).
4. Abrir `hardware\fabrication\gerbers` no GerbView e rever visualmente (Edge.Cuts, máscara dos pads LQFP 0,5 mm, slots do P1).
5. Instalar `arm-none-eabi-gcc` + `scons`; compilar `hardware\reference\panda\board` (`scons -u -j8`) em DEBUG e guardar `panda_h7.bin.signed` + `bootstub.panda_h7.bin` para o STEP 9.
6. Só então: protótipo (1–2 unidades), bring-up de bancada (`../hardware/research/step9-bringup-e-teste-veiculo.md`, 19 passos) e, se tudo passar, captura passiva no veículo com critérios de paragem.
7. Decisão D-06 (plataforma host openpilot) continua em aberto.
