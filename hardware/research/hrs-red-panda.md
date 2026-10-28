# HRS — Especificação de Hardware derivada do firmware (Red Panda) + controle Black Panda

Fonte primária: clone oficial `02_REFERENCE\panda` = github.com/commaai/panda @ **408e14d46ebb7da45a7d21f8db315922e10242a8** (2026-10-21, MIT).
Firmware legado F4 (controle): `02_REFERENCE\panda_legacy_f4` = worktree de `panda_full` em **f849893bdcfc6cd05d4547d64d2802b5a83f409c** (2025-07-03; último commit antes de "Deprecate white and black pandas (#2227)" = 3d272335, 2025-07-19; `stm32f4/` removido em 1ce986f7 "bye bye f4 (#2259)", 2025-08-26).
Datasheet: `02_REFERENCE\datasheets\DS13313_STM32H725_ae.pdf` (= DS13311 Rev 5, STM32H725xE/G). Referência de registradores: RM0468 (citado em panda/README.md:3; **não baixado** — itens de registrador marcados como "RM0468 NÃO VERIFICADO" onde o CMSIS `stm32h725xx.h` não basta).
Legenda: **[F]** fato com fonte · **[I]** inferência · **[H]** hipótese · **NV** = NÃO VERIFICADO.

---
## 1. Tipos de placa e HW_TYPE

| Item | Valor | Fonte |
|---|---|---|
| Enum | `HW_TYPE_UNKNOWN 0`, `HW_TYPE_RED_PANDA 7`, `HW_TYPE_TRES 9`, `HW_TYPE_CUATRO 10` | board/boards/board_declarations.h:48-51 |
| Host | `HW_TYPE_RED_PANDA = b'\x07'`; `H7_DEVICES = [RED, TRES, CUATRO, BODY]`; `INTERNAL_DEVICES = (TRES, CUATRO)` → red = externo | python/__init__.py:133,154,157 |
| Detecção | `id1 = PF7 | PF8<<1 | PF9<<2 | PF10<<3` lidos com **pull-up interno** (`detect_with_pull(..., PULL_UP)`); `id2 = PD4 | PD5<<1 | PD6<<2 | PD7<<3` pull-up | board/stm32h7/board.h:25-34 |
| Ordem | `id2 == 3` → CUATRO; `id1 == 0` → **RED**; `id1 == 1` → UNKNOWN (red v2 depreciada); `id1 == 2` → TRES; senão UNKNOWN | board/stm32h7/board.h:36-50 |
| Mecanismo | `detect_with_pull`: MODE_INPUT, pull, espera `PULL_EFFECTIVE_DELAY 4096` iterações, lê IDR, remove pull | board/drivers/gpio.h:77-91 |
| Falha | `hw_type = UNKNOWN; print(...)`; `current_board` fica indefinido/não atribuído → comportamento inseguro; bootstub chama `detect_board_type()` antes de validar app (bootstub.c:41) | board/stm32h7/board.h:48-50 |

**Requisito de hardware HW_TYPE (Red):** PF7, PF8, PF9, PF10 devem ler **0** contra pull-up interno → ligados a GND (direto ou resistor baixo). PD4, PD5, PD6 **não** podem formar `id2 == 3` (PD4=1, PD5=1, PD6=0, PD7=0): como PD7 é saída STB (bus2) e PD4–PD6 não são usados no red, deixá-los **flutuando** (pull-up interno lê 1 → id2 = 0b0111 ou 0b1111 ≠ 3) é o que o firmware tolera; para robustez, PD6 pode ser amarrado... **[I]** a referência real não é publicada (ver P2) → valor de resistor **NV**; decisão conservadora: PF7–PF10 → GND via 0 Ω/direto; PD4–PD6 sem conexão (NC) **[D-08]**.
Pull-up interno típico H7: RPU 30–50 kΩ (DS13311 Tabela "I/O static characteristics" — valor exato **NV** neste dump).

Pinos LQFP144 (DS13311 Tab. 8 via `P3_pinos_LQFP144.json`): PF7=21, PF8=22, PF9=23, PF10=24, PD4=116, PD5=117, PD6=120, PD7=121.

## 2. MCU, defines, clock

| Item | Valor | Fonte |
|---|---|---|
| Build | `-mcpu=cortex-m7 -mhard-float -mfpu=fpv5-d16 -DSTM32H7 -DSTM32H725xx`, `APP_START_ADDRESS 0x8020000`, linker `stm32h7x5_flash.ld`, startup `startup_stm32h7x5xx.s` | SConscript:135-146 |
| IDCODE | `MCU_IDCODE 0x483` (checado em early_init; se diferente → entra bootloader) | stm32h7_config.h:4; early_init.h:47-50 |
| Variantes aceitas pelo header | STM32H725xx cobre AGI6, IGK6, IGT6, RGV6, VGT6, VGY6, **ZGT6**, REV6, VET6, **ZET6**, AEI6, IET6, IEK6 | board/stm32h7/inc/stm32h7xx.h:82 |
| HSE | **25 MHz** externo, `RCC_CR_HSEON`, CSS ligado | clock.h:3,66-67,115 |
| PLL1 | HSE/5 → ×48 → P/1 = **240 MHz** sysclk; Q/3 = **80 MHz** (FDCAN); R/2 | clock.h:72-85 |
| USB clock | HSI48 (`USBSEL = 0b11`) → nenhum cristal externo necessário para USB | clock.h:69,104 |
| FDCAN clock | PLL1Q 80 MHz (`FDCANSEL_0`) | clock.h:106 |
| ADC clock | per_ck = HSE | clock.h:110 |
| LSI | ligado para `clock_check` via TIM16 (sem LSE/cristal 32 kHz) | clock.h:122 |
| VOS | VOS1 (`PWR_D3CR_VOS_1|VOS_0`) "needed for 80 MHz CAN FD" | clock.h:60 |
| Regulador | `SYSCFG->PKGR`: TFBGA100 → `LDOEN`; **LQFP144 / UFBGA169 → `SMPSEN` ("powered only by SMPS")**; outro → `while(true)`. PWR->CR3 byte baixo write-once (só POR limpa) | clock.h:30-58 |
| VDD33USB detector | `PWR_CR3_USB33DEN` ligado | clock.h:117 |

→ **Requisito:** cristal 25 MHz em PH0/PH1 (LQFP144 pinos 25/26); core alimentado pelo **SMPS interno (Direct SMPS)**; VDD33USB alimentado com 3,3 V (pino 91) e VDD50USB (pino 90) conforme DS §3.7.

## 3. GPIOs inicializados (Red)

| Pino | LQFP144 | Modo | AF | Pull | Finalidade | Fonte |
|---|---|---|---|---|---|---|
| PA11 | 100 | AF | AF10 OTG1_FS (DM) | — | USB D− (OSPEEDR alto) | peripherals.h:8-10 |
| PA12 | 101 | AF | AF10 OTG1_FS (DP) | — | USB D+ | peripherals.h:8-10 |
| PF11 | 52 | ANALOG | — | none | VOLT_S (ADC1 INP2) | peripherals.h:25-27; red.h:69 |
| PB8 | 136 | AF | AF9 FDCAN1 RX | none | CAN bus0 RX (CAN1) | peripherals.h:31-36 |
| PB9 | 137 | AF | AF9 FDCAN1 TX | none | CAN bus0 TX | idem |
| PB12 | 72 | AF/ANALOG | AF9 FDCAN2 RX | none | FDCAN2 "OBD" (transceiver 4; usado quando mode==OBD_CAN2 XOR flipped) | red.h:53-58; peripherals.h:39-40 |
| PB13 | 73 | AF/ANALOG | AF9 FDCAN2 TX | none | idem | idem |
| PB5 | 132 | AF/ANALOG | AF9 FDCAN2 RX | none | FDCAN2 "normal" (transceiver 2; mode==NORMAL e não flipped) | red.h:36-42 |
| PB6 | 133 | AF/ANALOG | AF9 FDCAN2 TX | none | idem | idem |
| PG9 | 122 | AF | AF2 FDCAN3 (**TX** per DS Tab.8) | none | CAN bus2 | peripherals.h:46-51 |
| PG10 | 123 | AF | AF2 FDCAN3 (**RX** per DS) | none | CAN bus2 | idem |
| PG11 | 124 | OUT PP | — | none | STB transceiver 1 (bus0); `set_gpio_output(!enabled)` → **1 = standby** | red.h:9-12,75-77 |
| PB3 | 130 | OUT PP | — | none | STB transceiver 2 (FDCAN2 via PB5/6, modo normal) | red.h:13-15,79-81 |
| PD7 | 121 | OUT PP | — | none | STB transceiver 3 (bus2/FDCAN3) | red.h:16-18,83-85 |
| PB4 | 131 | OUT PP | — | none | STB transceiver 4 (FDCAN2 via PB12/13, modo OBD) | red.h:19-21,87-89 |
| PB1 | 50 | ANALOG | — | none | 5VOUT_S (configurado; **nenhuma leitura** no red.h) | red.h:91-93 |
| PB14 | 74 | OUT **OD** | — | **PULL_UP** | USB load switch — "enabled by pull resistor on board, obsolete for red panda"; saída 1 (Hi-Z) | red.h:95-99 |
| PC4 | 47 | ANALOG/INPUT | — | — | SBU1 (ADC1 INP4); alterna INPUT para leitura de ignição ("not 5V tolerant in ADC mode") | red.h:102-111; harness.h:63-66,86-88 |
| PA1 | 38 | ANALOG/INPUT | — | — | SBU2 (ADC1 INP17) | idem |
| PC10 | 109 | OUT **OD** | — | — | relay SBU1 (ativo-baixo; init = 1) | red.h:106-108; harness.h:98-101 |
| PC11 | 110 | OUT **OD** | — | — | relay SBU2 | idem |
| PE4 | 3 | OUT **OD** | — | none | LED RED (0 = acende) | red.h:124-125; led.h:21-31 |
| PE3 | 2 | OUT OD | — | none | LED GREEN | idem |
| PE2 | 1 | OUT OD | — | none | LED BLUE | idem |
| PE11–PE14 | 61–64 | AF5 SPI4 | — | — | `gpio_spi_init` só se `has_spi` (red: **false**) → NC | peripherals.h:14-19; red.h:118 |
| PA13/PA14 | 102/107 | SWD (reset default) | AF0 | — | debug; não reconfigurados pelo firmware | DS Tab.8 |
| PF7–PF10 | 21–24 | INPUT (pull-up transitório) | — | — | HW_TYPE id1 | board.h:25-29 |
| PD4–PD6 | 116,117,120 | INPUT (pull-up transitório) | — | — | HW_TYPE id2 | board.h:30-34 |
| GPIOH | — | clock ligado, MODER=0 | — | — | só PH0/PH1 (HSE) | stm32h7_config.h:93-95 |

`early_gpio_float()`: GPIOA->MODER = 0xAB000000 mantém PA13/PA14/PA15 em AF (SWD/JTDI) e **tudo o mais em input flutuante** no início (stm32h7_config.h:95). Implicação de hardware: transceivers devem ter STB puxado para standby por **pull-up externo** até o firmware configurar (fail-safe silencioso) **[I, D-09]**.

Sem uso no Red (funções `unused_*`): fan, bootkick, IR, siren, SOM GPIO, amp, read_current (red.h:117-134). `has_fan=false`, `has_spi=false`, `avdd_mV=3300`.

## 4. ADC e escalas

| Sinal | ADC/canal | Pino | Fórmula | Hardware derivado | Fonte |
|---|---|---|---|---|---|
| VOLT_S | ADC1 ch2 | PF11 | `adc_get_mV()*11` | divisor **1:11** (ex.: 100 k / 10 k → 12 V ≈ 1,09 V) **[I]** valores NV | red.h:68-70 |
| SBU1 | ADC1 ch4 | PC4 | mV absoluto vs `avdd/2 = 1650 mV` | detecção de orientação: SBU < 1,65 V = conectado; menor SBU = lado "relay" | red.h:110; harness.h:66-78 |
| SBU2 | ADC1 ch17 | PA1 | idem | idem | red.h:111 |
| VREFINT | ADC2 ch17 (interno) | — | `avdd = VREFINT_CAL*16*3300/raw` | calibração; requer VDDA = VREF+ **[I]** | lladc.h:54-64 |
| 5VOUT_S | — | PB1 | não lido | pino reservado; divisor opcional NV | red.h:91-93 |
| ADC1/2 | 16 bit (÷65535); ADC3 12 bit (÷4095) | | | | lladc.h:72-77 |

Corte de segurança: `read_voltage_mV() < 6000` com controls_allowed → ação (main.c:130). Divisor deve manter precisão em 6–16 V.

## 5. Barramentos CAN ↔ portas físicas

| bus (host) | can_number | Periférico | Pinos | Transceiver STB | Fonte |
|---|---|---|---|---|---|
| 0 | 0 | FDCAN1 | PB8/PB9 | PG11 (#1) | fdcan.h:5; drivers/can_common.h:117 |
| 1 | 1 | FDCAN2 | PB5/PB6 (**normal**, xcvr 2, STB PB3) **ou** PB12/PB13 (**OBD**, xcvr 4, STB PB4) — seleção: `(mode==NORMAL) != flipped` → PB5/PB6 | PB3 (#2) / PB4 (#4) | red.h:32-63 |
| 2 | 2 | FDCAN3 | PG9/PG10 | PD7 (#3) | drivers/can_common.h:119 |
| harness flipped | bus0↔bus2 trocados em `bus_config` | | | | drivers/can_common.h:130-134 |

CAN_MODE: `set_can_mode(NORMAL/OBD_CAN2)` escolhe qual par FDCAN2 ativa, dependendo de `harness.status == FLIPPED` (red.h:36-62). Velocidade default 500 k / 2 M (drivers/can_common.h:117-119, ×10 kbit).
**Hardware:** 4 transceivers CAN-FD; dois deles (2 e 4) partilham o mesmo FDCAN2 por multiplex de pinos — o firmware só habilita um por vez (os pinos do outro ficam ANALOG = alta impedância).

## 6. Mapa de memória

| Região | Valor | Fonte |
|---|---|---|
| FLASH | 0x08000000, 1024 K; setor 0 (128 K) = bootstub; app em **0x08020000** | stm32h7x5_flash.ld:71,89 |
| Provisioning | `PROVISION_CHUNK_ADDRESS 0x080FFFE0`, `DEVICE_SERIAL_NUMBER_ADDRESS 0x080FFFC0` (fim do 1 MB) | stm32h7_config.h:47-48 |
| RAM | DTCM 128 K @0x20000000 (stack), AXISRAM 320 K, SRAM1+2 32 K @0x30000000, SRAM4 16 K @0x38000000, Backup 4 K, ITCM 64 K | .ld:81-89 |
| Cookies | `enter_bootloader_mode 0x38001FFC`, `fault_cookie 0x38003FFC`, `self_test_cookie 0x38003FF8` (SRAM4) | .ld:58-60 |
| FDCAN Message RAM | base 0x4000AC00, 3384 B por módulo (46 RX FIFO0 + 1 TX, 72 B cada) | llfdcan_declarations.h:16-35 |
| Linker header | "STM32H735ZGTx ... 1024 K FLASH / 560 K RAM" (reutilizado) | .ld:9-10 |

→ **Variante exigida: Flash = 1 MB → sufixo "G"** (H725**Z**G**T6**). A variante "E" (512 K) é incompatível com provisioning em 0x080FFFC0 e com o layout do linker **[F]**.

## 7. Boot, DFU e gravação

| Item | Valor | Fonte |
|---|---|---|
| Bootloader ST | `BOOTLOADER_ADDRESS 0x1FF09804` (system memory) | stm32h7_config.h:12 |
| Entrada DFU | por software: `enter_bootloader_mode = ENTER_BOOTLOADER_MAGIC` → `jump_to_bootloader()`; também se IDCODE ≠ 0x483 | early_init.h:14-27,47-50,61-65 |
| BOOT0 | não usado pelo firmware; hardware deve manter BOOT0 (pino 135) em nível baixo (pull-down) para boot da Flash; opcionalmente botão para DFU de emergência **[I]**; option bytes BOOT_ADD **NV** (RM0468) | — |
| Fluxo oficial | `dfu-util -d 0483:df11 -a 0 -s 0x08020000 -D obj/panda_h7.bin.signed` e `-s 0x08000000:leave -D obj/bootstub.panda_h7.bin` | debug/dfu_util_h7.sh:9-11 |
| Assinatura | bootstub verifica SHA + RSA-1024 contra `release_rsa_key`; se compilado com `-DALLOW_DEBUG` também aceita `debug_rsa_key` | bootstub.c:60-84 |
| Build DEBUG | sem `RELEASE` no env: `cert = board/crypto/certs/debug` (chave privada **publicada no repo**) e `-DALLOW_DEBUG` | SConscript:12-21 |
| **RESTRIÇÃO** | Uma placa de terceiros só executa firmware (a) assinado pela comma (release, chave privada não pública) com bootstub oficial, ou (b) **build DEBUG completo (bootstub + app) compilado do fonte** — o bootstub DEBUG aceita a chave debug. Não se propõe nem é necessário desativar verificação. | bootstub.c; SConscript |
| Versão mínima | `MIN_VERSION 2`, `VERS_TAG 0x53524556` ("VERS") | bootstub.c:1-2 |
| Watchdog | `simple_watchdog_init(..., 3 s/8)` + IWDG1 | main.c:335-336; stm32h7_config.h:45 |

## 8. USB

| Item | Valor | Fonte |
|---|---|---|
| VID/PID | 0x3801 / 0xDDCC (app), 0xDDEE (bootstub); legado 0xbbaa aceito pelo host | config.h:11-17; python/__init__.py:128-129 |
| PHY | OTG_HS com **PHY FS interno** (`PHYSEL`), device-only, VBUS sensing **desativado** (`BVALOEN|BVALOVAL`) | llusb.h:14-33 |
| Hardware | PA11/PA12 diretos ao conector (sem resistores série exigidos pelo firmware); sem VBUS sense → VBUS não precisa ir a PA9; ESD no conector; VDD33USB=3,3 V, VDD50USB=5 V ou 3,3 V conforme DS §3.7 **[verificar DS]** | — |
| bcdDevice | definido como hw_type em runtime | usb.h:467 |

## 9. Controle: Black Panda (F4) — firmware legado

| Função | Black (F413) | Fonte (panda_legacy_f4) |
|---|---|---|
| Detecção | não DOS (PB1&PB7 pull-up), não WHITE (PA4–7 pull-down), não GREY (PA13 pull-down), não UNO (PB15) → **BLACK por exclusão** | board/stm32f4/board.h:20-37 |
| CAN1 bus0 | PB8/PB9 AF8 | stm32f4/peripherals.h:46-48 |
| CAN2 bus1 | PB5/PB6 (normal, xcvr2 STB PC13) / PB12/PB13 (OBD, xcvr4 STB PB10) AF9 | black.h:33-57 |
| CAN3 bus2 | PA8/PA15 AF11 | black.h:72-74 |
| STB | #1 PC1, #2 PC13, #3 PA0, #4 PB10 (1 = standby) | black.h:9-24 |
| VOLT_S | PC2 ADC ch12 ×11 | peripherals.h:42; white.h:68-70 |
| SBU1/SBU2 | PC0 (ch10) / PC3 (ch13); relays PC10/PC11 | black.h:91-100 |
| LEDs | PC9 / PC7 / PC6 OD | black.h:118-119 |
| USB load | PB1 (ativo-baixo) | black.h:27-29 |
| GPS | PC5, PC12 (desligado) | black.h:76-78 |
| USB | PA11/PA12 AF10 OTG_FS | peripherals.h:5-10 |

Validação do método: `parity_check.py` (STEP 3) será executado **primeiro** contra a netlist do baseline (01_BASELINE) com esta tabela F4; divergências → variante da placa ou erro de leitura, resolvidas antes de aplicar ao H7.

## 10. Requisitos de tensão/temperatura
- VDD 3,3 V (avdd_mV = 3300); VDDA/VREF+ = 3,3 V (calibração VREFINT assume referência = AVDD).
- H725 LQFP144: temperatura conforme sufixo "6" = −40…+85 °C (DS13311 ordering info; grau automotivo AEC-Q100 **não** — H7 não é AEC-Q; registrar como limitação).
- Corrente do core via SMPS: DS Tab.16 (L 2,2 µH, Isat 1,7 A) — consumo típico a 240 MHz **NV** (tabela de consumo não extraída).
