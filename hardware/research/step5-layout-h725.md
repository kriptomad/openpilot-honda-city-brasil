# STEP 5 — PCB Hybrid Panda (STM32H725ZGT6 LQFP-144) — relatório

Data: 2026-10-26 · Protocolo v3 (STEP 5 + parte do STEP 6: roteamento/zonas) · Projeto: `04_PROJECT\HybridPanda\HybridPanda.kicad_pcb`

> Status honesto: PCB **gerada e roteada por script** (5a → 5b → 5c → 5d), DRC do KiCad com **0 itens não ligados** na corrida final (ver §7). **Não** é "pronto para fabricar": restam itens herdados do baseline (§7.3), impedância só estimada analiticamente no STEP 6 (§8), BOM com itens PROVISÓRIOS (STEP 4) e nenhuma prova física. O Freerouting é não-determinista — qualquer nova corrida do pipeline tem de ser re-validada pelo DRC.

## 1. Método (reprodutível)
| Passo | Script | Entrada → saída | Evidência |
|---|---|---|---|
| 5a — placa a partir do baseline | `05_SCRIPTS\step5_update_pcb.py` | `HybridPanda.kicad_pcb.baseline` → `.kicad_pcb` (+ snapshot `.step5a`) | `06_REPORTS\step5_update_pcb.json` |
| 5b — trilhas críticas + Freerouting | `05_SCRIPTS\step5b_route.py --passes 60` | `.step5a` → `.kicad_pcb` | `06_REPORTS\step5b_route.json`, `step5b_freerouting.log`, `HybridPanda_step5b.dsn/.ses` |
| 5c — corretor orientado pelo DRC | `05_SCRIPTS\step5c_fix_unrouted.py --rounds 6` | `.kicad_pcb` (in place) | `06_REPORTS\step5c_fix.json` (`step5c_pre.json` para a fase P do 5b) |
| 5d — serigrafia das referências novas | `05_SCRIPTS\step5d_silk.py` | `.kicad_pcb` (in place) + DRC | `06_REPORTS\step5d_silk.json` (D-31) |
| DRC | `kicad-cli pcb drc --format json --severity-all --units mm` | → `06_REPORTS\hybrid_DRC_step5_final.json` | §7 |

Ferramentas: KiCad 10.0.7 (python embutido 3.11), Freerouting 2.5.0 (jar) + Java 25, headless. Comandos exactos em `05_SCRIPTS\README.md` (secção STEP 5). Nenhum ficheiro do baseline (`01_BASELINE`, `02_REFERENCE`) é alterado; tudo parte de cópias em `04_PROJECT`.

## 2. 5a — o que mudou no baseline (`step5_update_pcb.py`)
- **Removidos** (9): ANT1, C15, C25, C9, L1, R10, R22, U2, U4 (GPS e periféricos do F413 sem equivalente no red panda). U7 (F413 LQFP-100, F.Cu) substituído pelo **U7 = STM32H725ZGT6 LQFP-144 em B.Cu**, centro (109,5; 56,6), rotação 90° (D-21/D-22 — colocação por pontuação de distância pad→pad, 348,1 mm).
- **Adicionados** (37): C38–C63 (VCAP, desacoplamento VDD/VDDA/VDDLDO/VDDUSB, SMPS Cin/Cfilt/Cout), D13/D14 (ESD SBU), FB1, J1 (SWD 2×5 1,27 mm), L5 (DFE201610E 2,2 µH), R28–R33 (SBU 10k, pull-ups STB/EN).
- **Nets renomeadas**: 67 (CAN*→BUS* conforme D-17; GPS_* eliminadas).
- **Placa ampliada** +5 mm ao sul (Edge.Cuts y_max 73,76 → 78,76; D-24, autorização do usuário). Zonas GND/+3V3 estendidas até à nova borda.
- Limpeza de fragmentos respeitando o preenchimento das zonas (D-25): 51 itens removidos; cobre do baseline sob 19 pads novos removido.
- Relatório de distâncias pad→pad (fase E; limites: nenhum pad fora do contorno, 0 colisões): C39.1→U7.68 1,25 mm; C40.1→U7.140 1,34; L5.1→U7.15 1,46; L5.2→U7.17 1,46; C44.1→U7.36 1,10; Y1.3→U7.26 1,64; Y1.1→U7.25 3,26; C23.1→U7.25 2,41; C24.1→U7.26 3,28; desacoplamentos VDD (C45–C57) 1,09–2,23 mm (C47 sob o pino 19, 0,0); C59.1→U7.90 6,27 (VDD50USB; único > 5 mm). Tabela completa em `step5_update_pcb.json` → `phases.E.pad_gap_mm`.
- Nota aberta (registo 5a): VCAP tem 3 pinos (68/103/140) e 2 capacitores no esquemático — pino 103 alimentado por trilha; DS13311 §6.3.2 (ver STEP 4 PROVISÓRIOS).

## 3. Stackup e regras (herdados do baseline Black Panda, não alterados)
- 4 camadas, 1,59 mm: F.Cu 35 µm / pré-preg 0,2 / In1.Cu 17,5 µm / núcleo 1,065 / In2.Cu 17,5 µm / pré-preg 0,2 / B.Cu 35 µm. Uso: F.Cu/B.Cu sinais+componentes, **In2 = plano GND**, **In1 = +3V3 (zona sob o MCU, contorno 96,1–127 × 38,7–76,5) + sinais**.
- Regras: clearance 0,10 mm (todas as classes), trilha mín. 0,1375, via mín. 0,4/furo 0,3, furo↔cobre e furo↔furo 0,25, anel 0,05. Classes CAN_DIFF/USB com 0,7 de clearance no DSN.
- Alterações globais documentadas: clearance da zona GND 0,508 → 0,254 mm (D-28) e da zona +3V3 In1 0,254 (D-29).

## 4. 5b — roteamento (`step5b_route.py`)
Fases, por ordem: **Z** zonas (+3V3 In1 sob o MCU, clearance das zonas) → limpeza de duplicados/fragmentos → **C** trilhas críticas por script (travadas): VCAP (3 pinos), cristal 25 MHz (HSE_IN/OUT), SMPS (VLX/VFB/VDDSMPS: L5, C41/C42), desacoplamento U7 com via GND/+3V3 por pad (8 direcções, `_try_gnd`) → **M** desvio da trilha +5V In1 (x = 117,6) + via-in-pad GND do U1.2 (D-29) → **R** pré-rotas travadas B.Cu→via→F.Cu para pares que o Freerouting falhava sempre (BUS2_TX/BUS2_RX U7↔U9 — D-30; os restantes 6 pares só quando houver posição de via livre) → **V** vias de costura GND/+3V3 nos pads dos capacitores (42/50; os 8 "sem espaço" ficam para P/Freerouting) → **P** `step5c --pre` (só GND/+3V3/+5V, itens travados) → trava o baseline → **X** DSN (só planos GND; regras `via_*` 160, `kicad_default use_via 500:300`) → Freerouting headless (`--passes 60`) → SES → destrava baseline → alarga trilhas < 0,1375 → **F** refill + limpeza final (vias ligadas numa só camada, stubs fora do pour) + relatório.
- Decisões relevantes: D-23 (U7 em B.Cu), D-25, D-26, D-27 (fase P, `via_*` no DSN), D-28 (corredor BUS2, via 0,5, clearance GND), D-29 (ilhas, fase M, `via_via`, sem `wire_pin`), D-30 (fase R, pontes sem via, curtos do FR).

## 5. 5c — corretor (`step5c_fix_unrouted.py`)
Lê o DRC JSON e, por item não ligado, aplica por ordem: via de costura em pad (8 direcções), via-in-pad (0,6/0,5), trilha→pour da mesma rede (só se o contorno vertido tiver via/PTH da rede), ligação de ilhas GND, trilha directa / em Z / por via (In1/In2), A* local (grelha 0,2–0,25 mm; obstáculos incluem furos com folga 0,25), rip-up de cadeia destravada de outra rede (revertido se falhar); `fix_clusters` para agrupamentos GND/+3V3 isolados (D-29; fallback D-30: trilha directa/A* até item do agrupamento principal, sem via nova); `fix_holes` (afunilamento de trilha do FR sobre furo PTH/via primeiro; depois fusão/remoção de vias do FR com `hole_to_hole`/`hole_clearance`); `fix_shorts` (`shorting_items`/`clearance` com item destravado do FR — observado uma vez: via BUS1O_RX × trilha SBU1_ADC In2 na saída do próprio Freerouting). No fim remove vias destravadas ligadas numa só camada e micro-segmentos < 0,02 mm. Pára quando o DRC não tem itens não ligados, furos, curtos nem clearance corrigíveis.

## 6. Verificação de integridade do baseline após o pipeline
- USB D+/D− (P1 → U7.PA11/PA12): as trilhas do baseline em F.Cu iam ao F413 (F.Cu); como o U7 está em B.Cu, o troço final é **re-roteado pelo Freerouting** com vias (medição em STEP 6: `03_RESEARCH\STEP6_roteamento_impedancia.md` — 5 vias, 4 camadas, skew ≈ 2 mm, gap > 2 mm, i.e. par **não acoplado**). USB Full-Speed (12 Mbit/s) é tolerante a isto no comprimento em causa (< 40 mm), mas fica registado como risco em §8 e no LEIA-ME de fabricação.
- CAN H/L (BUS0–3_H/L, P1 ↔ U8–U11): trilhas do baseline em F.Cu **travadas permanentemente** (`re.match(r"BUS\w+_[HL]$")` em 5b/5c) — sem vias nos pares (requisito STEP 6 cumprido por herança; medição de comprimento/skew em STEP 6).

## 7. Resultado DRC (corrida final — pipeline 5a→5b→5c→5d de 2026-10-26 12:15–12:45; `06_REPORTS\hybrid_DRC_step5_final.json`, placa `HybridPanda.kicad_pcb` = snapshot `.step5_final`)
Corrida 20 do pipeline (as corridas 10–19 serviram para tornar o 5b/5c deterministas face ao Freerouting — D-26…D-30). Freerouting: 151 redes, 459 s, 30 ligações por fechar no seu critério (`step5b_freerouting.log`); KiCad após 5b: **6** itens não ligados; após 5c (3 rodadas, 40 itens adicionados, 46 micro-segmentos removidos, 0 vias soltas): **0**. Fases do 5b: M `u1_2_via: true` (via-in-pad GND U1.2 a 0,250 mm da trilha USB_PWR — aceite pelo DRC), R = 2/8 pares pré-roteados (BUS2_TX via 122,42; 53,87 · BUS2_RX via 123,02; 56,62), V = 42/50 vias de costura. 5d (`step5d_silk.py`): serigrafia das referências dos 37 componentes novos escondida (só cosmético). Totais: 1201 trilhas, 204 vias (0,45/0,25 do baseline; 0,5/0,6/0,7 com furo 0,3).

### 7.1 Itens não ligados
**0** (`unconnected_items: []`). Sem `clearance`, `shorting_items`, `track_dangling`, `via_dangling`, `track_width` nem `hole_to_hole`.

### 7.2 Violações novas (assinatura tipo+itens inexistente em `baseline_DRC.json`): 12
| Tipo | Qtd | Itens | Avaliação |
|---|---|---|---|
| `starved_thermal` | 11 | zona GND ↔ U6.9 (In1, ×3), U7.6/69/89 (B.Cu), C52.2/C46.2 (B.Cu), C27.2/U10.2/P1.A1 (F.Cu) | aviso: pad ligado à zona GND com 1 raio térmico em vez de 2 (regra da zona do baseline). Ligação eléctrica existe (DRC `unconnected` = 0; `fix_clusters` verifica agrupamentos). Mitigação possível: ligação sólida nestes pads — **não aplicada** (fora do âmbito; registado como exceção justificada). |
| `silk_overlap` | 1 | referência C23 × contorno de serigrafia Y1 (B.Cu) | cosmético (C23 é do baseline, reposicionado junto ao cristal); pode esconder-se a referência como no 5d. |

Antes do 5d havia ainda 20 `silk_over_copper` + 18 `silk_overlap` de referências de C38–C63/L5/FB1/R28 sobre pads vizinhos — eliminadas ao esconder a serigrafia dessas referências (não há cobre envolvido).

### 7.3 Violações herdadas do baseline (não tocadas; decisão: manter como está, documentar)
| Tipo | Baseline | Híbrida | Nota |
|---|---|---|---|
| `text_height` | 82 | 72 | textos < mínimo (regra do baseline); menos na híbrida porque os textos do GPS/F413 saíram |
| `lib_footprint_mismatch` | 67 | 58 | footprints embutidos ≠ biblioteca KiCad 10 (baseline); idem |
| `starved_thermal` | 13 | 18 | 7 do baseline mantidas + 11 novas (§7.2) |
| `footprint_type_mismatch` | 11 | 10 | atributo SMD/THT do footprint (baseline) |
| `hole_clearance` | 8 | 8 | **idênticas**: PTH GND de P1 (USB-C) × NPTH de P1 a 0,144 mm — geometria do footprint TYPE-C-31-M-04 do baseline |
| `silk_edge_clearance` | 4 | 4 | idênticas (baseline) |
| `silk_overlap` | 3 | 4 | 3 do baseline + 1 nova (§7.2) |
| `copper_edge_clearance` | 3 | 2 | U3 pads 5/6 × Edge.Cuts (baseline); uma desapareceu com a placa +5 mm |
| `courtyards_overlap` | 1 | 1 | **idêntica**: D7 × U9 (baseline) |
| `drill_out_of_range` | 1 | 1 | via GND 0,25 mm do baseline (regra mín. 0,3) |
| `isolated_copper` | 1 | 1 | ilha de preenchimento da zona GND (sem ligação, não é erro de rede) |
| **Total** | **194** | **179** | |

## 8. NÃO VERIFICADO / BLOQUEADO / pendente
- Impedância CAN_DIFF (120 Ω dif.) e USB (90 Ω dif.): **só estimada analiticamente** (STEP 6, `STEP6_roteamento_impedancia.md`); o DRC não verifica; sem TDR nem stackup do fabricante.
- Skew e comprimentos dos pares CAN/USB: medidos no STEP 6 (CAN 1,1–1,9 mm de skew, 0 vias; USB_D± 2,5 mm, **4 vias**, par não acoplado — risco registado no LEIA-ME de fabricação).
- Continuidade do plano GND In2: 1 agrupamento de conectividade (STEP 6 §4); fragmentos do pour documentados.
- `starved_thermal` novas (§7.2) — exceção justificada, não corrigida.
- Courtyard D7/U9 sobreposto e `isolated_copper`/`drill_out_of_range` são do baseline (ver §7.3) — não alterados (regra: não "melhorar" o baseline fora do escopo).
- Caixa mecânica: STLs de `01_BASELINE` **não servem** (placa +5 mm, D-24).
- Reprodutibilidade: o Freerouting é não-determinista; 20 corridas do pipeline foram necessárias para que 5b/5c fechassem sempre os pares problemáticos (D-26…D-30). Qualquer nova corrida exige repetir o DRC e o 5d.
- Nenhuma validação física (protótipo) — STEP 9 descreve o bring-up.
