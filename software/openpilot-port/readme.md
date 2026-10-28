# Honda City G7 2023 (Brasil) no openpilot v0.9.9 para o black panda

Port completo do suporte ao Honda City 2023 BR (commaai/opendbc #2425, commit
`43006b9a`, 2025-08-19) para a ultima versao do openpilot que ainda suporta o
black panda (STM32F4): **openpilot v0.9.9** (tag `8aadf02b`, 2025-06-05, panda
`e462c34d`).

Estado: port revisado e validado contra a rota publica do City; **ainda nao
testado no carro**. Nao use em via publica sem os testes de bancada e de
estacionamento descritos no final.

## Repositorios

| Repo | Branch | Commits |
|---|---|---|
| github.com/kriptomad/opendbc | `firmwarecityg7-v0.9.9` (PR #1) | `e370a036` (v0.9.9) + 5 commits |
| github.com/kriptomad/openpilot | `v0.9.9-cityg7-blackpanda` (PR #1 contra `v0.9.9-base`) | `8aadf02b` (v0.9.9) + 5 commits |

Os `.patch` em `patches/` sao a serie `git format-patch` equivalente, para
reaplicar em qualquer clone (`git am patches/opendbc/*.patch` em cima de
`e370a036`; `git am patches/openpilot/*.patch` em cima de `v0.9.9`).

Submodulos do openpilot: `opendbc_repo -> 07add98b` (fork), `panda -> e462c34d`
(inalterado, ultimo com `board/boards/black.h` e `board/stm32f4/`). O
`.gitmodules` aponta o opendbc para `../../kriptomad/opendbc.git`.

## O que foi portado (opendbc)

1. `34dd823b` - cherry-pick byte a byte de `43006b9a`: `HONDA_CITY_7G` em
   `values.py` (CarSpecs, flags BOSCH_RADARLESS, DBC `honda_civic_ex_2022_can_generated`,
   STEER_THRESHOLD 600, listas de ECU), `fingerprints.py` (6 ECUs, FW identico ao
   upstream), `interface.py` (steerActuatorDelay 0.15, torqueBP/V 2560, torque tune),
   `torque_data/override.toml` `[1.2, 1.2, 0.23]`.
2. `5f439d78` - so CI: ruff fixado em 0.11.13 (era da v0.9.9).
3. `256ff78c` - rota de teste atualizada para a rota final do upstream
   `56b2cf1dacdcd033/00000017--d24ffdb376`; linha do City em `docs/CARS.md`.
4. `ae690dd7` - **correcoes necessarias** descobertas no deep-read:
   - **EPB_STATUS (0x1C2)**: o City nao envia essa mensagem. A v0.9.9 exigia
     `EPB_STATUS` a 50 Hz para todo Bosch, entao o CANParser daria timeout e o
     openpilot nunca engajaria. Backport da parte Python de commaai/opendbc
     `6fa346ed` (#2458): flag `HondaFlags.HAS_EPB = 512` detectada por 0x1C2 no
     fingerprint, controlando o parse de `EPB_STATUS` e `carState.parkingBrake`.
   - **transmissionType**: City e CVT tradicional com 0x191 `GEARBOX` (sem 0x1A3).
     A v0.9.9 so detectava cvt para Accord/Civic 2022; agora reporta `cvt` para o
     City. O decode de marcha usa o branch padrao `GEARBOX` (byte0 one-hot, 8 = D).
5. `07add98b` - **complemento do `6fa346ed`**: o commit upstream tambem movia a
   definicao de `EPB_STATUS` de `_bosch_2018.dbc`/civic_touring_2016/clarity/
   odyssey/odyssey_chn para `_honda_common.dbc`. Sem isso, Nidec com 0x1C2 no
   fingerprint (ex.: HR-V em `honda_fit_ex_2018`) ligava HAS_EPB e quebrava com
   `could not find message 'EPB_STATUS'` (pego pelo `test_models` do openpilot).
   Os 6 hunks de DBC foram aplicados literalmente; cada DBC Honda gerado passa a
   ter exatamente uma `BO_ 450 EPB_STATUS`, com os mesmos bits de
   `EPB_ACTIVE/EPB_STATE/CHECKSUM/COUNTER`.
6. `d42db044` - **auditoria 2026-10-28 (D1)**: backport do hunk de
   `steerActuatorDelay` de upstream `28a16218`. Na v0.9.9 o
   `ret.steerActuatorDelay = 0.1` generico vinha depois do bloco por carro e
   sobrescrevia o 0.15 do City (o carParams da rota upstream tem 0.15).
7. `052a515f` - **auditoria 2026-10-28 (D2)**: `ret.lateralTuning.torque.ki =
   0.3` so no bloco do City em `honda/interface.py` (carParams da rota upstream
   tem ki 0.3, vindo de upstream `fb5ac6d3`, que mudou o default global). Por
   decisao do dono o default global em `opendbc/car/interfaces.py` fica em 0.1
   (v0.9.9) para nao retunar outras plataformas: desvio deliberado do upstream,
   restrito ao City.

8. `b4125fe6` - **auditoria 2 (D-1)**: `BO_ 401 GEARBOX` em
   `honda_civic_ex_2022_can.dbc` passa a ter o layout `GEARBOX_CVT` do
   `_gearbox_common.dbc` upstream (`9ef0b1fb`): `GEAR_SHIFTER 44|5@0+` no
   byte 5, `VAL_ 1 P 2 R 3 N 4 D 7 L 10 S` (antes: `5|6@0+` no byte 0 com
   one-hot `32 L 16 S 8 D 4 N 2 R 1 P`). D decodifica igual nos dois layouts
   (6116/6116 quadros da rota), S e L divergiam. O nome da mensagem continua
   `GEARBOX`, logo `carstate.py` nao muda. Afeta City, HR-V 3G e Civic 2022,
   exatamente como no upstream (os tres usam o mesmo DBC la). Tambem
   normaliza `pyproject.toml` para LF (o `5f439d78` tinha sido gravado com
   CRLF por clone Windows; so o pin do ruff fica como diferenca real).

HEAD do opendbc: `b4125fe6`.

### Lado openpilot (9 commits)

- `857dee1dc` - submodule opendbc para o fork, linha do City em `docs/CARS.md`
  (mesmo formato do commit upstream `09aa21390`), entrada em `RELEASES.md`.
- `4937c6391` - commit vazio (indexacao dos workflows no fork).
- `52f261127` - so CI: `uv.lock` com o sha256 atual do wheel `metadrive-simulator`
  (a comma re-subiu o arquivo; backport de `4d53a26a0`), e job `build release`
  pulado fora de `commaai/openpilot` (depende do ref interno `__nightly`).
- `bac73ff1b` - bump do submodule para `07add98b`.
- `0a5c06856` - aviso do port no `README.md`.
- `c3e422ae9` - **auditoria 2026-10-28 (D3)**: hunk verbatim de upstream
  `bae7a610f` (`GearShifter.sport` aceito para Honda em `car_specific.py`); o
  City CVT tem posicao S.
- `89df27131` - bump do submodule `opendbc_repo` para `052a515f`.
- `8be62bc95` - **auditoria 2 (D-2)**: `torqued.py` `ALLOWED_CARS += 'honda'`
  (backport de upstream `839a77334`, ja presente quando o City foi mergeado
  la). `torqued` so aprende quando `lateralTuning == torque`; na v0.9.9 o
  City e o unico Honda com torque tune, entao os Honda com PID (e os
  segmentos Honda do process replay) continuam com `useParams = False`.
- `e841f3cc3` - bump do submodule `opendbc_repo` para `b4125fe6`.

### Auditoria completa (2026-10-28)

Relatorio completo da auditoria commit a commit (73 commits Honda + genericos,
CarParams campo a campo, TX byte a byte, safety, FW, diferencas residuais):
`auditoria-port-city-v099.md`. Ferramentas novas em `tools/`:
`gen_dbc_from_tree.py`, `dbc_struct_compare.py`, `route_scan4_audit.py`,
`carparams_compare.py`, `tx_byte_compare.py`. Nada validado no carro.

Push feito em 2026-10-27: opendbc `fork/firmwarecityg7-v0.9.9` = `052a515f`,
openpilot `origin/v0.9.9-cityg7-blackpanda` = `89df27131`. Run de CI
`selfdrive_tests.yaml` disparado: `40517138906`
(https://github.com/kriptomad/openpilot/actions/runs/40517138906).

### Auditoria 2, independente e adversarial (2026-10-28)

Segundo auditor, sem acesso as conclusoes do primeiro, em
`audit2/audit2/auditoria2-independente.md` (11 scripts `audit2/a2_*.py`, replay
com o codigo real do carstate/carcontroller sobre a rota: 0xE4 5410/5410,
0x1C8 2705/2705, 0x30C 541/541, 0x33D 541/541 identicos incluindo counter
e checksum; 0 diferencas em 33 campos de carState). Resultado:

- **D-1 funcional** (layout de `GEARBOX` S/L) - corrigido em opendbc
  `b4125fe6` (ver item 8 acima; `tools/check_gearbox_cvt.py` confere os seis
  valores P/R/N/D/L/S no DBC gerado).
- **D-2 consciente** (`torqued` para Honda) - aplicado em openpilot
  `8be62bc95`.
- **D-3 plataforma** - `common/pid.py` / `latcontrol_torque.py` tem
  anti-windup diferente do upstream (`455a6a586`, `ab44c9a4f`). Nao e
  especifico do City; nao portado (mudaria a lateral de todos os carros).
  A auditoria 1 dizia "common/pid.py identico": estava **errado**.
- **D-4 cosmetico** - CRLF em `pyproject.toml`, corrigido em `b4125fe6`.
- **D-5/D-6 cosmeticos** - sem acao.
- A afirmacao da auditoria 1 de que o `pandad` upstream so mudou SPI/CAN-FD
  tambem foi refutada (ha logica de relay/IsOnroad); e diferenca de
  plataforma, nao do City.

Serie `patches/` regenerada (9 opendbc + 11 openpilot). Push: opendbc
`fork/firmwarecityg7-v0.9.9` = `6cbc8005` (`b4125fe6` + README do branch),
openpilot `origin/v0.9.9-cityg7-blackpanda` = `9ad0dbb08` (`e841f3cc3` +
README do branch + bump). Run de CI em `e841f3cc3`: `40525385443`
(https://github.com/kriptomad/openpilot/actions/runs/40525385443): static,
build, unit, cars (0-3) verdes; process replay so com o diff esperado de
`carParams.flags` (16->528, 6->518) nos 2 segmentos Honda; macOS cancelado
(runner). Os READMEs dos dois branches listam commit a commit o que mudou
(gerados por `tools/readme_branch_note.py`).

## Auditoria do port (hunk a hunk)

`tools/audit_port_hunks.py` (rodar dentro de `../opendbc-v0.9.9-city-g7/`) le
`git show -U0` dos commits upstream portados e confere, para cada arquivo, que
toda linha adicionada existe no HEAD do branch e toda linha removida nao existe.
Resultado para `43006b9a` + `6fa346ed` (2026-10-27): 13 avisos, todos
explicados, nenhum faltando:

- `values.py` (2): as duas listas de ECU do upstream traziam `*HONDA_BOSCH_CANFD`
  no fim, vindo de um commit posterior a v0.9.9 nao relacionado ao City (Pilot
  CAN-FD). `CAR.HONDA_CITY_7G` esta nas duas linhas.
- `routes.py` (1): rota trocada de proposito pela rota final do upstream.
- DBCs (10): falso positivo - linhas genericas `SG_ COUNTER/CHECKSUM` que
  existem em outras mensagens dos mesmos arquivos; `BO_ 450` tem zero
  ocorrencias nos 5 arquivos de origem.

Lado openpilot comparado com o commit upstream `09aa21390` (RELEASES.md,
docs/CARS.md, opendbc_repo): equivalente.

## Como foi validado

- CI do fork opendbc: `test.sh (ubuntu-24.04)` e `--ubsan` **passam**. `macos` e
  `Safety mutation tests` falham tambem na base intocada (`e370a036`) por
  toolchain dos runners - pre-existente, nao relacionado ao port.
- Rota publica do City (`commadataci/.../00000017--d24ffdb376/0/rlog.zst`)
  decodificada frame a frame:
  - carParams gravado: `HONDA_CITY_7G`, `cvt`.
  - Todas as mensagens exigidas pelo `carstate.py` da v0.9.9 estao presentes nas
    frequencias esperadas, **exceto EPB_STATUS** (corrigido acima).
  - Comparacao sinal a sinal `honda_civic_ex_2022_can_generated` (v0.9.9) vs
    `honda_bosch_radarless_generated` (upstream atual) em todos os frames do bus 0:
    todos os sinais RX usados decodificam identicos. GEARBOX: v0.9.9 `8 -> D` e
    upstream `4 -> D` em 100% dos frames.
  - TX: `LKAS_HUD` byte 3 `SET_ME_X48 = 0x48` (v0.9.9) == `LDW_OFF` bit 27 +
    `SET_ME_X1` bit 30 (upstream). `STEERING_CONTROL` identico.
- Refactors Honda posteriores a v0.9.9 analisados (gear position #2457, steering
  sensors, SCM, LKAS_HUD overlaps, dynamic CANParser, checksums, torque em accel
  space, slimming carState): nenhum altera bytes no barramento para o City; so o
  EPB (#2458) tinha efeito funcional e foi backportado.
- openpilot fork, workflow `selfdrive`, run 40507192072 (commit `0a5c06856`):
  - `static analysis`, `build`, `unit tests`: **pass**.
  - `cars (0..3)` = `selfdrive/car/tests/test_models.py` sobre as rotas reais de
    todos os carros: **pass** (468/433/447/403 testes). `HONDA_CITY_7G` e a
    plataforma de indice 50 em `sorted(PLATFORMS)` -> shard `cars (2)`, 447 passed,
    0 failed: test_car_interface, test_car_params, test_panda_safety_rx_checks,
    test_panda_safety_tx_cases, test_panda_safety_carstate(+fuzzy) do City
    passaram com a rota `56b2cf1dacdcd033/00000017--d24ffdb376`.
  - `process replay`: falha **esperada e unica**: `carParams.flags` nos dois
    segmentos Honda (Civic Nidec `regenB328FF8BA0A`, Accord Bosch
    `regen6170C8C9A35`), processo `card` - e o bit novo `HAS_EPB = 512`. Os logs
    de referencia da comma sao anteriores ao backport e so podem ser regenerados
    com credenciais de upload da comma. Nenhum outro processo/segmento difere.
  - `build macOS`: falha de runner (`brew` sem formula `dawn`), pre-existente.
  - `build release`: pulado em forks (ref `__nightly`).
  - Historico: run 40502967932 falhou em tudo por hash do wheel `metadrive`
    (corrigido em `52f261127`); run 40503817720 pegou o HR-V (corrigido em
    `07add98b`).

## Como subir no black panda

1. No comma device (ou PC Linux) clone o fork e faca checkout do branch:
   `git clone -b v0.9.9-cityg7-blackpanda --recurse-submodules https://github.com/kriptomad/openpilot`
2. `scons -j$(nproc)` compila tambem o firmware do panda (`panda/board`, F4 e H7)
   com o safety de `opendbc_repo/opendbc/safety` (Honda Bosch radarless - sem
   alteracao para o City).
3. Flash do black panda: `panda/board/flash.py` com o panda em DFU
   (`panda/board/recover.py` se necessario). Toolchain local ja instalada em
   `%LOCALAPPDATA%\arm-gnu-toolchain\bin` para builds no Windows.
4. Antes de rodar no carro: teste de bancada com panda + harness Bosch B,
   confirmar fingerprint por FW (6 ECUs), `carParams.carFingerprint == HONDA_CITY_7G`,
   `transmissionType == cvt`, sem `canError`; depois teste parado/estacionamento.

## Arquivos locais

- `../opendbc-v0.9.9-city-g7/` - clone de trabalho (ignorado pelo git do HybridPanda).
- `../openpilot-v0.9.9-city-g7/` - clone `--shared` do hardware/reference/openpilot (ignorado).
- `.venv_city/` - venv para lint/scripts (ruff 0.11.13, cantools, pycapnp, zstandard).
- `patches/` - serie format-patch (versionada).
- `tools/` - `audit_port_hunks.py` (auditoria hunk a hunk), `gen_honda_dbcs_windows.py`
  (gera os DBCs Honda no Windows, onde `generator.py` nao roda), scripts de
  analise da rota (`route_scan*.py`, `dbc_signal_compare.py`).
