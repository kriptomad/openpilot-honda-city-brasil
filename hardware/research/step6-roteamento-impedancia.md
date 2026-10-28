# STEP 6 — Roteamento, impedância e zonas — relatório de medições

Data: 2026-10-26 12:31 · Placa: `hardware\hybrid-panda\HybridPanda.kicad_pcb` · Script: `hardware\scripts\step6_reports.py` (só leitura) · JSON: `hardware\reports\step6_reports.json`

> O DRC do KiCad **não verifica impedância**. Os valores abaixo são estimativas analíticas (Hammerstad-Jensen / IPC-2141) a partir do stackup gravado no ficheiro; a referência de retorno real depende de onde há cobre em In1 (zona +3V3 só sob o MCU) — fora dela a referência é In2 (GND) a ≈1,28 mm, o que sobe Z0. Validação só com o fabricante (stackup controlado) ou TDR.

## 1. Stackup (do ficheiro)
| Camada | Espessura (mm) | εr |
|---|---|---|
| F.SilkS | None |  |
| F.Paste | None |  |
| F.Mask | 0.01 |  |
| F.Cu | 0.035 |  |
| dielectric 1 | 0.2 | 4.5 |
| In1.Cu | 0.0175 |  |
| dielectric 2 | 1.065 | 4.5 |
| In2.Cu | 0.0175 |  |
| dielectric 3 | 0.2 | 4.5 |
| B.Cu | 0.035 |  |
| B.Mask | 0.01 |  |
| B.Paste | None |  |
| B.SilkS | None |  |

## 2. Pares diferenciais
| Par | Classe | Camadas | Comprimento H/+ (mm) | Comprimento L/− (mm) | Skew (mm) | Vias no par | Larguras (mm) | Gap c-c (mm) | Travadas |
|---|---|---|---|---|---|---|---|---|---|
| BUS0_H/BUS0_L | CAN_DIFF | F.Cu | 8.96 | 10.12 | 1.160 | 0 | 0.15/0.2/0.25 | 0.651 | 10/11 |
| BUS1N_H/BUS1N_L | CAN_DIFF | F.Cu | 18.76 | 20.69 | 1.930 | 0 | 0.15/0.25 | 0.822 | 22/23 |
| BUS1O_H/BUS1O_L | CAN_DIFF | F.Cu | 12.06 | 13.83 | 1.770 | 0 | 0.15/0.175/0.25 | 0.948 | 20/21 |
| BUS2_H/BUS2_L | CAN_DIFF | F.Cu | 7.34 | 6.21 | 1.130 | 0 | 0.15/0.25 | 0.758 | 12/13 |
| USB_D+/USB_D- | USB | B.Cu,F.Cu,In1.Cu,In2.Cu | 16.88 | 19.37 | 2.490 | 4 | 0.2 | 1.081 | 0/21 |
| USB_R_D+/USB_R_D- | USB | F.Cu | 14.50 | 14.50 | 0.000 | 0 | 0.2 | 0.45 | 0/16 |

Critérios do protocolo (STEP 6): vias nos pares CAN = 0 → OK; pares em F.Cu → OK.

## 3. Impedância estimada
| Par | Camada | Ref. | h (mm) | εr | w (mm) | Z0 (Ω) | gap borda (mm) | Zdiff (Ω) | Nota |
|---|---|---|---|---|---|---|---|---|---|
| BUS0_H/BUS0_L | F.Cu | In1.Cu | 0.2 | 4.5 | 0.15 | 72.4 | 0.501 | 138.5 | referência In1 só é plano sob o MCU (+3V3); fora dela a referência real é In2 (h maior → Z maior) |
| BUS0_H/BUS0_L | F.Cu | In1.Cu | 0.2 | 4.5 | 0.2 | 64.5 | 0.451 | 121.9 | referência In1 só é plano sob o MCU (+3V3); fora dela a referência real é In2 (h maior → Z maior) |
| BUS0_H/BUS0_L | F.Cu | In1.Cu | 0.2 | 4.5 | 0.25 | 58.3 | 0.401 | 108.4 | referência In1 só é plano sob o MCU (+3V3); fora dela a referência real é In2 (h maior → Z maior) |
| BUS1N_H/BUS1N_L | F.Cu | In1.Cu | 0.2 | 4.5 | 0.15 | 72.4 | 0.672 | 142.0 | referência In1 só é plano sob o MCU (+3V3); fora dela a referência real é In2 (h maior → Z maior) |
| BUS1N_H/BUS1N_L | F.Cu | In1.Cu | 0.2 | 4.5 | 0.25 | 58.3 | 0.572 | 113.0 | referência In1 só é plano sob o MCU (+3V3); fora dela a referência real é In2 (h maior → Z maior) |
| BUS1O_H/BUS1O_L | F.Cu | In1.Cu | 0.2 | 4.5 | 0.15 | 72.4 | 0.798 | 143.3 | referência In1 só é plano sob o MCU (+3V3); fora dela a referência real é In2 (h maior → Z maior) |
| BUS1O_H/BUS1O_L | F.Cu | In1.Cu | 0.2 | 4.5 | 0.175 | 68.2 | 0.773 | 134.8 | referência In1 só é plano sob o MCU (+3V3); fora dela a referência real é In2 (h maior → Z maior) |
| BUS1O_H/BUS1O_L | F.Cu | In1.Cu | 0.2 | 4.5 | 0.25 | 58.3 | 0.698 | 114.6 | referência In1 só é plano sob o MCU (+3V3); fora dela a referência real é In2 (h maior → Z maior) |
| BUS2_H/BUS2_L | F.Cu | In1.Cu | 0.2 | 4.5 | 0.15 | 72.4 | 0.608 | 141.0 | referência In1 só é plano sob o MCU (+3V3); fora dela a referência real é In2 (h maior → Z maior) |
| BUS2_H/BUS2_L | F.Cu | In1.Cu | 0.2 | 4.5 | 0.25 | 58.3 | 0.508 | 111.7 | referência In1 só é plano sob o MCU (+3V3); fora dela a referência real é In2 (h maior → Z maior) |
| USB_D+/USB_D- | B.Cu | In2.Cu | 0.2 | 4.5 | 0.2 | 64.5 | 0.881 | 128.1 |  |
| USB_D+/USB_D- | F.Cu | In1.Cu | 0.2 | 4.5 | 0.2 | 64.5 | 0.881 | 128.1 | referência In1 só é plano sob o MCU (+3V3); fora dela a referência real é In2 (h maior → Z maior) |
| USB_D+/USB_D- | In1.Cu |  |  |  |  |  |  |  | camada interna: não estimado |
| USB_D+/USB_D- | In2.Cu |  |  |  |  |  |  |  | camada interna: não estimado |
| USB_R_D+/USB_R_D- | F.Cu | In1.Cu | 0.2 | 4.5 | 0.2 | 64.5 | 0.25 | 110.4 | referência In1 só é plano sob o MCU (+3V3); fora dela a referência real é In2 (h maior → Z maior) |

Alvos: CAN 120 Ω diferencial (ISO 11898-2), USB FS 90 Ω diferencial. Os pares do baseline Black Panda (herdados, trilhas travadas) não foram desenhados para impedância controlada; CAN clássico/FD a ≤ 5 Mbit/s com trilhas de poucos cm tolera o desvio (comprimento ≪ λ/10) — registado como NÃO VERIFICADO fisicamente.

## 4. Planos
| Rede | Camada | Polígonos | Área (mm²) | Maior (mm²) | Fracção do maior | Fragmentos < 5 mm² |
|---|---|---|---|---|---|---|
| GND | F.Cu | 19 | 1249.7 | 764.6 | 0.612 | 11 |
| GND | In2.Cu | 10 | 1720.3 | 1545.0 | 0.898 | 5 |
| GND | B.Cu | 14 | 1398.1 | 1334.4 | 0.954 | 9 |
| GND | agrupamentos de conectividade | [417] | | | | |
| +3V3 | In1.Cu | 3 | 729.9 | 693.3 | 0.95 | 0 |
| +3V3 | agrupamentos de conectividade | [333] | | | | |

Continuidade: 1 agrupamento = rede inteiramente ligada (zonas + vias + trilhas). Fragmentos pequenos do pour são cobre isolado da zona (não são erro de ligação; o DRC acusa `isolated_copper` só quando sem ligação alguma).

## 5. Totais
- Trilhas: 1201 · Vias: 204 · Largura mínima de trilha: 0.1500 mm · Tamanhos de via (Ø/furo): [(0.45, 0.25), (0.5, 0.3), (0.6, 0.3), (0.7, 0.3)]

## 6. NÃO VERIFICADO
- Impedância por medição (TDR) e stackup real do fabricante.
- Meandros de compensação de skew: não gerados (skew medido acima; pares do baseline mantidos como estão).
- Integridade de sinal CAN FD a 5 Mbit/s (tempo de subida vs. stubs): fora do âmbito desta medição.
