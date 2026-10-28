# PANDAREVIVE - escopo do forward-port STM32F4 / black panda

Branch: `revive-f4` em `C:\Users\costabr\Downloads\openpilot\pandarevive\panda`
(clone de kriptomad/panda, base = upstream/master 1305b78c, 2026-10-25).
Push autorizado em 2026-10-27: a branch esta em kriptomad/panda (PR de fork
kriptomad/panda#1 so para rodar o CI). Nenhum commit foi feito neste
repositorio HybridPanda.

Status honesto: o firmware F4 COMPILA (debug e release) junto com o H7 e o
body. Nada foi executado em hardware. Nao existe "validado" nem "pronto"
neste documento; apenas "compila" e "revisado por leitura".

## 1. Commits na branch revive-f4 (mais antigo primeiro)

| hash     | assunto |
|----------|---------|
| 967f6359 | board: restore STM32F4 / black panda sources verbatim |
| ed13efa9 | board: adapt STM32F4 port to current driver/sys structure |
| 87270986 | bxcan: port to the current can_common / fdcan.h structure |
| a56ee038 | build: add the STM32F4 panda target |
| 611b2d50 | python: restore STM32F4 / black panda support |
| ee3ba954 | misra: check the STM32F4 variant again |
| 9ed2fd36 | README: mention the black panda (STM32F413) target |
| e78c41e6 | misra: clean the STM32F4 variant and the H7 self test findings |

Total: 52 arquivos, +25435 / -38 linhas sobre 1305b78c. Todos os commits
levam o trailer `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`.
O commit ed13efa9 e intermediario (declarado na mensagem): o F4 so passa a
ter alvo de build em a56ee038; o H7 compila em todos os commits.

## 2. O que o upstream removeu

- 3d272335 (2025-07-19): `board/boards/black.h` e `white.h` (781 linhas).
- 1ce986f7 "bye bye f4" (2025-08-26): arvore `board/stm32f4/*`,
  `board/drivers/bxcan*.h`, `board/boards/dos.h`, `board/debug/dfu_util_f4.sh`,
  suporte F4 em `python/` (McuType.F4, HW_TYPE_BLACK/WHITE/DOS,
  st_serial_to_dfu_serial F4), bloco F4 em `tests/misra/*`.
- Depois disso (~134 commits): `*_declarations.h` consolidados em
  `board/drivers/drivers.h`; `critical/faults/power_saving` movidos para
  `board/sys/`; driver UART removido; jungle removido; `self_test.s`,
  `llmpu.h`, `lldts.h`, `clock_check`, `hold_unused_in_reset`,
  `adc_signal_t`, `can_health_t` com `irq2_call_rate`; safety movida
  para o pacote opendbc (`opendbc/safety/*.h`, `CANPacket_t` com
  `data[64]` fixo).

## 3. O que foi restaurado (967f6359)

Verbatim de `1ce986f7^` e `3d272335^`:
`board/stm32f4/{board.h, clock.h, inc/*, interrupt_handlers.h, lladc.h,
lladc_declarations.h, llbxcan.h, llbxcan_declarations.h, llfan.h,
llflash.h, llspi.h, lluart.h, llusb.h, llusb_declarations.h,
peripherals.h, startup_stm32f413xx.s, stm32f4_config.h,
stm32f4_flash.ld}`, `board/drivers/bxcan.h`,
`board/drivers/bxcan_declarations.h`, `board/boards/black.h`,
`board/debug/dfu_util_f4.sh`.

Removidos em seguida (ed13efa9 / 87270986) por nao existirem mais no
modelo atual: `lluart.h` (driver UART nao existe mais no H7), `llspi.h`
(black panda nao tem SPI), `bxcan_declarations.h` (prototipos foram para
`drivers.h`).

## 4. Adaptacoes de API, arquivo por arquivo

### 4.1 Camada MCU `board/stm32f4/`

- `stm32f4_config.h` (reescrito espelhando `stm32h7_config.h`):
  `MCU_IDCODE 0x463U` (l.5), `BOOTLOADER_ADDRESS 0x1FFF0004U` (l.13),
  `NUM_INTERRUPTS 102U` (l.20), inclui `sys/critical.h`, `sys/faults.h`,
  `drivers/mpu.h` (fora de BOOTSTUB), `stm32f4/board.h`, `clock.h`,
  `llflash.h` (BOOTSTUB) ou `llbxcan.h` + `llusb.h`. Stubs exigidos pelo
  codigo comum: `spi_error_count`, `spi_init()`,
  `can_tx_comms_resume_spi()` (l.74-76).
- `board.h`: apenas black. `detect_board_type()` (l.24-42) checa as
  assinaturas de pinos de dos/white/grey/uno e as mapeia para
  `HW_TYPE_UNKNOWN`; caso contrario `HW_TYPE_BLACK_PANDA` /
  `board_black`. Define `sound_output_level` (l.20) e `sound_tick()`
  vazio (l.22) porque o F4 nao tem saida de som.
- `lladc_declarations.h` / `lladc.h`: nova API `adc_signal_t`
  (`ADC_CHANNEL_DEFAULT`, 480 ciclos, oversampling 16 por software),
  `adc_measure_avdd_mV()` por VREFINT calibrado (l.48),
  `adc_check(expected_avdd)` +-10% (l.59), `adc_get_mV()` (l.64).
  So existe ADC1 no F413 usado aqui.
- `lldts.h` (novo): `dts_init()` (l.5) e `dts_get_temperature()` (l.10;
  l.18 converte cada temperatura de calibracao para float separadamente,
  MISRA 10.8, e78c41e6)
  via canal 18 + calibracao de fabrica (0x1FFF7A2C/2E), reescalado pelo
  AVDD medido.
- `clock.h`: `clock_check_init()` (l.42), `lsi_capture()` (l.53),
  `clock_check()` (l.64): LSI capturado em TIM5 CH4 (TIM5->OR TI4_RMP),
  janela 3/4..5/4 do nominal.
- `peripherals.h`: `flasher_peripherals_init()` (l.38),
  `hold_unused_in_reset()` (l.45) com mascaras de RSTR do F413
  (AHB1 0x006010FF, AHB2 0x000000C0, AHB3 0x00000003,
  APB1 0xFFFECBFF, APB2 0x035779F3), `peripherals_init()` (l.61)
  habilita GPIOA-D, DMA2, PWR, SYSCFG, OTGFS, CAN1-3, ADC1,
  TIM1/2/3/5/6/8/9 e chama `hold_unused_in_reset()` (l.91);
  `check_option_bytes()` (l.100) so verifica OPTLOCK (nao ha BOOT_ADD).
- `stm32f4_flash.ld`: RAM unica de 320K (l.54), cookies no topo
  (`enter_bootloader_mode` 0x2004FFFC, `fault_cookie` 0x2004FFF8,
  `self_test_cookie` 0x2004FFF4, l.36-39), `_estack 0x2004FFF0` (l.41),
  `_sram_start/_sram_end` (l.42-43), regiao `.data` com
  `_ssafety/_esafety` alinhada a 64B, stack guard, ASSERTs iguais ao H7
  mais `_estack <= _sram_end` (l.186).
- `startup_stm32f413xx.s`: `.fpu fpv4-sp-d16` (l.48), `bl
  ram_test_startup` apos `__initialize_hardware_early` (l.82), weak
  para `ram_test_none` (l.133-134).
- `self_test.s` (novo): copia do H7 para Cortex-M4 sem o bloco de clock
  de SRAM do RCC, regioes `_sram_start/_sram_end`.
- `llusb.h`, `llfan.h`, `llflash.h`, `interrupt_handlers.h`, `llbxcan.h`:
  `#pragma once` e `nvic_enable/nvic_disable` no lugar de `NVIC_*`.
- `llbxcan_declarations.h`: removido `void print()`, adicionado
  `CAN_ACK_ERROR 3U` (l.15).

### 4.2 bxCAN `board/drivers/bxcan.h` (87270986)

Reescrito tomando `board/drivers/fdcan.h` atual como molde:
`cans[PANDA_CAN_CNT]`, `can_irq_number[PANDA_CAN_CNT][3]`,
`can_set_speed()` com `can_silent` global, `can_clear_send()` limitado a
10 Hz com `can_core_reset_cnt`, `update_can_health_pkt()` preenchendo
`irq0/1/2_call_rate`, `last_data_error = 0`, limpeza de FOVR0,
`process_can()` sob `ENTER_CRITICAL` + `refresh_can_tx_slots_available()`,
`can_rx()` com `mpu_safety_open/close` ao redor de `safety_fwd_hook` e
`safety_rx_hook`, encaminhamento via `can_send(..., true)`,
`ignition_can_hook`, LED azul, `rx_buffer_overflow`. `pending_can_live`
removido (nao existe mais no can_common).

### 4.3 Codigo compartilhado

- `board/drivers/drivers.h`: l.6-9 selecao de `lladc_declarations.h`
  por MCU; l.103-117 bloco fdcan so H7; l.120-130 bloco bxcan so F4
  (`cans`, `CAN_IRQS_ARRAY_SIZE 3U`, `can_irq_number`, `can_clear_send`,
  `update_can_health_pkt`); l.132-207 harness + interrupts para
  `STM32H7 || STM32F4`.
- `board/drivers/mpu.h`: movido de `board/stm32h7/llmpu.h` (e
  independente de MCU: MPU v7-M em ambos). `stm32h7_config.h` ajustado.
- `board/drivers/self_test.h`: guardas `#ifdef STM32H7` em l.26, 49,
  59, 134, 199, 226, 319, 344, 378, 398: tabela de regioes (F4 =
  `_sram_start.._sram_end`, l.207-208), buffers de backup/DMA sem secao
  `.sram12`, `ram_test_skip` tambem pula os buffers no F4, sem scrub de
  ECC, sem checagem de BDMA/DMA1, sem flags de ECC no `self_test_check`
  e `self_test_init`. Em e78c41e6: `ram_test_block` inicializa as
  tabelas `alias`/`alias_val` inteiras antes da varredura (l.164-167,
  cppcheck `uninitvar` na variante F4), `ram_test_next` troca o modulo
  pelo wrap com ternario (l.227-229, `moduloofone` porque o F4 tem uma
  unica regiao), `ram_test_backup` volta a ser static local de
  `ram_test_block` no H7 (l.156-159, MISRA 8.9) e `ram_test_skip` nao
  tem mais variavel sempre falsa no H7 (l.133-140). O binario H7 muda em
  poucos bytes (text 68248 -> 68252 debug, 66432 -> 66456 release) por
  causa do laco de inicializacao e do wrap; mesma semantica.
- `board/drivers/harness.h`: l.9, l.72, l.86 e l.123 - cross-check com
  ADC2 (`adc_mismatches` e o `FAULT_ADC` dele) apenas no H7; F4 tem um
  unico ADC, entao o contador nem existe la (e78c41e6: cppcheck apontava
  `unsignedLessThanZero` num contador que nunca era incrementado).
- `board/drivers/clock_source.h`: so H7 (e78c41e6). O black panda nao
  tem saida de clock source; `stm32f4/board.h` nao inclui mais o
  driver, os prototipos em `drivers.h` l.82-89 ficam sob `STM32H7` e o
  comando 0xe6 em `main_comms.h` l.266-271 e no-op no F4 (MISRA 8.7
  acusava `clock_source_init` sem chamador no F4).
- `board/sys/power_saving.h`: l.57 `enter_stop_mode()` H7; l.166-...
  versao F4 (GPIO A-D analogicos, transceivers off, ADC1 off, EXTI0 =
  PC0 SBU1, EXTI3 = PC3 SBU2, EXTI5 = PB5 CAN2 RX, EXTI8 = PA8 CAN3 RX
  se harness invertido senao PB8 CAN1 RX, PWR->CR LPDS|FPDS, WFI,
  reset). Atencao: CAN1 RX (PB8) e CAN3 RX (PA8) compartilham a linha
  EXTI8, por isso a escolha depende da orientacao do harness.
- `board/main_comms.h`: l.316, 339, 348, 354, 360 - comandos
  ALLOW_DEBUG 0xef/0xf5 recebem alvos de registrador do F4 (TIM5->PSC,
  ADC->CCR TSVREFE, CAN1->IER TMEIE, APB1ENR TIM13EN); o teste "p6" nao
  tem equivalente no F4 e vira no-op comentado.
- `board/drivers/can_common.h` l.22-28: `CAN_RX_BUFFER_SIZE 2048U` no
  F4 (4096 no H7). Motivo: `CANPacket_t` agora e fixo em 72 bytes (antes
  o F4 usava `CANPACKET_DATA_SIZE_MAX 8`); 4096 x 72 + 3 x 416 x 72 =
  384768 bytes nao cabem em 320K (ld reportou overflow de 82944 bytes).
  Com 2048 sobram ~64K para .bss restante, heap e pilha. A fila TX
  continua em 416.
- `board/config.h` l.22-23, `board/main.c` l.20-22 (fdcan vs bxcan),
  `board/flasher.h` l.4-5 (`APP_START_ADDRESS 0x8004000U`).
- `board/boards/board_declarations.h` l.50 `HW_TYPE_BLACK_PANDA 3U`,
  l.62 `extern struct board board_black`.
- `board/boards/black.h`: struct `board` identica em campos a `red.h`
  (verificado por diff de campos): `has_fan=false` (l.102),
  `black_read_voltage_mV()` ADC1 ch12 x11 (l.81, l.110), harness com
  `adc_signal_SBU1/2 = ADC_CHANNEL_DEFAULT(ADC1, 10/13)` (l.94-95),
  `set_bootkick/read_current/set_fan_enabled/set_ir_power/set_siren/
  read_som_gpio/set_amp_enabled = unused_*`. Removidos
  `black_check_ignition` e `black_init_bootloader` (campos nao existem
  mais; ignicao vem do harness no codigo comum).

### 4.4 Build `SConscript` (a56ee038)

- l.98 `CPPPATH` usa `project["INC_DIR"]`; l.122 `self_test.s` por
  projeto; l.133-134 H7; l.147-... `base_project_f4`
  (`-mcpu=cortex-m4 -mhard-float -DSTM32F4 -DSTM32F413xx
  -Iboard/stm32f4/inc -mfpu=fpv4-sp-d16`, startup
  `startup_stm32f413xx.s`, ld `stm32f4_flash.ld`, app `0x8004000`);
  l.189 `build_project("panda", base_project_f4, ...)` gera
  `board/obj/panda.bin.signed` e `board/obj/bootstub.panda.bin`
  (mesmos nomes de antes de 1ce986f7, que `python/constants.py` usa).

### 4.5 Python (611b2d50)

- `python/constants.py` l.34 `F4Config` (idcode 0x463, setores
  4x16K + 64K + 11x128K, sector_count 16, uid 0x1FFF7A10, block 0x800,
  serial 0x1FFF79C0, app 0x8004000 `panda.bin.signed`, bootstub
  0x8000000 `bootstub.panda.bin`); l.65 `McuType.F4`.
- `python/__init__.py` l.133 `HW_TYPE_BLACK_PANDA = b'\x03'`, l.155
  `F4_DEVICES`, l.157 `SUPPORTED_DEVICES = F4_DEVICES + H7_DEVICES`,
  l.622 `get_mcu_type()` por HW type; usado em `flash()` (l.447, 462),
  `up_to_date()` (l.513) e `get_dfu_serial()` (l.656) no lugar de
  `McuType.H7` fixo.
- `python/dfu.py` l.108: serial DFU do F4 (`+ 0xA`), como antes.
  `PandaDFU.program_bootstub()` apaga setores 0 e 1 (comportamento atual
  do upstream; no F4 isso e bootstub + primeiro setor do app, suficiente
  porque `recover()` reflasha o app em seguida).
- `python/usb.py` ja identifica o MCU em DFU pelo `sector_count`
  (16 -> F4), sem mudanca.
- `tests/hitl/test_1_program.py`: compara `dfu.get_mcu_type()` com
  `p.get_mcu_type()` em vez de assumir H7.

### 4.6 MISRA / testes (ee3ba954)

- `tests/misra/test_misra.sh` l.65: variante F4 do cppcheck.
- `tests/misra/test_mutation.py` l.18, 26, 33, 63: ignora
  `stm32f4/inc` e `llflash.h`, mutacao F4-only em `llbxcan.h`.
- `tests/misra/checkers.txt`: bloco F4 na frente do H7, reconstruido
  como copia do bloco H7 com a linha de opcoes trocada (a lista de
  checkers do cppcheck nao depende dos defines). NAO foi gerado pelo
  cppcheck 2.21.0 do CI: `comma-deps-cppcheck` nao tem wheel para
  Windows. Com o cppcheck 2.22.0 local (secao 5.1) os relatorios
  `--checkers-report` das variantes F4 e H7 sao identicos entre si, o
  que sustenta a copia, mas 2.22 lista 269/389 checkers e 2.21 267/386,
  entao o arquivo so pode ser confirmado pelo CI (test_misra.sh sai com
  codigo 4 se divergir; nesse caso basta commitar o que o CI gerar).
- `.github/workflows/test.yaml`: nao alterado; o job `build` roda
  `scons` (debug e `RELEASE=1`) que agora inclui o F4, e `./test.sh`
  roda ruff + unittest. Nao ha matriz por MCU para alterar.

## 5. O que compila (evidencia local)

Toolchain: Arm GNU Toolchain 14.2.Rel1 (mingw-w64 x86_64), extraida em
`C:\Users\costabr\Downloads\openpilot\pandarevive\toolchain\bin`
(winget falhou; zip oficial baixado via curl). Python: venv
`panda\.venv_pr` (Python 3.13 - fora do `< 3.13` do pyproject, so
afeta o aviso do pycapnp no macOS), opendbc clone em
`pandarevive\opendbc` via `PYTHONPATH`.

Observacao sobre o SConstruct no Windows: o `SConstruct` upstream nao e
portavel (SCons escolhe msvc e `tests/libpanda` precisa de gcc de host).
O build local usou um arquivo auxiliar NAO commitado
(`local_build_windows.scons`, copia deixada ao lado deste documento):
mesmo conteudo do SConstruct + plataforma posix forcada + spawn direto
+ `tests/libpanda` pulado. O `SConscript` do repositorio e o mesmo que
o CI Linux usa.

`scons -j8` (debug, `-DALLOW_DEBUG`):

```
   text    data     bss     dec     hex filename
  59476     900  262268  322644   4ec54 board/obj/panda/main.elf       (F4)
  10988    1204   22860   35052    88ec board/obj/panda/bootstub.elf   (F4)
  68248    1108  433725  503081   7ad29 board/obj/panda_h7/main.elf
  18352    1420   46565   66337   10321 board/obj/panda_h7/bootstub.elf
  65112    1096  419769  485977   76a59 board/obj/body_h7/main.elf

bootstub.panda.bin      12200   panda.bin.signed      60524
bootstub.panda_h7.bin   19792   panda_h7.bin.signed   69516
bootstub.body_h7.bin    12936   body_h7.bin.signed    66368
```

`RELEASE=1 CERT=board/crypto/certs/debug scons -j8`: tambem OK
(F4 main text 57680, H7 main text 66432).

Apos e78c41e6 (debug): F4 main text 58944 / data 900 / bss 262268,
F4 bootstub text 10544, H7 main text 68252, body 65112;
`bootstub.panda.bin` 11756, `panda.bin.signed` 59992,
`panda_h7.bin.signed` 69520. Release: F4 main text 57144, H7 66456.
O F4 encolheu porque `clock_source.h` saiu do build.

Checagens no ELF F4: `.isr_vector` em 0x08004000 com 0x1D8 bytes
(16 + 102 vetores), `_estack 0x2004FFF0`, cookies 0x2004FFF4/F8/FC,
`.bss` termina em 0x2003FB3C, `_stack_guard 0x2003FC00`.

Python/lint:
- `ruff check .` -> All checks passed.
- `mypy python/` -> os mesmos 6 erros de ambiente da base (usb1 sem
  stubs, opendbc.car.structs, libusb_package, INCLUDE_PATH); nenhum
  novo. mypy nao faz parte do CI do panda.
- `python -W error -m unittest discover -s tests`: 47 testes;
  `usbprotocol.test_pandalib` OK; HITL todos "skipped (HITL=1)";
  `usbprotocol.test_comms` ERRO por falta de `libpanda.so` (precisa gcc
  de host; limitacao do Windows, igual na base); `misra.test_mutation`
  FALHA por falta de bash/cppcheck (idem). O TU `tests/libpanda/panda.c`
  foi ao menos checado com `arm-none-eabi-gcc -fsyntax-only` antes e
  depois das mudancas: ambos OK.
- Sanidade da API: `Panda.SUPPORTED_DEVICES` = [03, 07, 09, 0a, b1];
  `McuType.F4.config.sector_address(1) == 0x8004000`;
  `st_serial_to_dfu_serial(..., F4)` difere da H7 pelo `+0xA`.

### 5.1 cppcheck/MISRA local e CI (2026-10-27)

CI do fork, run 40521727858 (commit 9ed2fd36):
- `windows pip package test`: OK.
- `./test.sh (ubuntu-latest)`: FALHOU em `test_misra_mutation_0` (arvore
  sem mutacao) com 6 achados, todos na variante F4: harness.h:121
  unsignedLessThanZero, self_test.h:220 moduloofone, self_test.h:183
  uninitvar (alias e alias_val), lldts.h:18 misra 10.8,
  clock_source.h:18 misra 8.7. As mutacoes 1 e 2 (power_saving.h e
  llbxcan.h) foram detectadas, ou seja, o checker roda a variante F4.
- `build`: FALHOU no passo "Test python package installer" com
  "Package 'pandacan' requires a different Python: 3.14.4 not in
  '<3.13,>=3.12.3'". Causa: `ubuntu-latest` passou a resolver para a
  imagem ubuntu-26.04 (Python de sistema 3.14.4); o passo roda `pip`
  depois de `source .venv/bin/activate`, mas o venv do uv nao tem pip,
  entao cai no pip do sistema ("Defaulting to user installation"). Nos
  runs do upstream commaai/panda de 26-27/10 (40396070449 OK,
  40431444057) a imagem ainda era ubuntu-24.04 com Python 3.12.3 e o
  mesmo passo passou. Nao e regressao desta branch (`setup.sh`,
  `pyproject.toml` e `test.yaml` sao identicos ao upstream) e o upstream
  ainda nao tem correcao; nada foi alterado no workflow. Correcoes
  possiveis quando o upstream decidir: fixar `runs-on: ubuntu-24.04` ou
  trocar o passo por `uv pip install .[dev]`.
- `./test.sh (macos-latest)`: cancelado pela falha do ubuntu.

Correcao local (e78c41e6): cppcheck 2.22.0 extraido do MSI oficial
(`msiexec /a`, sem instalar) e rodado com as mesmas opcoes de
`tests/misra/test_misra.sh` (`--check-level=exhaustive --safety
--addon=misra`, suppressions.txt, includes do arm-gcc e do opendbc),
script `pandarevive\run_misra.ps1`. Resultado: variante F4 sem achados,
variante H7 sem achados (a H7 tinha 2 achados introduzidos pelos
commits anteriores e nao alcancados pelo CI: self_test.h
knownConditionTrueFalse e misra 8.9). Build debug e release OK depois.
Novo run do CI apos o push (commit e78c41e6): 40525636665.
- `./test.sh (ubuntu-latest)` (imagem ubuntu-26.04): OK. scons das tres
  imagens, ruff e `unittest`: 51 testes, OK (42 HITL skipped);
  `test_misra_mutation_0` (arvore limpa, variantes F4 e H7 com cppcheck
  2.21.0) OK, mutacoes 1 e 2 detectadas; `test_comms` com libpanda OK.
- `windows pip package test`: OK.
- `build`: FALHOU de novo no mesmo passo de pip/Python 3.14 (imagem
  ubuntu-26.04), pre-existente, ver acima; os passos `scons` debug e
  release desse job nao chegam a rodar no CI, mas o debug roda no
  `./test.sh` e o release foi feito localmente.
- `./test.sh (macos-latest)`: ainda em fila (queued) ~1h depois do push, no momento
  deste relatorio; o run anterior tambem nao conseguiu runner macOS antes
  de ser cancelado. Conferir em https://github.com/kriptomad/panda/actions/runs/40525636665

Atencao: `test_mutation.py` chama `test_misra.sh` com
`SKIP_TABLES_DIFF=1`, entao o CI NAO compara `tests/misra/checkers.txt`
nem `coverage_table`. Esses arquivos so sao conferidos quando alguem
roda `tests/misra/test_misra.sh` direto num Linux/macOS com o
`comma-deps-cppcheck` 2.21.0 do pyproject; e isso que falta para
confirmar o bloco F4 do checkers.txt.

## 6. O que NAO foi testado (tudo que depende de hardware)

Sem uma black panda ligada, nada abaixo foi exercitado:

1. Enumeracao USB (OTG FS do F4 com o `llusb.h` restaurado + `usb.h`
   atual) e o protocolo de controle/bulk.
2. Timing do bxCAN (prescaler via `can_speed_to_prescaler`, PCLK1 48 MHz,
   quanta/SEQ1/SEQ2 antigos) nas 3 interfaces, incluindo o multiplex
   CAN1/CAN3 por `set_can_mode` e o encaminhamento por `safety_fwd_hook`.
3. `delay()` em `llbxcan.h`: `libc.h` atual escala para o clock do H7;
   no F4 a 96 MHz os tempos de espera de INAK/SLAK sao diferentes dos
   originais (ha timeout com contagem, nao trava, mas o valor absoluto
   mudou).
4. Deteccao de harness so com ADC1 (sem o cross-check ADC2 do H7) e a
   calibracao do AVDD por VREFINT (`adc_check` pode disparar
   `FAULT_ADC` indevidamente se o calculo estiver errado).
5. Temperatura (`lldts.h`): formula com calibracao de fabrica; valor
   so aparece no health, nao afeta safety.
6. `clock_check()` com LSI em TIM5 CH4 (`TIM5->OR` remap): se a captura
   nao acontecer o firmware levanta falha de clock; isto precisa de teste
   real.
7. `hold_unused_in_reset()`: mascaras derivadas de `stm32f413xx.h`;
   um bit errado deixa um periferico necessario em reset. Os enables
   feitos antes (USB, CAN1-3, ADC1, timers, DMA2, SYSCFG, PWR) foram
   conferidos por leitura.
8. Startup RAM march (`self_test.s` F4) e o `ram_test_next()` em
   runtime na RAM unica (cookies preservados em r10/r11 como no SRAM4 do
   H7) - nunca rodou.
9. MPU (`drivers/mpu.h`) nas regioes do F4 (`_ssafety/_esafety`,
   stack guard): o layout do ld foi feito para isso, sem execucao.
10. Stop mode F4 (`power_saving.h`): so alcancavel pelo comando de
    debug 0xb5; compartilhamento EXTI8 entre PB8 e PA8.
11. DFU: enderecos/serial no python e o `dfu_util_f4.sh` nao foram
    exercitados; o bootstub F4 (12200 bytes) cabe no setor 0 de 16K.
12. Fila RX de 2048 pacotes: comportamento sob carga alta (3 barramentos
    a 500 kbit) nao medido; o antigo F4 tinha 4096 entradas (de 16 B).
13. HITL: `test_6_safety` injeta `inject_readback_fault(p6)` e falhas de
    ECC que no F4 sao no-op/inexistentes; `test_7_internal` so roda em
    tres/cuatro; `test_9_harness` assume 3300 mV para nao-tres/cuatro
    (correto para a black). Precisa de ajuste quando houver bancada.
14. MISRA/cppcheck para a variante F4 (ver 4.6).

## 7. Mudancas ainda necessarias do lado openpilot

Nao fazem parte desta execucao; lista do que conferir:

- `cereal/log.capnp`: `PandaType.blackPanda @3` ainda existe no enum;
  nada a mudar la.
- `selfdrive/pandad/`: `panda.cc`/`pandad.py` usam
  `Panda.SUPPORTED_DEVICES`/`get_mcu_type()`; conferir que
  `pandad.py` nao filtra `is_internal()` nem exige SPI e que o fluxo
  de flash (`flash_panda` com `McuType`) chama `get_mcu_type()` em vez
  de assumir H7. Verificar tambem `panda.cc` quanto a
  `hw_type == black` em `can_health`/`fan`/`som` (campos ausentes devem
  continuar zerados).
- `system/hardware`/`selfdrive/ui`: alertas que tratam "panda antiga"
  (deprecated) poderiam bloquear a black; procurar por `HW_TYPE_BLACK`
  / `DEPRECATED_DEVICES` (removido daqui) no openpilot.
- Submodulos: apontar `panda` para a `revive-f4` (apos push) e manter o
  `opendbc` no commit que o SConscript e o `CAN_PACKET_VERSION_HASH`
  esperam (o hash e calculado do `opendbc/safety/can.h`; python e
  firmware devem ver a mesma copia).
- Honda City (BR) 2023: ja esta no opendbc master; a black panda e so
  CAN classico (sem CAN FD), e o safety `honda` nao exige FD. Nada a
  fazer no opendbc para o City; `set_can_mode`/`canfd_enabled` ficam
  false.
- Release notes / docs do fork: registrar que a black panda volta como
  alvo `panda` (F4) ao lado de `panda_h7`, e que SPI, fan, siren, som,
  SOM GPIO e CAN FD nao existem nesse hardware.

## 8. Itens em aberto (resumo)

- Nenhum teste em hardware (secao 6 inteira).
- `tests/misra/checkers.txt` reconstruido a mao; o CI nao o compara
  (SKIP_TABLES_DIFF=1 no test_mutation.py). Rodar
  `tests/misra/test_misra.sh` num Linux com o cppcheck 2.21.0 do
  pyproject e commitar o que ele gerar, se divergir.
- Job `build` do CI vermelho por causa da imagem ubuntu-26.04 / Python
  3.14 no passo `pip install .[dev]` (pre-existente, igual no upstream
  assim que os runners deles migrarem); decisao de correcao fica para
  o upstream ou para o owner (fixar ubuntu-24.04 ou usar `uv pip`).
- `tests/libpanda` nao executavel neste Windows (rodou OK no CI Linux);
  cppcheck local e 2.22.0, o CI usa 2.21.0 (ambos limpos no commit
  e78c41e6).
- `.github/workflows/test.yaml` inalterado (ja cobre o F4 via `scons`);
  se quiser artefatos separados do F4, adicionar depois.
- Arquivo auxiliar `local_build_windows.scons` existe so fora do repo
  (idem `run_misra.ps1` em `pandarevive\`).
- Branch `revive-f4` enviada para kriptomad/panda (push autorizado em
  27/10); nada foi enviado para commaai/panda.
