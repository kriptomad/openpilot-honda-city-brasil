# Coverage matrix — HRS vs. fontes oficiais commaai

Gerado por `05_SCRIPTS/coverage_matrix.py`. Requisitos: 61, provados: 61, não encontrados: 0.

HEADs: panda=408e14d46ebb, hardware=a42a4752dc58, opendbc=c3955753ae72, panda_legacy_f4=f849893bdcfc, openpilot=ff47f484e606, datasheets=-

| ID | Requisito | Status | Evidência (repo/arquivo:linha) | Texto |
|---|---|---|---|---|
| HRS-01 | HW_TYPE_RED_PANDA == 7 | FOUND | `panda/board/boards/board_declarations.h:50` | `#define HW_TYPE_RED_PANDA 7U` |
| HRS-02 | id1 = PF7..PF10 read with internal pull-up | FOUND | `panda/board/stm32h7/board.h:25` | `const uint8_t id1 = detect_with_pull(GPIOF, 7, PULL_UP) \|` |
| HRS-03 | id1 == 0 -> RED | FOUND | `panda/board/stm32h7/board.h:38` | `} else if (id1 == 0U) {` |
| HRS-04 | id2 = PD4..PD7 (3 -> CUATRO) | FOUND | `panda/board/stm32h7/board.h:30` | `const uint8_t id2 = detect_with_pull(GPIOD, 4, PULL_UP) \|` |
| HRS-05 | detect_with_pull delay 4096 loops | FOUND | `panda/board/drivers/gpio.h:77` | `#define PULL_EFFECTIVE_DELAY 4096` |
| HRS-06 | host lib: HW_TYPE_RED_PANDA = 0x07, red is external (not INTERNAL_DEVICES) | FOUND | `panda/python/__init__.py:133` | `HW_TYPE_RED_PANDA = b'\x07'` |
| HRS-10 | build defines -DSTM32H725xx, cortex-m7, fpv5-d16 | FOUND | `panda/SConscript:139` | `"-DSTM32H725xx",` |
| HRS-11 | MCU_IDCODE 0x483 (reboot to bootloader if mismatch) | FOUND | `panda/board/stm32h7/stm32h7_config.h:5` | `#define MCU_IDCODE 0x483U` |
| HRS-12 | HSE 25 MHz crystal | FOUND | `panda/board/stm32h7/clock.h:4` | `HSE: 25MHz` |
| HRS-13 | PLL1: 240 MHz core, 80 MHz FDCAN (PLL1Q) | FOUND | `panda/board/stm32h7/clock.h:7` | `CPU: 240MHz` |
| HRS-14 | LQFP144 -> SMPS only (PWR_CR3_SMPSEN); TFBGA100 -> LDO; else hang | FOUND | `panda/board/stm32h7/clock.h:66` | `register_set(&(PWR->CR3), PWR_CR3_SMPSEN, 0xFU); // powered only by SMPS` |
| HRS-15 | USB clock from HSI48 | FOUND | `panda/board/stm32h7/clock.h:6` | `HSI48 enabled (for USB)` |
| HRS-16 | VOS1 for 80 MHz CAN FD | FOUND | `panda/board/stm32h7/clock.h:71` | `// Set VOS level (VOS3 to 170Mhz, VOS2 to 300Mhz, VOS1 to 400Mhz, VOS0 to 550Mhz)` |
| HRS-17 | VDD33USB voltage detector enabled | FOUND | `panda/board/stm32h7/clock.h:121` | `register_set_bits(&(PWR->CR3), PWR_CR3_USB33DEN);` |
| HRS-20 | FLASH 1024K, app at 0x08020000 | FOUND | `panda/board/stm32h7/stm32h7x5_flash.ld:71` | `_app_start = 0x08020000; /* Reserve Sector 0(128K) for bootloader */` |
| HRS-21 | provisioning at end of 1 MB flash (0x080FFFC0/E0) -> requires 'G' variant | FOUND | `panda/board/stm32h7/stm32h7_config.h:45` | `#define PROVISION_CHUNK_ADDRESS 0x080FFFE0U` |
| HRS-22 | ST bootloader address 0x1FF09804 | FOUND | `panda/board/stm32h7/stm32h7_config.h:14` | `#define BOOTLOADER_ADDRESS 0x1FF09804U` |
| HRS-23 | bootstub RSA signature check (release key; debug only with ALLOW_DEBUG) | FOUND | `panda/board/bootstub.c:72` | `#ifdef ALLOW_DEBUG` |
| HRS-24 | DFU flash flow (dfu-util 0483:df11) | FOUND | `panda/board/debug/dfu_util_h7.sh:10` | `$DFU_UTIL -d 0483:df11 -a 0 -s 0x08020000 -D obj/panda_h7.bin.signed` |
| HRS-25 | FDCAN message RAM base 0x4000AC00 | FOUND | `panda/board/stm32h7/llfdcan_declarations.h:16` | `#define FDCAN_START_ADDRESS 0x4000AC00UL` |
| HRS-30 | USB VID 0x3801 / PID 0xDDCC | FOUND | `panda/board/config.h:16` | `#define USB_PID 0xDDCCU` |
| HRS-31 | USB PA11/PA12 AF10 | FOUND | `panda/board/stm32h7/peripherals.h:9` | `set_gpio_alternate(GPIOA, 11, GPIO_AF10_OTG1_FS);` |
| HRS-32 | internal FS PHY, VBUS sensing disabled | FOUND | `panda/board/stm32h7/llusb.h:41` | `USBx->GOTGCTL \|= USB_OTG_GOTGCTL_BVALOEN;` |
| HRS-40 | STB xcvr1 (bus0) PG11 | FOUND | `panda/board/boards/red.h:12` | `set_gpio_output(GPIOG, 11, !enabled);` |
| HRS-41 | STB xcvr2 PB3 (FDCAN2 via PB5/PB6, OBD) | FOUND | `panda/board/boards/red.h:15` | `set_gpio_output(GPIOB, 3, !enabled);` |
| HRS-42 | STB xcvr3 (bus2) PD7 | FOUND | `panda/board/boards/red.h:18` | `set_gpio_output(GPIOD, 7, !enabled);` |
| HRS-43 | STB xcvr4 PB4 (FDCAN2 via PB12/PB13) | FOUND | `panda/board/boards/red.h:21` | `set_gpio_output(GPIOB, 4, !enabled);` |
| HRS-44 | FDCAN2 on PB5/PB6 AF9 (OBD mode) | FOUND | `panda/board/boards/red.h:44` | `set_gpio_alternate(GPIOB, 5, GPIO_AF9_FDCAN2);` |
| HRS-45 | FDCAN2 on PB12/PB13 AF9 (normal mode) | FOUND | `panda/board/boards/red.h:58` | `set_gpio_alternate(GPIOB, 12, GPIO_AF9_FDCAN2);` |
| HRS-46 | FDCAN1 PB8/PB9 AF9 | FOUND | `panda/board/stm32h7/peripherals.h:32` | `set_gpio_alternate(GPIOB, 8, GPIO_AF9_FDCAN1);` |
| HRS-47 | FDCAN3 PG9/PG10 AF2 | FOUND | `panda/board/stm32h7/peripherals.h:49` | `set_gpio_alternate(GPIOG, 9, GPIO_AF2_FDCAN3);` |
| HRS-48 | VOLT_S = ADC1 ch2 (PF11) x11 | FOUND | `panda/board/boards/red.h:71` | `return adc_get_mV(&(const adc_signal_t) ADC_CHANNEL_DEFAULT(ADC1, 2)) * 11U;` |
| HRS-49 | PF11 analog mode | FOUND | `panda/board/stm32h7/peripherals.h:26` | `set_gpio_mode(GPIOF, 11, MODE_ANALOG);` |
| HRS-50 | 5VOUT_S on PB1 analog | FOUND | `panda/board/boards/red.h:92` | `set_gpio_mode(GPIOB, 1, MODE_ANALOG);` |
| HRS-51 | USB load switch PB14 open-drain, pull-up, obsolete | FOUND | `panda/board/boards/red.h:95` | `set_gpio_output_type(GPIOB, 14, OUTPUT_TYPE_OPEN_DRAIN);` |
| HRS-52 | SBU1 PC4 ADC ch4; SBU2 PA1 ADC ch17 | FOUND | `panda/board/boards/red.h:106` | `.pin_SBU1 = 4,` |
| HRS-53 | relay SBU1 PC10 / SBU2 PC11 | FOUND | `panda/board/boards/red.h:108` | `.pin_relay_SBU1 = 10,` |
| HRS-54 | LEDs PE4 red / PE3 green / PE2 blue | FOUND | `panda/board/boards/red.h:123` | `.led_GPIO = {GPIOE, GPIOE, GPIOE},` |
| HRS-55 | LED open-drain active-low | FOUND | `panda/board/drivers/led.h:23` | `set_gpio_output_type(current_board->led_GPIO[i], current_board->led_pin[i], OUTPUT_TYPE_OPEN_DRAIN);` |
| HRS-56 | avdd 3300 mV | FOUND | `panda/board/boards/red.h:119` | `.avdd_mV = 3300U,` |
| HRS-57 | has_spi false (SPI4 PE11-14 unused) | FOUND | `panda/board/boards/red.h:117` | `.has_spi = false,` |
| HRS-58 | has_fan false | FOUND | `panda/board/boards/red.h:118` | `.has_fan = false,` |
| HRS-60 | orientation threshold avdd/2 | FOUND | `panda/board/drivers/harness.h:66` | `uint16_t detection_threshold = current_board->avdd_mV / 2U;` |
| HRS-61 | SBU pins not 5V tolerant in ADC mode -> back to MODE_INPUT | FOUND | `panda/board/drivers/harness.h:82` | `// Pins are not 5V tolerant in ADC mode` |
| HRS-62 | relay pins open-drain, idle high | FOUND | `panda/board/drivers/harness.h:98` | `set_gpio_output_type(current_board->harness_config->GPIO_relay_SBU1, current_board->harness_config->pin_relay_SBU1, OUTPUT_TYPE_OPEN_DRAIN);` |
| HRS-63 | ignition = !digital_input(SBU ign side) | FOUND | `panda/board/drivers/harness.h:43` | `ret = !get_gpio_input(current_board->harness_config->GPIO_SBU1, current_board->harness_config->pin_SBU1);` |
| HRS-64 | bus0<->bus2 swap when harness flipped | FOUND | `panda/board/drivers/can_common.h:131` | `bus_config[0].bus_lookup = flipped ? 2U : 0U;` |
| HRS-65 | early GPIO float (all inputs at reset) | FOUND | `panda/board/stm32h7/stm32h7_config.h:95` | `GPIOA->MODER = 0xAB000000U; GPIOB->MODER = 0; GPIOC->MODER = 0; GPIOD->MODER = 0; GPIOE->MODER = 0; GPIOF->MODER = 0; GPIOG->MODER = 0; GPIO` |
| HRS-66 | under-voltage threshold 6000 mV | FOUND | `panda/board/main.c:130` | `if ((controls_allowed_countdown > 0U) && (heartbeat_tick_counter > 2U) && (current_board->read_voltage_mV() < 6000U)) {` |
| HW-01 | red panda MCU STM32H725 (README) | FOUND | `hardware/panda/README.md:31` | `<td>STM32H725</td>` |
| HW-02 | OBD-C pinout (SBU1 ~100 Ohm, SBU2 1k ign) | FILE_PRESENT | `hardware/harness/OBD-C.sch.pdf` | `sha256 3450700E3711643C` |
| HW-03 | harness box v3 schematic (termination 120 R, DG419 relay) | FILE_PRESENT | `hardware/harness/v3/Harness_Box.pdf` | `sha256 36DC9E55FF193A98` |
| HW-04 | Honda Bosch B harness drawing | FILE_PRESENT | `hardware/harness/v3/Honda_Bosch_B_Harness.pdf` | `sha256 4E5F271483ABA0D8` |
| HW-05 | no red panda schematic/PCB published | FOUND | `hardware/panda/ (11 files, 1 schematic/pcb/pdf)` | `` |
| VEH-01 | Honda City 2023 BR = HondaBoschPlatformConfig BOSCH_RADARLESS | FOUND | `opendbc/opendbc/car/honda/values.py:248` | `HONDA_CITY_7G = HondaBoschPlatformConfig(` |
| F4-01 | black panda STB PC1/PC13/PA0/PB10 | FOUND | `panda_legacy_f4/board/boards/black.h:12` | `set_gpio_output(GPIOC, 1, !enabled);` |
| F4-02 | black panda CAN3 PA8/PA15 AF11 | FOUND | `panda_legacy_f4/board/boards/black.h:75` | `set_gpio_alternate(GPIOA, 8, GPIO_AF11_CAN3);` |
| F4-03 | black panda LEDs PC9/PC7/PC6 | FOUND | `panda_legacy_f4/board/boards/black.h:120` | `.led_pin = {9, 7, 6},` |
| OP-01 | openpilot pins panda submodule | FOUND | `openpilot/.gitmodules:2` | `path = panda` |
| OP-02 | pandad talks to red panda via USB (python lib) | FOUND | `openpilot/openpilot/selfdrive/pandad/pandad.py:21` | `with Panda(cli=False) as p:` |
| OP-03 | datasheet DS13311 pin table present | FOUND | `datasheets/DS13313_text.txt:5528` | `- - - 122 - C8 A8 153 PG9 I/O FT_h -` |
