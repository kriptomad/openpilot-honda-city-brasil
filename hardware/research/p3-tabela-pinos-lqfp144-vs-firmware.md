# P3 — Tabela pino LQFP144 (STM32H725ZG) × função exigida pelo firmware × rede

Fonte: ST **DS13311 Rev 5 (Nov/2023)** 'STM32H725xE/G', Tabela 8 (pin and ball descriptions), arquivo `hardware/reference/datasheets/DS13313_STM32H725_ae.pdf` (SHA-256 3953CF96…3AA14), texto extraído com pypdf em `DS13313_text.txt`. Firmware: `hardware/reference/panda` @ 408e14d4. Gerado por `hardware/scripts/extract_ds_pins.py` (não editado à mão).

Coluna 'AF/ADC confirmado' = a função exigida aparece literalmente na lista de funções alternativas/adicionais do pino no datasheet.

| Porta | LQFP144 pino | TFBGA100 | Função exigida | Fonte firmware | Rede | AF/ADC confirmado | Linha DS |
|---|---|---|---|---|---|---|---|
| PA11 | 100 | D10 | OTG_HS_DM AF10 (USB FS PHY interno; DS nomeia OTG_HS) | stm32h7/peripherals.h | USB_DM | SIM | 1347 |
| PA12 | 101 | D9 | OTG_HS_DP AF10 | stm32h7/peripherals.h | USB_DP | SIM | 1357 |
| PF11 | 52 | - | ADC1_INP2 ADC1 ch2 (VOLT_S) | stm32h7/peripherals.h | VOLT_S | SIM | 617 |
| PB8 | 136 | A4 | FDCAN1_RX AF9 | stm32h7/peripherals.h | FDCAN1_RX | SIM | 1846 |
| PB9 | 137 | E3 | FDCAN1_TX AF9 | stm32h7/peripherals.h | FDCAN1_TX | SIM | 1860 |
| PB12 | 72 | K8 | FDCAN2_RX AF9 (normal) | stm32h7/peripherals.h | FDCAN2_RX | SIM | 893 |
| PB13 | 73 | J8 | FDCAN2_TX AF9 (normal) | stm32h7/peripherals.h | FDCAN2_TX | SIM | 929 |
| PB5 | 132 | A6 | FDCAN2_RX AF9 (OBD) | stm32h7/peripherals.h | FDCAN2OBD_RX | SIM | 1781 |
| PB6 | 133 | D4 | FDCAN2_TX AF9 (OBD) | stm32h7/peripherals.h | FDCAN2OBD_TX | SIM | 1797 |
| PG9 | 122 | - | FDCAN3_TX AF2 (firmware só define AF2; direção pelo DS) | stm32h7/peripherals.h | FDCAN3_TX | SIM | 1611 |
| PG10 | 123 | - | FDCAN3_RX AF2 | stm32h7/peripherals.h | FDCAN3_RX | SIM | 1623 |
| PG11 | 124 | - | GPIO out: CAN0 transceiver STB (bus0) | boards/red.h | CAN0_STB | SIM | 1652 |
| PB3 | 130 | B6 | GPIO out: OBD transceiver STB | boards/red.h | CAN_OBD_STB | SIM | 1735 |
| PD7 | 121 | C6 | GPIO out: CAN2 transceiver STB (bus2) | boards/red.h | CAN2_STB | SIM | 1599 |
| PB4 | 131 | C5 | GPIO out: CAN1 transceiver STB (bus1) | boards/red.h | CAN1_STB | SIM | 1751 |
| PB1 | 50 | K5 | ADC12_INP5 analog (5VOUT_S; red.h só MODE_ANALOG) | boards/red.h | 5VOUT_S | SIM | 592 |
| PB14 | 74 | K9 | GPIO OD pull-up: USB_LOAD_EN | boards/red.h | USB_LOAD_EN | SIM | 945 |
| PC4 | 47 | H4 | ADC12_INP4 ADC1 ch4 (SBU1) | boards/red.h | SBU1 | SIM | 527 |
| PA1 | 38 | J2 | ADC1_INP17 ADC1 ch17 (SBU2) | boards/red.h | SBU2 | SIM | 336 |
| PC10 | 109 | B10 | GPIO out active-low: relay SBU1 | boards/red.h | RELAY_SBU1 | SIM | 1460 |
| PC11 | 110 | B9 | GPIO out active-low: relay SBU2 | boards/red.h | RELAY_SBU2 | SIM | 1472 |
| PE4 | 3 | C3 | GPIO OD: LED red | boards/red.h | LED_R | SIM | 37 |
| PE3 | 2 | B3 | GPIO OD: LED green | boards/red.h | LED_G | SIM | 29 |
| PE2 | 1 | A3 | GPIO OD: LED blue | boards/red.h | LED_B | SIM | 17 |
| PF7 | 21 | - | GPIO in pull-up: HW_TYPE id1 bit0 (RED=0) | stm32h7/board.h | HWID1_0 | SIM | 157 |
| PF8 | 22 | - | GPIO in: HW_TYPE id1 bit1 (RED=0) | stm32h7/board.h | HWID1_1 | SIM | 187 |
| PF9 | 23 | - | GPIO in: HW_TYPE id1 bit2 (RED=0) | stm32h7/board.h | HWID1_2 | SIM | 199 |
| PF10 | 24 | - | GPIO in: HW_TYPE id1 bit3 (RED=0) | stm32h7/board.h | HWID1_3 | SIM | 210 |
| PD4 | 116 | B7 | GPIO in pull-up: HW_TYPE id2 bit0 (PD4..PD6 != 0b011) | stm32h7/board.h | HWID2_0 | SIM | 1550 |
| PD5 | 117 | D7 | GPIO in: HW_TYPE id2 bit1 | stm32h7/board.h | HWID2_1 | SIM | 1557 |
| PD6 | 120 | A7 | GPIO in: HW_TYPE id2 bit2 | stm32h7/board.h | HWID2_2 | SIM | 1585 |
| PH0 | 25 | G1 | OSC_IN (HSE 25 MHz) pino PH0-OSC_IN | stm32h7/clock.h | HSE_IN | SIM | 219 |
| PH1 | 26 | G2 | OSC_OUT (HSE 25 MHz) pino PH1-OSC_OUT | stm32h7/clock.h | HSE_OUT | SIM | 220 |
| PA13 | 102 | C10 | SWDIO (debug) | - | SWDIO | SIM | 1370 |
| PA14 | 107 | C9 | SWCLK (debug) | - | SWCLK | SIM | 1422 |
| PE11 | 61 | - | GPIO (SPI4_NSS) unused | boards/red.h (has_spi=false) | NC | SIM | 735 |
| PE12 | 62 | - | GPIO (SPI4_SCK) unused | boards/red.h | NC | SIM | 744 |
| PE13 | 63 | - | GPIO (SPI4_MISO) unused | boards/red.h | NC | SIM | 753 |
| PE14 | 64 | - | GPIO (SPI4_MOSI) unused | boards/red.h | NC | SIM | 762 |

## Pinos de alimentação / sistema (LQFP144)

| Nome | Pinos LQFP144 |
|---|---|
| VSS | 6, -, 12, 18, 33, -, 41, -, 55, -, 69, -, 80, -, -, -, -, 89, -, 104, -, -, 118, -, 128, -, 141, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, -, - |
| VBAT | 8 |
| VDD | 13, 19, 32, -, 42, 71, -, -, -, 106, -, 129, -, 144, -, -, -, -, - |
| VSSSMPS | 14 |
| VLXSMPS | 15 |
| VFBSMPS | 17 |
| NRST | 27 |
| VSSA | 34 |
| VREF+ | 35 |
| VDDA | 36 |
| VCAP | 68, 103, 140 |
| VDDLDO | 70, 105, 143 |
| VDD50USB | 90 |
| VDD33USB | 91, - |
| BOOT0 | 135 |
| PDR_ON | 142 |

## Cruzamento com a biblioteca oficial do KiCad (MCU_ST_STM32H7:STM32H725ZGTx)

| Nome | DS13311 Tabela 8 (parser) | KiCad lib | Igual? |
|---|---|---|---|
| VDD | 13, 19, 32, 42, 71, 106, 129, 144 | 7, 13, 19, 32, 42, 56, 71, 79, 92, 106, 119, 129, 144 | parcial (PDF ilegível) |
| VSS | 6, 12, 18, 33, 41, 55, 69, 80, 89, 104, 118, 128, 141 | 6, 12, 18, 33, 41, 55, 69, 80, 89, 104, 118, 128, 141 | SIM |
| VBAT | 8 | 8 | SIM |
| VDDSMPS | (linha ilegível no PDF) | 16 | parcial (PDF ilegível) |
| VSSSMPS | 14 | 14 | SIM |
| VLXSMPS | 15 | 15 | SIM |
| VFBSMPS | 17 | 17 | SIM |
| NRST | 27 | 27 | SIM |
| VSSA | 34 | 34 | SIM |
| VREF+ | 35 | 35 | SIM |
| VDDA | 36 | 36 | SIM |
| VCAP | 68, 103, 140 | 68, 103, 140 | SIM |
| VDDLDO | 70, 105, 143 | 70, 105, 143 | SIM |
| VDD50USB | 90 | 90 | SIM |
| VDD33USB | 91 | 91 | SIM |
| BOOT0 | 135 | 135 | SIM |
| PDR_ON | 142 | 142 | SIM |

GPIO exigidos: DS × KiCad lib divergentes: nenhum

## Pinos exigidos ausentes no LQFP144: nenhum

## Observação TFBGA100
Na coluna TFBGA100, '-' indica que o pino NÃO existe nesse encapsulamento. Todos os PFx/PGx exigidos pelo firmware aparecem como '-' → paridade 1:1 impossível em TFBGA100 (fato, Tabela 8).