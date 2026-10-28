# P3 / P4 / P5 / P6 — Mapa de pinos, identificação, clock e boot exigidos pelo firmware (lado firmware)

Data: 2026-10-22. Fonte primária: clone somente leitura `hardware/reference/panda` (github.com/commaai/panda, **commit `408e14d46ebb7da45a7d21f8db315922e10242a8`**, 2026-10-21). Licença MIT (`hardware/reference/panda/LICENSE`).
Todas as linhas abaixo são FATO (código lido), salvo indicação INFERÊNCIA / NÃO VERIFICADO.
Os nomes de arquivo candidatos no prompt (`llcan.h`, `clock_init`, `detect_configuration()`) **não existem**; os reais são `board/stm32h7/llfdcan.h`, `board/stm32h7/clock.h` (`clock_init()`), `board/stm32h7/board.h` (`detect_board_type()`), `board/boards/red.h`, `board/stm32h7/peripherals.h` (`common_init_gpio()`), `board/early_init.h`.

## P3 — Mapa de GPIO exigido para `board_red` (HW_TYPE_RED_PANDA)

| Função | Porta/pino H7 | AF / modo | Arquivo:linha | Observação |
|---|---|---|---|---|
| USB OTG_FS D− / D+ | PA11 / PA12 | AF10 OTG1_FS | `stm32h7/peripherals.h:9-10` | PHY interno FS |
| VOLT_S (tensão 12 V) | **PF11** | analógico, `ADC1` canal 2 ×11 | `peripherals.h:25-26`, `boards/red.h:71` | canal INP2 ↔ PF11: ver pesquisa ST (P3-ST) |
| FDCAN1 RX / TX (bus 0) | PB8 / PB9 | AF9 FDCAN1 | `peripherals.h:31-35` | |
| FDCAN2 RX / TX (bus 1, modo normal) | PB12 / PB13 | AF9 FDCAN2 | `red.h:57-61` | comutado em tempo de execução |
| FDCAN2 RX / TX (OBD, `CAN_MODE_OBD_CAN2`) | PB5 / PB6 | AF9 FDCAN2 | `peripherals.h:41-45`, `red.h:43-47` | par alternativo do mesmo FDCAN2 |
| FDCAN3 RX / TX (bus 2) | **PG9 / PG10** | **AF2 FDCAN3** | `peripherals.h:48-52` | ≠ PD12/PD13 (usado no v1 — descartado) |
| STB transceiver 1 (bus 0) | **PG11** | saída, 1 = standby | `red.h:12,78-79` | |
| STB transceiver 2 (OBD) | PB3 | saída | `red.h:15,81-82` | |
| STB transceiver 3 (bus 2) | PD7 | saída | `red.h:18,84-85` | também lido como strap id2 bit3 |
| STB transceiver 4 (bus 1) | PB4 | saída | `red.h:21,87-88` | |
| 5VOUT_S | PB1 | analógico | `red.h:91-92` | nenhum canal ADC lido em `red.h` (apenas configurado) |
| USB load switch EN | PB14 | saída open-drain, pull-up interno, nível 1 | `red.h:95-98` | comentário: "obsolete for red panda" |
| SBU1 (harness) | PC4 | ADC1 canal 4 | `red.h:102,106,110` | |
| SBU2 (harness) | **PA1** | ADC1 canal 17 | `red.h:103,107,111` | |
| Relé SBU1 / SBU2 | PC10 / PC11 | saída (ativo baixo, `drivers/harness.h:23-27`) | `red.h:104-105,108-109` | |
| LED R / G / B | PE4 / PE3 / PE2 | saída open-drain (ou AF2 TIM3 p/ PWM) | `red.h:123-124`, `drivers/led.h:22-29` | ânodo comum em +3V3 (INFERÊNCIA pelo open-drain) |
| Strap id1 (HW_TYPE) | PF7, PF8, PF9, PF10 | entrada com pull-up interno; red exige leitura **0 em todos** | `stm32h7/board.h:25-28,38` | ver P4 |
| Strap id2 | PD4, PD5, PD6, PD7 | entrada com pull-up; red exige id2 ≠ 3 | `board.h:30-36` | ver P4 |
| SPI4 (apenas tres/cuatro, `has_spi=false` no red) | PE11–PE14 | AF5 | `peripherals.h:15-18` | não usado no red |
| SWD | PA13 / PA14 | padrão de reset | — | não configurado pelo firmware (INFERÊNCIA: mantido) |
| HSE | PH0 / PH1 | OSC_IN/OSC_OUT | `clock.h:4,78-80` | ver P5 |
| BOOT0 | BOOT0 | — | — | ver P6 |

Não existem em `red.h`: fan, IR, siren, SOM GPIO, bootkick, amp (`unused_*`, `red.h:117-130`).

### Tabela (a): periférico × pino no F413 (projeto original) × pino exigido pelo firmware H7 × rede × observações

Fonte do lado F413: `archive/baseline-original/BlackPanda/kicad_project/BlackPanda.kicad_sch` (netlist extraída, ver `hardware/research/from-v1/original-mcu-pinout.txt`).

| Função | F413 (original) | H7 exigido (red) | Rede proposta v2 | Observação |
|---|---|---|---|---|
| USB D−/D+ | PA11/PA12 | PA11/PA12 | USB_DM/USB_DP | igual |
| bus 0 RX/TX | PA8/PA15 (CAN3 F4) | PB8/PB9 (FDCAN1) | CAN0_RX/TX | mudança de controlador: no F4 o bus0 era CAN3; no H7 é FDCAN1 |
| bus 1 RX/TX | PB12/PB13 (CAN2) | PB12/PB13 (FDCAN2) | CAN1_RX/TX | igual |
| bus 2 RX/TX | PB8/PB9 (CAN1) | **PG9/PG10 (FDCAN3)** | CAN2_RX/TX | novo |
| OBD RX/TX | PB5/PB6 (CAN2 alt) | PB5/PB6 (FDCAN2 alt) | OBD_RX/TX | igual |
| STB bus0 / OBD / bus2 / bus1 | PC1 / PC13 / PA0 / PB10 | **PG11 / PB3 / PD7 / PB4** | *_STB | todos diferentes |
| VOLT_S | PC2 | **PF11** | VOLT_S | |
| SBU1 / SBU2 | PC0 / PC3 | PC4 / **PA1** | SBU1/SBU2 | |
| Relés SBU1/SBU2 | PC10/PC11 | PC10/PC11 | RELAY_SBU1/2 | igual |
| USB_LOAD | PB1 | PB14 | USB_LOAD_EN | |
| 5VOUT_S | — (não existia) | PB1 | 5VOUT_S | opcional: configurado, não lido |
| LEDs | (SMP4-RGB em outros pinos) | PE4/PE3/PE2 | LED_R/G/B | |
| GPS (UART/RESET/BOOT/TIMEPULSE/LOAD) | PA9/PA10/PC14/PC5/PB0/PC12 | — | removido | red não tem GPS; ANT1/U.FL removidos |
| UART debug | PA2/PA3 | — | removido | não usado pelo red |
| SPI | PA4–PA7 | — | — | `has_spi=false` |
| Straps id1/id2 | — | PF7–PF10 = 0; PD4–PD6 livres | ID straps | novo |

## P4 — Identificação da placa (HW_TYPE)

Mecanismo (`board/stm32h7/board.h:23-51`, `drivers/gpio.h detect_with_pull()`): cada pino é configurado como **entrada com pull-up interno**, aguarda-se `PULL_EFFECTIVE_DELAY`, lê-se o nível, e o pull-up é removido. Não há ADC nem divisor.

| id | Pinos (bit0..bit3) | Assinatura | Resultado |
|---|---|---|---|
| id2 | PD4, PD5, PD6, PD7 | == 3 (PD4=0, PD5=0, PD6=1, PD7=1) | HW_TYPE_CUATRO |
| id1 | PF7, PF8, PF9, PF10 | == 0 (todos **puxados a GND externamente**) | **HW_TYPE_RED_PANDA (7)** → `board_red` |
| id1 | | == 1 | RED_PANDA_V2 (depreciado → UNKNOWN) |
| id1 | | == 2 | HW_TYPE_TRES |
| outro | | | HW_TYPE_UNKNOWN |

Ordem: id2 é testado antes de id1 (`board.h:35`). Para ser reconhecida como red, a placa deve ter: **PF7, PF8, PF9, PF10 em nível baixo com pull-up interno ativo** e **id2 ≠ 3**.
- Valor do resistor de pull-down externo no Red Panda real: **NÃO VERIFICADO** (hardware fechado). INFERÊNCIA segura: ligação direta a GND ou pull-down ≤ 1 kΩ, pois os pinos só são usados como entrada (nunca saída) e o pull-up interno típico é ~40 kΩ (valor do datasheet: ver P3-ST, NÃO VERIFICADO aqui). Decisão de projeto proposta: resistores 0 Ω/1 kΩ a GND (montados) para permitir alteração futura.
- id2: PD4–PD6 não usados no red; deixá-los **sem conexão** (leem 1 com pull-up) e PD7 é STB3 (lê 1 se o transceiver tiver pull-up interno no STB — TCAN1044V: NÃO VERIFICADO aqui; mesmo se ler 0, id2 ∈ {7, 15} ≠ 3). **Evitar** qualquer pull-down em PD4/PD5 combinado com PD6/PD7 altos.

Falha de detecção (`main.c:306`, `libc.h assert_fatal`): `hw_type == UNKNOWN` → imprime "ASSERT FAILED / Unsupported board type" e **trava em `while(1)`**. Não é Hard Fault; a afirmação do prompt é **REFUTADA** (é um hang deliberado, comportamento seguro: nenhum CAN inicializado). No bootstub (`bootstub.c:43`) `detect_board_type()` também é chamado antes de qualquer flash.

## P5 — Clock

- **HSE externo de 25 MHz é obrigatório** (`clock.h:4` "HSE: 25MHz"; `clock.h:78-80` liga HSEON e espera HSERDY sem timeout; sem HSE o firmware trava aqui). Sem bypass (HSEBYP não é setado) → **cristal**, não oscilador.
- PLL1: DIVM=5, N=48, P=1 → 240 MHz núcleo; Q=3 → 80 MHz para FDCAN (`clock.h:84-88`, `stm32h7_config.h CORE_FREQ 240`). ADC usa per_ck = HSE (`clock.h:116`). CSS do HSE habilitado (`clock.h:119`).
- Capacitores de carga, gm, drive level: lado ST (DS13313/AN2867) — ver `P2_P5_P6_P7_ST_datasheet.md` (pesquisa online).
- LSI 32 kHz interno usado para o watchdog/monitor (`clock.h:124`); sem LSE/cristal de 32 kHz.

## P6 — Boot / DFU

- `BOOTLOADER_ADDRESS 0x1FF09804` (`stm32h7/stm32h7_config.h:14`): endereço do vetor de reset do bootloader de sistema ST para H72x/73x — confirmação em AN2606: ver pesquisa ST (NÃO VERIFICADO aqui).
- Entrada em DFU **por software**: o host envia um comando USB (`main_comms.h:184`) que grava `enter_bootloader_mode = ENTER_BOOTLOADER_MAGIC` e reinicia; em `early_init.h:60-64`, antes de `main`, o firmware acende o LED verde e salta para `BOOTLOADER_ADDRESS` (`jump_to_bootloader()`). Também salta se `DBGMCU->IDCODE != 0x483` (`early_init.h:46-50`) — proteção contra MCU errado.
- "Softloader" (`ENTER_SOFTLOADER_MAGIC`): bootstub próprio da comma via USB (`bootstub.c:46`, `flasher.h`), com verificação RSA da aplicação (`bootstub.c:52-72`).
- **Pino BOOT0 físico**: não há código que dependa dele, mas é o único caminho de recuperação quando o bootstub está vazio/corrompido (placa nova). O prompt pergunta por BOOT1: o STM32H7 **não tem BOOT1**; o boot alternativo é por option bytes BOOT_ADD0/1 — confirmar no RM0468 (pesquisa ST, NÃO VERIFICADO aqui). Resistor de pull-down de BOOT0 e botão: valor conforme AN5419 (pesquisa ST); o original usa 10 kΩ + botão para +3V3 (`original_copy` SW1/R14 — FATO do projeto original, não da ST).
- Primeira gravação: via DFU de sistema (BOOT0 = 1 no reset) ou SWD (`PA13/PA14`); upstream usa `python -m panda.flash` / `dfu-util` (scripts em `hardware/reference/panda/scripts` — não lidos em detalhe).

## Conflitos de paridade 1:1 (Diretriz 2) — decisão: STM32H723 TFBGA100

Pinos exigidos que **não existem em LQFP100**: PG9, PG10, PG11, PF7, PF8, PF9, PF10, PF11 (portas F e G ausentes no LQFP100 — R3 v1, confirmação DS13313 na pesquisa ST). Em **TFBGA100** a disponibilidade de cada um está sendo verificada (`P2_P5_P6_P7_ST_datasheet.md`, Q3). Se algum faltar, o projeto PARA e reporta.
