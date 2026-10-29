# Paridade firmware x hardware — perfil `red_h7` — netlist `hybrid_HybridPanda_netlist.xml`

Firmware: 02_REFERENCE/panda @ 408e14d46ebb7da45a7d21f8db315922e10242a8. MCU: U7 (STM32H725ZGT6, Package_QFP:LQFP-144_20x20mm_P0.5mm).
Resultado: **SEM DIVERGÊNCIA** — OK=36

| Pino FW | Pad | Papel | Sinal/grupo | Net | Status | Detalhe | Fonte firmware |
|---|---|---|---|---|---|---|---|
| PA11 | 100 | usb_dm |  | `USB_D-` | **OK** | reaches R20 | board/stm32h7/peripherals.h:8 |
| PA12 | 101 | usb_dp |  | `USB_D+` | **OK** | reaches R21 | board/stm32h7/peripherals.h:9 |
| PB8 | 136 | can_rx | FDCAN1 | `BUS0_RX` | **OK** | xcvr=U11 | board/stm32h7/peripherals.h:31 |
| PB9 | 137 | can_tx | FDCAN1 | `BUS0_TX` | **OK** | xcvr=U11 | board/stm32h7/peripherals.h:32 |
| PG11 | 124 | can_stb | FDCAN1 | `BUS0_STB` | **OK** | xcvr=U11; STB reaches the same transceiver | board/boards/red.h:11 |
| PB12 | 72 | can_rx | FDCAN2_OBD | `BUS1O_RX` | **OK** | xcvr=U8 | board/boards/red.h:53 |
| PB13 | 73 | can_tx | FDCAN2_OBD | `BUS1O_TX` | **OK** | xcvr=U8 | board/boards/red.h:54 |
| PB4 | 131 | can_stb | FDCAN2_OBD | `BUS1O_STB` | **OK** | xcvr=U8; STB reaches the same transceiver | board/boards/red.h:20 |
| PB5 | 132 | can_rx | FDCAN2_NORMAL | `BUS1N_RX` | **OK** | xcvr=U10 | board/boards/red.h:40 |
| PB6 | 133 | can_tx | FDCAN2_NORMAL | `BUS1N_TX` | **OK** | xcvr=U10 | board/boards/red.h:41 |
| PB3 | 130 | can_stb | FDCAN2_NORMAL | `BUS1N_STB` | **OK** | xcvr=U10; STB reaches the same transceiver | board/boards/red.h:14 |
| PG9 | 122 | can_tx | FDCAN3 | `BUS2_TX` | **OK** | xcvr=U9 | board/stm32h7/peripherals.h:46 (AF2; DS13311 Tab.8 PG9=FDCAN3_TX) |
| PG10 | 123 | can_rx | FDCAN3 | `BUS2_RX` | **OK** | xcvr=U9 | board/stm32h7/peripherals.h:47 (DS13311 PG10=FDCAN3_RX) |
| PD7 | 121 | can_stb | FDCAN3 | `BUS2_STB` | **OK** | xcvr=U9; STB reaches the same transceiver | board/boards/red.h:17 |
| PF11 | 52 | adc | VOLT_S | `VoltageSens` | **OK** | reaches R2,R3 | board/boards/red.h:71; peripherals.h:26 |
| PB1 | 50 | analog_nc | 5VOUT_S (not read) | `5VOUT_S` | **OK** | reaches R15,R16 | board/boards/red.h:92 |
| PB14 | 74 | out | USB load switch (obsolete, OD pull-up) | `USB_LOAD` | **OK** | reaches Q3 | board/boards/red.h:96-98 |
| PC4 | 47 | adc | SBU1 | `SBU1_ADC` | **OK** | reaches D13,R28 | board/boards/red.h:110 |
| PA1 | 38 | adc | SBU2 | `SBU2_ADC` | **OK** | reaches D14,R29 | board/boards/red.h:111 |
| PC10 | 109 | relay | relay_SBU1 | `relay_SBU1` | **OK** | reaches Q2 | board/boards/red.h:106 |
| PC11 | 110 | relay | relay_SBU2 | `relay_SBU2` | **OK** | reaches Q1 | board/boards/red.h:108 |
| PE4 | 3 | led | LED_RED | `LED_RED` | **OK** | reaches R19 | board/boards/red.h:124-125 |
| PE3 | 2 | led | LED_GREEN | `LED_GREEN` | **OK** | reaches R18 | board/boards/red.h:124-125 |
| PE2 | 1 | led | LED_BLUE | `LED_BLUE` | **OK** | reaches R17 | board/boards/red.h:124-125 |
| PF7 | 21 | hwtype |  | `GND` | **OK** | net=GND; expect=low | board/stm32h7/board.h:25 (id1 bit0, RED needs 0) |
| PF8 | 22 | hwtype |  | `GND` | **OK** | net=GND; expect=low | board/stm32h7/board.h:26 |
| PF9 | 23 | hwtype |  | `Net-(JP1-B)` | **OK** | net=Net-(JP1-B); expect=float_or_low | board/stm32h7/board.h:27 (PCR-1: strap via JP1 - fechado = RED id1=0, aberto = HYBRID id1=4; ver 03_RESEARCH/HYBRID_FW_PORT.md) |
| PF10 | 24 | hwtype |  | `GND` | **OK** | net=GND; expect=low | board/stm32h7/board.h:28 |
| PD4 | 116 | hwtype |  | `unconnected-(U7-PD4-Pad116)` | **OK** | floating; expect=float_or_high | board/stm32h7/board.h:30 (id2 must not be 3) |
| PD5 | 117 | hwtype |  | `unconnected-(U7-PD5-Pad117)` | **OK** | floating; expect=float_or_high | board/stm32h7/board.h:31 |
| PD6 | 120 | hwtype |  | `unconnected-(U7-PD6-Pad120)` | **OK** | floating; expect=float_or_high | board/stm32h7/board.h:32 |
| PH0 | 25 | hse |  | `HSE_IN` | **OK** | reaches C23,Y1 | board/stm32h7/clock.h:66 (HSE 25 MHz) |
| PH1 | 26 | hse |  | `HSE_OUT` | **OK** | reaches C24,Y1 | board/stm32h7/clock.h:66 |
| BOOT0 | 135 | boot0 |  | `BOOT0` | **OK** | reaches R14,SW1 | DS13311 pin 135; firmware enters DFU by software, BOOT0 must be low at reset |
| PA13 | 102 | swd | SWDIO | `SWDIO` | **OK** | reaches J1 | early_gpio_float keeps AF (stm32h7_config.h:95) |
| PA14 | 107 | swd | SWCLK | `SWCLK` | **OK** | reaches J1 | idem |

## Pinos do MCU ligados no hardware mas sem função no firmware (SEM_USO no firmware)

| Pino | Pad | Net | Componentes |
|---|---|---|---|
| VLXSMPS_15 | 15 | `VLXSMPS` | C41, L5 |
| VFBSMPS_17 | 17 | `VCAP` | C39, C40, C42, C64, L5 |

## Pinos de alimentação do MCU

| Pino | Pad | Net |
|---|---|---|
| VSS | 6 | `GND` |
| VDD | 7 | `+3V3` |
| VBAT | 8 | `+3V3` |
| VSS | 12 | `GND` |
| VDD | 13 | `+3V3` |
| VSSSMPS | 14 | `GND` |
| VDDSMPS | 16 | `+3V3` |
| VSS | 18 | `GND` |
| VDD | 19 | `+3V3` |
| NRST | 27 | `NRST` |
| VDD | 32 | `+3V3` |
| VSS | 33 | `GND` |
| VSSA | 34 | `GND` |
| VREF+ | 35 | `VDDA` |
| VDDA | 36 | `VDDA` |
| VSS | 41 | `GND` |
| VDD | 42 | `+3V3` |
| VSS | 55 | `GND` |
| VDD | 56 | `+3V3` |
| VCAP | 68 | `VCAP` |
| VSS | 69 | `GND` |
| VDDLDO | 70 | `+3V3` |
| VDD | 71 | `+3V3` |
| VDD | 79 | `+3V3` |
| VSS | 80 | `GND` |
| VSS | 89 | `GND` |
| VDD50USB | 90 | `+3V3` |
| VDD33USB | 91 | `+3V3` |
| VDD | 92 | `+3V3` |
| VCAP | 103 | `VCAP` |
| VSS | 104 | `GND` |
| VDDLDO | 105 | `+3V3` |
| VDD | 106 | `+3V3` |
| VSS | 118 | `GND` |
| VDD | 119 | `+3V3` |
| VSS | 128 | `GND` |
| VDD | 129 | `+3V3` |
| VCAP | 140 | `VCAP` |
| VSS | 141 | `GND` |
| PDR_ON | 142 | `+3V3` |
| VDDLDO | 143 | `+3V3` |
| VDD | 144 | `+3V3` |
