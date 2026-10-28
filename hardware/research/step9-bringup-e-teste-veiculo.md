# STEP 9 — Plano de bring-up em bancada e de teste no veículo

Data: 2026-10-26 · Projeto: Hybrid Panda (Black Panda form factor + STM32H725ZGT6, firmware red panda) · Protocolo v3 STEP 9

> **Nenhum passo abaixo foi executado.** Não existe protótipo; este é um plano escrito a partir do firmware (`hardware\reference\panda`, HRS em `hardware\research\hrs-red-panda.md`), do esquemático (`step4-esquematico-h725.md`) e do datasheet DS13311. Onde um valor depende de hardware não publicado pela comma está marcado **NV** (não verificado). Fabricação está marcada **NÃO FABRICAR** em `hardware\fabrication\readme.md` até os bloqueios serem removidos.

## 0. Pré-requisitos
| Item | Estado | Nota |
|---|---|---|
| Placa montada (ENIG, 4 camadas) | NÃO EXISTE | ver `hardware/fabrication` |
| Fonte de bancada 12 V limitada em corrente (≤ 300 mA no 1.º arranque), multímetro, osciloscópio ≥ 100 MHz, analisador CAN FD (ou segunda panda), ST-Link V3 / J-Link, cabo USB-C | a providenciar | |
| Firmware: build **DEBUG** de `hardware\reference\panda` (`scons -u -j8` sem `RELEASE=1`) → `board/obj/bootstub.panda_h7.bin` + `panda_h7.bin.signed` (chave debug publicada, SConscript:12-21) | **BLOQUEADO**: toolchain `arm-none-eabi-gcc`/`scons` não instalada nesta máquina (../../docs/progress.md) | o bootstub oficial **release** só aceita binários assinados pela comma (bootstub.c:60-84); numa placa de terceiros usar bootstub+app DEBUG — não se propõe remover a verificação |
| `dfu-util`, `python -m pip install -e hardware\reference\panda` (lib host `panda`) | a providenciar | `debug/dfu_util_h7.sh:9-11` |
| Harness box v3 + cabo OBD-C do carro (comma) | **NÃO** possuído (P10) | a panda **não** tem terminação de 120 Ω — está na harness box (D-04) |

## 1. Bring-up em bancada (ordem obrigatória; parar na primeira falha)
| # | Passo | Como | Critério de aceitação | Fonte |
|---|---|---|---|---|
| 1 | Inspeção visual | lupa/microscópio: U7 LQFP-144 (passo 0,5 mm) sem pontes, orientação do pino 1 (B.Cu, rot. 90°), U8–U11, L5, Y1, J1; sem componentes em falta vs `hardware\fabrication\assembly\CPL_JLC.csv` | 0 pontes, 0 faltas | STEP5 §2 |
| 2 | Continuidade / curtos sem alimentar | ohmímetro: GND↔+3V3, GND↔+5V, GND↔+12V, GND↔VCAP, GND↔VDDA, VLXSMPS↔GND; cada par CAN_H/L↔GND; USB D+/D−↔GND; PF7–PF10↔GND (devem ser 0 Ω — strap RED) | nenhum curto em rails (> 1 kΩ após carga de caps); PF7–PF10 = 0 Ω | D-08; HRS §1 |
| 3 | Alimentação **sem MCU alimentado**? | não é possível desmontar o U7; alternativa: alimentar 12 V com limite 100 mA e medir **sem** USB | consumo < 60 mA **NV** (a confirmar com a placa real); U1/U3/U6 reguladores a 5 V/3,3 V ±3 % | baseline Black Panda |
| 4 | Regulação | medir +5V, +3V3, VDDA (FB1), VCAP (≈1,2–1,35 V quando o core arranca em SMPS Direct), VFBSMPS; osciloscópio no VLXSMPS: comutação 2,4 MHz | 3,3 V ±3 %; VCAP 1,1–1,4 V; ripple VDD < 50 mVpp **NV** | DS13311 §6.3.3; PROGRESS "fatos-chave" |
| 5 | SWD | ST-Link em J1 (1 VTref, 2 SWDIO, 4 SWCLK, 10 NRST, 3/5/9 GND); `st-info --probe` / STM32CubeProgrammer | IDCODE **0x483** (H72x/H73x), Flash 1024 K, option bytes BOOT_ADD default (sistema) **NV**; se IDCODE ≠ 0x483 o firmware salta para o bootloader (early_init.h:61-65) | HRS §7 |
| 6 | DFU | BOOT0: SW1 premido (→ 3V3) durante reset, ou sem app válido o bootstub entra em DFU; `dfu-util -l` | aparece `0483:df11` | HRS §7 |
| 7 | Gravação (fluxo oficial, build DEBUG) | `dfu-util -d 0483:df11 -a 0 -s 0x08020000 -D panda_h7.bin.signed` depois `-s 0x08000000:leave -D bootstub.panda_h7.bin` | sem erro de verificação; LED pisca após reset | debug/dfu_util_h7.sh |
| 8 | USB e enumeração | ligar USB-C ao PC; `lsusb`/Gestor de dispositivos | VID/PID **0x3801:0xDDCC** (app) — se ficar em **0xDDEE** o bootstub rejeitou a assinatura/versão | HRS §8 (config.h:11-17) |
| 9 | HW_TYPE pelo host | `python -c "from panda import Panda; p=Panda(); print(p.get_type(), p.get_version(), p.health())"` | `get_type() == b'\x07'` (RED) — se `\x00` UNKNOWN: verificar PF7–PF10 (devem ler 0) e PD4–PD6 (id2 ≠ 3) | HRS §1 (board.h:25-50) |
| 10 | Sensores de tensão | `health()['voltage']` com 12,0 V na entrada | 12000 ± 5 % mV (divisor 1:11 em PF11 — valores R2/R3 do baseline, **NV** para o H7: ADC 16 bit, `adc_get_mV()*11`) | HRS §4 |
| 11 | Corrente | `health()['current']` | red não lê corrente (`unused_read_current`) → 0 esperado | red.h:117-134 |
| 12 | LEDs | `p.set_led(…)`/health loop | R/G/B visíveis (active-low PE4/PE3/PE2 via R19/R18/R17) | HRS §3 |
| 13 | SBU / orientação do harness | com harness box ligada em cada orientação: `health()['harness_status']` 1 = NORMAL, 2 = FLIPPED; sem harness = 0 | SBU < 1,65 V no lado ligado; relés PC10/PC11 comutam (medir Q1/Q2) | harness.h:63-101 |
| 14 | CAN loopback | `p.set_safety_mode(Panda.SAFETY_ALLOUTPUT)`; `p.set_can_loopback(True)`; `p.can_send(0x123,b'\x01'*8,0)`; `p.can_recv()` | mensagem volta no bus 0; repetir bus 1 (NORMAL: U10 / FLIPPED-OBD: U8) e bus 2 (U9) | HRS §5 |
| 15 | CAN clássico com analisador | 500 kbit/s, terminação externa 120 Ω (a panda não tem) | tramas ACK; sem erro de bit; medir dominante ≈ 2 V diferencial | ISO 11898-2 |
| 16 | CAN FD | `p.set_canfd_data_bitrate(bus, 2000)` (2 Mbit/s) com analisador FD ou 2.ª placa; depois 5 Mbit/s (limite TJA1042TK/3, R3v2) | tramas FD com BRS recebidas; olho aberto no osciloscópio | HRS §5; D-20 |
| 17 | Ventoinha / harness | red: `has_fan=false` → nada a testar | — | red.h |
| 18 | Proteções e consumo | sobretensão 16 V, inversão de polaridade (D1 baseline), consumo final com 3 buses activos | consumo ≈ baseline + H725 (**NV**, estimar ≤ 250 mA @12 V) | STEP3 g-5 |
| 19 | Térmico | câmara/termopar em U7, U1, L5 após 30 min | U7 < 70 °C **NV** | DS13311 |

Critérios de paragem: qualquer curto em rail (passo 2), tensão fora de ±5 % (passo 4), IDCODE errado (5), HW_TYPE ≠ 7 (9) ou tensão medida errada (10) → **não** ligar ao veículo.

## 2. Teste no veículo (Honda City 2023 BR — CAN clássico, harness Bosch B; P1 refutada: o carro **não** usa CAN FD)
Só após §1 completo. Ordem:
1. **Captura passiva**: `p.set_safety_mode(Panda.SAFETY_SILENT)` (sem ACK, sem TX) antes de ligar a harness; ignição ON, motor desligado; `python examples/can_logger.py` 5 min. Critério: tramas dos buses 0/1/2 com IDs plausíveis da `opendbc` Honda (`honda_bosch_radarless`), 0 erros de bus, `health()['can_send_errs']`=0, `harness_status` estável.
2. Repetir com motor ligado, parado, 10 min; verificar `health()['voltage']` ≥ 12,5 V com alternador e ausência de reinícios (`uptime` monotónico).
3. **Nunca** sair de SAFETY_SILENT nesta fase; **nunca** com o veículo em movimento. Qualquer luz de avaria no painel, código DTC, `fault_status ≠ 0` ou reinício da panda → desligar a harness e parar.
4. Só depois disto (fora do âmbito deste projecto): `SAFETY_NOOUTPUT` com openpilot a ler, avaliação do openpilot `pandad` com a placa (requer a decisão D-06 sobre o host).

## 3. O que ainda não existe / riscos ordenados
1. Firmware nunca compilado nem executado neste hardware (toolchain ausente; build DEBUG necessário).
2. Placa nunca fabricada; DRC com itens herdados; impedância/USB_D± não verificados (STEP 6/7).
3. Divisor VoltageSens herdado do F413 (3,3 V ADC 12 bit) reutilizado para o H725 (ADC 16 bit) — a fórmula `*11` assume o mesmo divisor **NV** (R2/R3).
4. BOM com MPNs PROVISÓRIOS (cristal CL, L5, FB1, ESD) e sem códigos LCSC.
5. Caixa mecânica do Black Panda não serve (placa +5 mm, D-24).
6. O Honda City 2023 não precisa de CAN FD — o benefício da placa H7 é o firmware actual (black panda descontinuado em 2025), não o FD.
