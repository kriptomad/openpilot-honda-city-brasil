# Paridade firmware x hardware — perfil `black_f4` — netlist `baseline_BlackPanda_netlist.xml`

Firmware: hardware/reference/panda_legacy_f4 @ f849893bdcfc6cd05d4547d64d2802b5a83f409c. MCU: U7 (STM32F413RGTx, Package_QFP:LQFP-64_10x10mm_P0.5mm).
Resultado: **SEM DIVERGÊNCIA** — OK=35

| Pino FW | Pad | Papel | Sinal/grupo | Net | Status | Detalhe | Fonte firmware |
|---|---|---|---|---|---|---|---|
| PA11 | 44 | usb_dm |  | `USB_D-` | **OK** | reaches R20 | board/stm32f4/peripherals.h:5-10 |
| PA12 | 45 | usb_dp |  | `USB_D+` | **OK** | reaches R21 | board/stm32f4/peripherals.h:5-10 |
| PB8 | 61 | can_rx | CAN1 | `CAN2_RX` | **OK** | xcvr=U11 | board/stm32f4/peripherals.h:46 |
| PB9 | 62 | can_tx | CAN1 | `CAN2_TX` | **OK** | xcvr=U11 | board/stm32f4/peripherals.h:47 |
| PC1 | 9 | can_stb | CAN1 | `CAN2_EN` | **OK** | xcvr=U11; STB reaches the same transceiver | board/boards/black.h:12 |
| PB12 | 33 | can_rx | CAN2_OBD | `CAN1_RX` | **OK** | xcvr=U8 | board/boards/black.h:33-57 |
| PB13 | 34 | can_tx | CAN2_OBD | `CAN1_TX` | **OK** | xcvr=U8 | board/boards/black.h:33-57 |
| PB10 | 29 | can_stb | CAN2_OBD | `CAN1_EN` | **OK** | xcvr=U8; STB reaches the same transceiver | board/boards/black.h:21 |
| PB5 | 57 | can_rx | CAN2_NORMAL | `CAN3_RX` | **OK** | xcvr=U10 | board/boards/black.h:33-57 |
| PB6 | 58 | can_tx | CAN2_NORMAL | `CAN3_TX` | **OK** | xcvr=U10 | board/boards/black.h:33-57 |
| PC13 | 2 | can_stb | CAN2_NORMAL | `CAN3_EN` | **OK** | xcvr=U10; STB reaches the same transceiver | board/boards/black.h:15 |
| PA8 | 41 | can_rx | CAN3 | `CAN0_RX` | **OK** | xcvr=U9 | board/boards/black.h:72-74 |
| PA15 | 50 | can_tx | CAN3 | `CAN0_TX` | **OK** | xcvr=U9 | board/boards/black.h:72-74 |
| PA0 | 14 | can_stb | CAN3 | `CAN0_EN` | **OK** | xcvr=U9; STB reaches the same transceiver | board/boards/black.h:18 |
| PC2 | 10 | adc | VOLT_S | `VoltageSens` | **OK** | reaches R2,R3 | board/stm32f4/peripherals.h:42; white.h:68-70 |
| PB1 | 27 | out | USB load switch (active low) | `USB_LOAD` | **OK** | reaches Q3 | board/boards/black.h:30 |
| PC0 | 8 | adc | SBU1 | `SBU1` | **OK** | reaches D5,P1,Q2,R24 | board/boards/black.h:91-100 |
| PC3 | 11 | adc | SBU2 | `SBU2` | **OK** | reaches D5,P1,Q1,R23 | board/boards/black.h:91-100 |
| PC10 | 51 | relay | relay_SBU1 | `relay_SBU1` | **OK** | reaches Q2 | board/boards/black.h:91-100 |
| PC11 | 52 | relay | relay_SBU2 | `relay_SBU2` | **OK** | reaches Q1 | board/boards/black.h:91-100 |
| PC9 | 40 | led | LED_RED | `Net-(U7-PC9)` | **OK** | reaches R19 | board/boards/black.h:119-120 |
| PC7 | 38 | led | LED_GREEN | `Net-(U7-PC7)` | **OK** | reaches R18 | board/boards/black.h:119-120 |
| PC6 | 37 | led | LED_BLUE | `Net-(U7-PC6)` | **OK** | reaches R17 | board/boards/black.h:119-120 |
| PC5 | 25 | out | GPS off | `GPS_BOOT` | **OK** | reaches U4 | board/boards/black.h:76-78 |
| PC12 | 53 | out | GPS off | `GPS_LOAD` | **OK** | reaches U2 | board/boards/black.h:76-78 |
| PB7 | 59 | hwtype |  | `unconnected-(U7-PB7-Pad59)` | **OK** | floating; expect=float_or_high | board/stm32f4/board.h:24 (DOS needs PB1&PB7 low) |
| PA4 | 20 | hwtype |  | `SPI_NSS` | **OK** | net=SPI_NSS; expect=float_or_low | board/stm32f4/board.h:27 (WHITE if PA4-7 high w/ pull-down) |
| PA5 | 21 | hwtype |  | `SPI_SCK` | **OK** | net=SPI_SCK; expect=float_or_low | board/stm32f4/board.h:27 |
| PA6 | 22 | hwtype |  | `SPI_MISO` | **OK** | net=SPI_MISO; expect=float_or_low | board/stm32f4/board.h:27 |
| PA7 | 23 | hwtype |  | `SPI_MOSI` | **OK** | net=SPI_MOSI; expect=float_or_low | board/stm32f4/board.h:27 |
| PA13 | 46 | hwtype |  | `unconnected-(U7-PA13-Pad46)` | **OK** | floating; expect=float_or_low | board/stm32f4/board.h:30 (GREY if PA13 high w/ pull-down) |
| PB15 | 36 | hwtype |  | `unconnected-(U7-PB15-Pad36)` | **OK** | floating; expect=float_or_high | board/stm32f4/board.h:32 (UNO if PB15 low) |
| PH0 | 5 | hse |  | `Net-(U7-PH0)` | **OK** | reaches C23,Y1 | board/stm32f4/clock.h (HSE) |
| PH1 | 6 | hse |  | `Net-(U7-PH1)` | **OK** | reaches C24,Y1 | idem |
| BOOT0 | 60 | boot0 |  | `Net-(U7-BOOT0)` | **OK** | reaches R14,SW1 | DFU via BOOT0 |

## Pinos do MCU ligados no hardware mas sem função no firmware (SEM_USO no firmware)

| Pino | Pad | Net | Componentes |
|---|---|---|---|
| PC14 | 3 | `GPS_RESET` | U4 |
| PA2 | 16 | `UART_TX` |  |
| PA3 | 17 | `UART_RX` |  |
| PC4 | 24 | `Net-(U7-PC4)` | R15, R16 |
| PB0 | 26 | `GPS_TIMEPULSE` | U4 |
| PB2 | 28 | `Net-(U7-PB2)` | R22 |
| PA9 | 42 | `GPS_RX` | U4 |
| PA10 | 43 | `GPS_TX` | U4 |

## Pinos de alimentação do MCU

| Pino | Pad | Net |
|---|---|---|
| VBAT | 1 | `+3V3` |
| NRST | 7 | `unconnected-(U7-NRST-Pad7)` |
| VSSA | 12 | `GND` |
| VDDA | 13 | `+3V3` |
| VSS | 18 | `GND` |
| VDD | 19 | `+3V3` |
| VCAP_1 | 30 | `Net-(U7-VCAP_1)` |
| VSS | 31 | `GND` |
| VDD | 32 | `+3V3` |
| VSS | 47 | `GND` |
| VDD | 48 | `+3V3` |
| VSS | 63 | `GND` |
| VDD | 64 | `+3V3` |
