# STEP 4 — Esquemático Hybrid Panda (STM32H725ZGT6) — relatório

Data: 2026-10-23 · Protocolo v3 (STEP 4, spec 0x04 A–G) · Projeto: `04_PROJECT\HybridPanda\HybridPanda.kicad_sch`

> Status honesto: esquemático **gerado e verificado por ferramenta** (ERC 0 erros, paridade firmware 36/36, geometria 100 % ancorada). **Não** é "pronto para fabricar": restam STEP 5 (PCB), STEP 6 (DRC/fab), e itens PROVISÓRIOS de BOM (cristal CL, indutor, ESD) a confirmar em datasheet primário.

## 1. Método (reprodutível)
| Passo | Ferramenta | Evidência |
|---|---|---|
| Cópia do baseline → `04_PROJECT` + prova round-trip | `05_SCRIPTS\step4_copy_and_roundtrip.py` | `06_REPORTS\step4_roundtrip.md` (348/348 tuplas de netlist idênticas; PCB 86 fp/387 pads/998 trilhas idênticos) |
| Prova da transformação de pinos (kiutils) | `05_SCRIPTS\sch_geom.py` selftest | baseline: 382 pinos ancorados / 10 soltos (todos soltos já no original: #PWR015/016/017, U6.2/3, U2.6, U4.14–17) |
| Geração do esquemático | `05_SCRIPTS\step4_build_schematic.py` (+ `step4_bom_values.json`) | `06_REPORTS\step4_build_schematic.json`; backups em `99_BACKUPS\*_step4_build` |
| Netlist / ERC / paridade / geometria | `05_SCRIPTS\step4_verify.ps1` | `06_REPORTS\hybrid_HybridPanda_netlist.xml`, `hybrid_ERC.json`, `parity_red_h7_hybrid_HybridPanda_netlist.md` |
| PDF / BOM | kicad-cli | `06_REPORTS\hybrid_schematic.pdf`, `06_REPORTS\hybrid_BOM.csv` |

O gerador é idempotente: sempre parte de `HybridPanda.kicad_sch.baseline` (cópia byte-idêntica do baseline, SHA256 conferido com o primeiro backup).

## 2. O que foi removido do baseline (40 símbolos)
- Bloco MCU F413: U7, Y1 (16 MHz) + C23/C24, SW1 + R14 (BOOT0), R22 (BOOT1 — não existe no H7), C25 (VCAP único), R17/R18/R19 (LED), 41 rótulos globais do U7 (incl. SPI_*/UART_*/GPS_* órfãos), 9 símbolos de alimentação.
- Divisor 5 V: R15/R16 (+#PWR0168/0169) — recriados no bloco "5V sense".
- Bloco GPS (fora do escopo red panda, sem pinos no H725 para isso): U4 NEO-M8M, U2 SiP32431, ANT1, L1, C9, C15, R10 + alimentações.
- 106 fios/gráficos, 15 junções, 18 no-connects. Texto "GPS" removido; "Microcontroller" reposicionado.
Mantidos intactos: USB-C P1, ESD, 4× TJA1042TK/3 (U8–U11), reguladores (U1/U3/U6), SBU detection (Q1/Q2/D5/R23/R24), U5 RGB LED, Q3/R26 (USB load switch), C1/C2/C5/C11/C14 (3V3).

## 3. Renomeação de nets CAN → BUS (D-17)
| Baseline | Novo | Motivo |
|---|---|---|
| CAN2_{TX,RX,EN,H,L} | BUS0_{TX,RX,STB,H,L} | xcvr U11 = bus0 firmware (FDCAN1 PB8/PB9) → P1 B10/B11 |
| CAN3_* | BUS1N_* | U10 = bus1 **normal** (FDCAN2 PB5/PB6, STB PB3) → P1 B2/B3 |
| CAN1_* | BUS1O_* | U8 = bus1 **OBD** (FDCAN2 PB12/PB13, STB PB4) → P1 A2/A3 |
| CAN0_* | BUS2_* | U9 = bus2 (FDCAN3 PG9/PG10, STB PD7) → P1 A10/A11 |
Pinagem de P1 inalterada (D-13).

## 4. Mapa MCU pino × função × net × componente (144 pads; 77 conectados, 67 NC)
Fonte: netlist exportada (`hybrid_HybridPanda_netlist.xml`). `(NC)` = no-connect explícito no esquemático.

| Pad | Pino | Net | Outros componentes na net |
|---|---|---|---|
| 1 | PE2 | `LED_BLUE` | R17 |
| 2 | PE3 | `LED_GREEN` | R18 |
| 3 | PE4 | `LED_RED` | R19 |
| 4 | PE5 | `(NC)` |  |
| 5 | PE6 | `(NC)` |  |
| 6 | VSS | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 7 | VDD | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 8 | VBAT | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 9 | PC13 | `(NC)` |  |
| 10 | PC14 | `(NC)` |  |
| 11 | PC15 | `(NC)` |  |
| 12 | VSS | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 13 | VDD | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 14 | VSSSMPS | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 15 | VLXSMPS | `VLXSMPS` | C41, L5 |
| 16 | VDDSMPS | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 17 | VFBSMPS | `VFBSMPS` | C42, L5 |
| 18 | VSS | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 19 | VDD | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 20 | PF6 | `(NC)` |  |
| 21 | PF7 | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 22 | PF8 | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 23 | PF9 | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 24 | PF10 | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 25 | PH0 | `HSE_IN` | C23, Y1 |
| 26 | PH1 | `HSE_OUT` | C24, Y1 |
| 27 | NRST | `NRST` | C38, J1 |
| 28 | PC0 | `(NC)` |  |
| 29 | PC1 | `(NC)` |  |
| 30 | PC2_C | `(NC)` |  |
| 31 | PC3_C | `(NC)` |  |
| 32 | VDD | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 33 | VSS | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 34 | VSSA | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 35 | VREF+ | `VDDA` | C43, C44, FB1 |
| 36 | VDDA | `VDDA` | C43, C44, FB1 |
| 37 | PA0 | `(NC)` |  |
| 38 | PA1 | `SBU2_ADC` | D14, R29 |
| 39 | PA2 | `(NC)` |  |
| 40 | PA3 | `(NC)` |  |
| 41 | VSS | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 42 | VDD | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 43 | PA4 | `(NC)` |  |
| 44 | PA5 | `(NC)` |  |
| 45 | PA6 | `(NC)` |  |
| 46 | PA7 | `(NC)` |  |
| 47 | PC4 | `SBU1_ADC` | D13, R28 |
| 48 | PC5 | `(NC)` |  |
| 49 | PB0 | `(NC)` |  |
| 50 | PB1 | `5VOUT_S` | R15, R16 |
| 51 | PB2 | `(NC)` |  |
| 52 | PF11 | `VoltageSens` | R2, R3 |
| 53 | PF14 | `(NC)` |  |
| 54 | PF15 | `(NC)` |  |
| 55 | VSS | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 56 | VDD | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 57 | PE7 | `(NC)` |  |
| 58 | PE8 | `(NC)` |  |
| 59 | PE9 | `(NC)` |  |
| 60 | PE10 | `(NC)` |  |
| 61 | PE11 | `(NC)` |  |
| 62 | PE12 | `(NC)` |  |
| 63 | PE13 | `(NC)` |  |
| 64 | PE14 | `(NC)` |  |
| 65 | PE15 | `(NC)` |  |
| 66 | PB10 | `(NC)` |  |
| 67 | PB11 | `(NC)` |  |
| 68 | VCAP | `VCAP` | C39, C40 |
| 69 | VSS | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 70 | VDDLDO | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 71 | VDD | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 72 | PB12 | `BUS1O_RX` | U8 |
| 73 | PB13 | `BUS1O_TX` | U8 |
| 74 | PB14 | `USB_LOAD` | Q3 |
| 75 | PB15 | `(NC)` |  |
| 76 | PD8 | `(NC)` |  |
| 77 | PD9 | `(NC)` |  |
| 78 | PD10 | `(NC)` |  |
| 79 | VDD | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 80 | VSS | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 81 | PD11 | `(NC)` |  |
| 82 | PD12 | `(NC)` |  |
| 83 | PD13 | `(NC)` |  |
| 84 | PD14 | `(NC)` |  |
| 85 | PD15 | `(NC)` |  |
| 86 | PG6 | `(NC)` |  |
| 87 | PG7 | `(NC)` |  |
| 88 | PG8 | `(NC)` |  |
| 89 | VSS | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 90 | VDD50USB | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 91 | VDD33USB | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 92 | VDD | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 93 | PC6 | `(NC)` |  |
| 94 | PC7 | `(NC)` |  |
| 95 | PC8 | `(NC)` |  |
| 96 | PC9 | `(NC)` |  |
| 97 | PA8 | `(NC)` |  |
| 98 | PA9 | `(NC)` |  |
| 99 | PA10 | `(NC)` |  |
| 100 | PA11 | `USB_D-` | R20 |
| 101 | PA12 | `USB_D+` | R21 |
| 102 | PA13(JTMS | `SWDIO` | J1 |
| 103 | VCAP | `VCAP` | C39, C40 |
| 104 | VSS | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 105 | VDDLDO | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 106 | VDD | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 107 | PA14(JTCK | `SWCLK` | J1 |
| 108 | PA15(JTDI) | `(NC)` |  |
| 109 | PC10 | `relay_SBU1` | Q2 |
| 110 | PC11 | `relay_SBU2` | Q1 |
| 111 | PC12 | `(NC)` |  |
| 112 | PD0 | `(NC)` |  |
| 113 | PD1 | `(NC)` |  |
| 114 | PD2 | `(NC)` |  |
| 115 | PD3 | `(NC)` |  |
| 116 | PD4 | `(NC)` |  |
| 117 | PD5 | `(NC)` |  |
| 118 | VSS | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 119 | VDD | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 120 | PD6 | `(NC)` |  |
| 121 | PD7 | `BUS2_STB` | R33, U9 |
| 122 | PG9 | `BUS2_TX` | U9 |
| 123 | PG10 | `BUS2_RX` | U9 |
| 124 | PG11 | `BUS0_STB` | R30, U11 |
| 125 | PG12 | `(NC)` |  |
| 126 | PG13 | `(NC)` |  |
| 127 | PG14 | `(NC)` |  |
| 128 | VSS | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 129 | VDD | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 130 | PB3(JTDO | `BUS1N_STB` | R31, U10 |
| 131 | PB4(NJTRST) | `BUS1O_STB` | R32, U8 |
| 132 | PB5 | `BUS1N_RX` | U10 |
| 133 | PB6 | `BUS1N_TX` | U10 |
| 134 | PB7 | `(NC)` |  |
| 135 | BOOT0 | `BOOT0` | R14, SW1 |
| 136 | PB8 | `BUS0_RX` | U11 |
| 137 | PB9 | `BUS0_TX` | U11 |
| 138 | PE0 | `(NC)` |  |
| 139 | PE1 | `(NC)` |  |
| 140 | VCAP | `VCAP` | C39, C40 |
| 141 | VSS | `GND` | C1, C10, C11, C12, C14, C16, C17, C18, C19, C2, C20, C21, C23, C24, C26, C27, C28, C29, C3, C30, C31, C32, C33, C34, C38, C39, C4, C40, C41, C42, C43, C44, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C6, C60, C61, C62, C63, C7, C8, D1, D11, D12, D13, D14, D5, D6, D7, D8, D9, J1, P1, Q3, R1, R14, R16, R2, R27, R6, U1, U10, U11, U12, U3, U6, U8, U9, Y1 |
| 142 | PDR_ON | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 143 | VDDLDO | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |
| 144 | VDD | `+3V3` | C1, C11, C14, C16, C2, C26, C27, C28, C29, C45, C46, C47, C48, C49, C5, C50, C51, C52, C53, C54, C55, C56, C57, C58, C59, C60, C61, C62, C63, D13, D14, FB1, J1, L3, R23, R24, R30, R31, R32, R33, SW1, U10, U11, U12, U5, U8, U9 |

### 4.1 Resumo funcional (firmware ↔ hardware)
| Função (red.h / board.h) | Pino H725 | Net | Destino |
|---|---|---|---|
| FDCAN1 RX/TX/STB | PB8/PB9/PG11 | BUS0_RX/TX/STB | U11 pinos 4/1/8 |
| FDCAN2 normal RX/TX/STB | PB5/PB6/PB3 | BUS1N_* | U10 |
| FDCAN2 OBD RX/TX/STB | PB12/PB13/PB4 | BUS1O_* | U8 |
| FDCAN3 TX/RX/STB | PG9/PG10/PD7 | BUS2_* | U9 |
| USB FS DM/DP | PA11/PA12 | USB_D-/USB_D+ | P1 via ESD (baseline) |
| USB load switch | PB14 | USB_LOAD | Q3.B → U1.EN (R26 pull-up mantém "ligado" — red.h:89-98) |
| VBUS/12 V sense | PF11 | VoltageSens | R2/R3 (baseline) |
| 5 V out sense | PB1 | 5VOUT_S | R15/R16 10k/10k |
| SBU1/SBU2 ADC | PC4/PA1 | SBU1_ADC/SBU2_ADC | R28/R29 10k + D13/D14 BAT54S (D-16) |
| Relay SBU | PC10/PC11 | relay_SBU1/2 | Q2.B/Q1.B (baseline) |
| LED R/G/B (active-low) | PE4/PE3/PE2 | LED_RED/GREEN/BLUE | R19 100R / R18 110R / R17 180R → U5 |
| HW_TYPE straps | PF7–PF10 | GND | direto (D-08: pull-up interno lê 0 = RED) |
| HW_TYPE PD4–PD6 | — | (NC) | flutuam = 1 (board.h) |
| HSE | PH0/PH1 | HSE_IN/HSE_OUT | Y1 25 MHz + C23/C24 15 pF |
| BOOT0 | BOOT0 | BOOT0 | SW1 → 3V3, R14 10k → GND |
| NRST | NRST | NRST | C38 100 nF, J1.10 |
| SWD | PA13/PA14 | SWDIO/SWCLK | J1 (2×5 1,27 mm, ARM) |
| SMPS | VLXSMPS/VFBSMPS | VLXSMPS/VFBSMPS | L2 2,2 µH, C41 220 pF, C42 10 µF, PWR_FLAG |
| VCAP ×3 | 68/103/140 | VCAP | C39/C40 2,2 µF (D-19) |
| VDDA/VREF+ | 36/35 | VDDA | FB1 + C43 1 µF + C44 100 nF, PWR_FLAG |
| VDD×14, VBAT, VDD33USB, VDD50USB, VDDLDO×3, VDDSMPS, PDR_ON | — | +3V3 | D-14; desacoplamento C45–C63 |

## 5. Pinagem de conectores (resumo)
- **P1 USB-C (TYPE-C-31-M-04)**: inalterado vs baseline — A2/A3 BUS1O_H/L, B2/B3 BUS1N_H/L, B10/B11 BUS0_H/L, A10/A11 BUS2_H/L, A8 SBU1, B8 SBU2, VBUS/GND conforme baseline (ver `STEP3_*` §g-1 e D-13).
- **J1 SWD** (Conn_02x05_Odd_Even, 1,27 mm): 1 VTref=+3V3, 2 SWDIO, 3/5/9 GND, 4 SWCLK, 6 (SWO) NC, 7 KEY NC, 8 NC, 10 NRST.
- **USB-A / 12 V in**: inalterados (baseline).

## 6. Checklist cruzado por CI (0x04-E)
| CI | Alimentação | Desacoplamento | Pinos obrigatórios | Estado |
|---|---|---|---|---|
| U7 STM32H725ZGT6 | +3V3 em todos VDD*, VBAT, VDD33USB/VDD50USB (D-14); VSS/VSSA/VSSSMPS GND | 5×100 nF (baseline) + 15×100 nF + 3×4,7 µF + 1 µF; VDDA 1 µF+100 nF; VCAP 2×2,2 µF; SMPS 220 pF/10 µF | BOOT0 pull-down, NRST cap, PDR_ON=VDD, HSE, SWD | OK (ERC 0) |
| U8–U11 TJA1042TK/3 | VCC 5 V, VIO 3V3 (baseline) | baseline | TXD/RXD/STB cada um ao par FDCAN correto (paridade OK) + pull-up 10k STB (R30–R33, D-09) | OK |
| Y1 25 MHz | — | C23/C24 15 pF (PROVISÓRIO) | PH0/PH1 | OK |
| L2 SMPS | VLXSMPS→VFBSMPS | 220 pF / 10 µF | — | OK (MPN PROVISÓRIO) |
| D13/D14 BAT54S | K→3V3, A→GND, COM→nó ADC | — | — | OK |

## 7. ERC (kicad-cli 10.0.7, `--severity-all`)
- **Erros: 0** (baseline tinha 7 power_pin_not_driven — resolvidos com PWR_FLAGs em GND/+3V3/+5V/+12V/12V_Protected/VLXSMPS/VDDA; V_BCKP sumiu com o GPS).
- Avisos: 131 `endpoint_off_grid` (todos herdados do baseline — nenhum novo), 178 `lib_symbol_mismatch` (símbolos embutidos vs. biblioteca KiCad 10 — herdado), 6 `lib_symbol_issues` (bibliotecas Legacy `.lib` do projeto, KiCad 10 não as carrega — herdado; símbolos embutidos no .kicad_sch funcionam), 36 `pin_to_pin` (30 herdados + 6 novos justificados: 3× VCAP power_out↔power_out — D-19; PF7–PF10 bidirecional↔PWR_FLAG GND — strap intencional D-08; U5 pinos "Unspecified" ↔ resistores — símbolo de LED do baseline).
- `erc.pin_map[power_out][power_out]` foi rebaixado de erro para aviso no `.kicad_pro` (D-19). `sym-lib-table` reapontado para `HybridPanda.symbols`.

## 8. Paridade com o firmware (`parity_check.py --profile red_h7`)
`Resultado: SEM DIVERGÊNCIA — OK=36` — todos os 36 pinos do perfil red_h7 (CAN ×12, USB ×2, ADC ×4, relay ×2, LED ×3, HW_TYPE ×7, HSE ×2, BOOT0, SWD ×2, PB14) conectados aos componentes esperados; os 4 grupos CAN resolvem para transceivers distintos com STB no mesmo CI. Relatório: `06_REPORTS\parity_red_h7_hybrid_HybridPanda_netlist.md`. Correção de ferramenta: `PORT_RX` passou a aceitar nomes `PB4(NJTRST)` do símbolo H7.

## 9. BOM (agrupada por valor/footprint, sem símbolos de alimentação) — 48 linhas
| Ref | Valor | Footprint | Qtd |
|---|---|---|---|
| C1,C2,C5,C11,C14,C26-C33 | 100NF | Capacitor_SMD:C_0402_1005Metric | 13 |
| C3,C10,C16-C21 | 47uF | Capacitor_SMD:C_0805_2012Metric | 8 |
| C4,C6,C7,C12 | 2.2uF | Capacitor_SMD:C_0805_2012Metric | 4 |
| C8 | 10uF | Capacitor_SMD:C_0402_1005Metric | 1 |
| C23,C24 | 15pF | Capacitor_SMD:C_0402_1005Metric | 2 |
| C34 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | 1 |
| C37 | 10nF (LOW ESR) | Capacitor_SMD:C_0402_1005Metric | 1 |
| C38,C44-C59 | 100nF | Capacitor_SMD:C_0402_1005Metric | 17 |
| C39,C40 | 2.2uF | Capacitor_SMD:C_0603_1608Metric | 2 |
| C41 | 220pF | Capacitor_SMD:C_0402_1005Metric | 1 |
| C42 | 10uF | Capacitor_SMD:C_0805_2012Metric | 1 |
| C43,C63 | 1uF | Capacitor_SMD:C_0402_1005Metric | 2 |
| C60-C62 | 4.7uF | Capacitor_SMD:C_0603_1608Metric | 3 |
| D1 | SMAJ16CA-13-F | BlackPanda:DIOM4325X250N | 1 |
| D2 | BAS40WS 43 | Diode_SMD:D_SOD-323 | 1 |
| D5-D9 | PESD2CAN,215 | BlackPanda:SOT95P230X110-3N | 5 |
| D10 | BAS70H 115 | Diode_SMD:D_SOD-123F | 1 |
| D11 | B320AE-13 | Diode_SMD:D_SMA | 1 |
| D12 | SM540C | Diode_SMD:D_SMC | 1 |
| D13,D14 | BAT54S | Package_TO_SOT_SMD:SOT-23 | 2 |
| FB1 | 600R@100MHz | Inductor_SMD:L_0603_1608Metric | 1 |
| J1 | SWD | Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD | 1 |
| L3 | 47uH 2A - SMMS0650-470M | BlackPanda:IND-SMD_L7.3-W6.8 | 1 |
| L4 | 15uH | BlackPanda:L_10.5x11.5_H4.0 | 1 |
| L5 | 2.2uH DFE201610E-2R2M | Inductor_SMD:L_Murata_DFE201610P | 1 |
| P1 | TYPE-C-31-M-04 | BlackPanda:USB-C-SMD_TYPE-C-USB-20 | 1 |
| Q1,Q2 | DDTA143ECA-7-F P08 | BlackPanda:SOT23-3 | 2 |
| Q3 | PDTC114EU | Package_TO_SOT_SMD:SOT-323_SC-70 | 1 |
| Q4 | HY12P03C2 | Package_SO:PowerPAK_SO-8_Single | 1 |
| R1,R2 | 1K | Resistor_SMD:R_0402_1005Metric | 2 |
| R3,R9,R23,R24,R26 | 10K | Resistor_SMD:R_0402_1005Metric | 5 |
| R5 | 10K (1%) | Resistor_SMD:R_0402_1005Metric | 1 |
| R6 | 3.16K (1%) | Capacitor_SMD:C_0603_1608Metric | 1 |
| R14-R16,R28-R33 | 10k | Resistor_SMD:R_0402_1005Metric | 9 |
| R17 | 180R | Resistor_SMD:R_0402_1005Metric | 1 |
| R18 | 110R | Resistor_SMD:R_0402_1005Metric | 1 |
| R19 | 100R | Resistor_SMD:R_0402_1005Metric | 1 |
| R20,R21 | 22R | Resistor_SMD:R_0402_1005Metric | 2 |
| R27 | 2.4K | Resistor_SMD:R_0402_1005Metric | 1 |
| SW1 | SW_Push | Button_Switch_SMD:SW_SPST_SKQG_WithStem | 1 |
| U1 | AP22615AWU-7 | Package_TO_SOT_SMD:SOT-23-6 | 1 |
| U3 | 10_0_QHHTZB6_3 | BlackPanda:USB-A-TH_10.0QHHTZB6.3 | 1 |
| U5 | FM-B1921RGBA-SH | BlackPanda:LED-ARRAY-SMD_4P-L2.2-W2.1-BR | 1 |
| U6 | TPS5450DDAR | BlackPanda:CONV_TPS5450DDAR | 1 |
| U7 | STM32H725ZGT6 | Package_QFP:LQFP-144_20x20mm_P0.5mm | 1 |
| U8-U11 | TJA1042TK-3 | Package_DFN_QFN:DFN-8-1EP_3x3mm_P0.65mm_EP1.55x2.4mm | 4 |
| U12 | XL1509-3.3 | Package_SO:Diodes_PSOP-8 | 1 |
| Y1 | 25MHz X322525MOB4SI | Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm | 1 |

Itens **PROVISÓRIOS** (ver `step4_bom_values.json` e `R3v2_componentes_STEP4.md`): Y1 CL 12 pF lido de listagem LCSC (não do datasheet YXC) → C23/C24 15 pF a afinar; L2 DFE201610E-2R2M (Isat não lido do datasheet Murata; footprint `L_Murata_DFE201610P` a conferir com o desenho Murata no STEP 5); FB1 valor genérico 600 Ω@100 MHz (MPN aberto); capacitores sem MPN.

## 10. Divergências da pesquisa vs. hipóteses anteriores
- **Transceivers mantidos** (não substituídos): datasheet NXP TJA1042 confirma "timing guaranteed for data rates up to 5 Mbit/s in the CAN FD fast phase" e pinagem TXD1/GND2/VCC3/RXD4/VIO5/CANL6/CANH7/STB8 (R3v2 §3.1, [F]). Linha "Transceivers" da tabela híbrida passa de *Substituído* para *Reaproveitado* (D-20).
- PF7–PF10 ligados **diretamente** a GND (em vez de 0 Ω): o verificador exige net GND e é o que o `detect_with_pull` espera.

## 11. Pendências para o STEP 5
- Área da PCB para LQFP-144 20×20 mm + 19 capacitores extras + J1 + L2 (g-6): decidir contorno (manter Black Panda ou crescer) antes de posicionar.
- Atualizar PCB a partir do esquemático via pcbnew API (sem comando kicad-cli): footprints novos, nets renomeadas.
- Cosmética do esquemático: coluna de suporte compacta (textos sobrepostos em alguns blocos) — não afeta netlist.
