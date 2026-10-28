# AUDITORIA 2 (independente, adversarial) - port Honda City G7 2023 (BR) para openpilot v0.9.9 / black panda

Data: 2026-10-28. Autor: segundo auditor, sem acesso a carro ou hardware.
Objetivo: tentar PROVAR ERRADO o port, re-derivando tudo de codigo e dados; o
relatorio do primeiro auditor (`../auditoria-port-city-v099.md`) foi usado apenas
como lista de afirmacoes a falsificar.

Revisoes auditadas (fixas no inicio da auditoria; nenhuma mudou durante ela):

| Repositorio | Branch | HEAD | Base | Upstream de referencia |
|---|---|---|---|---|
| opendbc (fork) | `firmwarecityg7-v0.9.9` | `052a515f` | `e370a036` (opendbc da v0.9.9) | `43006b9a` (City no opendbc, 2025-08-19) |
| openpilot (fork) | `v0.9.9-cityg7-blackpanda` | `89df27131` | `8aadf02b` (v0.9.9) | `09aa21390` (City no openpilot, 2025-08-19) |
| panda (submodule) | - | `e462c34d` (2025-06-03) | - | `3dc21386` (gitlink do openpilot `09aa21390`) |

Cadeia opendbc: `e370a036 -> 34dd823b -> 5f439d78 -> 256ff78c -> ae690dd7 ->
07add98b -> d42db044 -> 052a515f`. Cadeia openpilot: `8aadf02b -> 857dee1dc ->
4937c6391 -> 52f261127 -> bac73ff1b -> 0a5c06856 -> c3e422ae9 -> 89df27131`.
Gitlink `opendbc_repo` em `89df27131` = `052a515f` (confere com o HEAD do
opendbc auditado); gitlink `panda` = `e462c34d`.

Nada neste documento foi testado em veiculo. Nenhum repositorio foi alterado:
tudo foi lido com `git show`/`git diff`/worktrees temporarios; os patches
propostos estao em `audit2\proposed-patches\` e NAO foram aplicados.

---------------------------------------------------------------------------

## 1. Metodo (o que foi feito de diferente do primeiro auditor)

1. **Replay com o codigo real das duas arvores** (`audit2\a2_replay.py`):
   em vez de um packer proprio, foram executados `CarInterface.get_params`,
   `CarInterface.update` (carstate) e `CarInterface.apply` (carcontroller +
   hondacan) da arvore do port (HEAD `052a515f`, com um shim puro-Python do
   parser/packer C++ da v0.9.9 - `audit2\a2_v099_shim.py`, fiel a
   `parser_pyx.pyx`/`packer_pyx.pyx`/`dbc.cc`) e da arvore upstream
   `43006b9a` (parser Python nativo), alimentados com os MESMOS quadros CAN
   e os MESMOS `carControl` do rlog da rota de CI do City
   (`56b2cf1dacdcd033/00000017--d24ffdb376/0`, 61,18 s, 6111 eventos `can`,
   5531 `carControl`, 5480 `sendcan`). Saida: `carState` e quadros TX das
   duas arvores comparados entre si e com os `carState`/`sendcan` gravados
   pelo upstream no carro.
2. **DBC**: geracao de `honda_civic_ex_2022_can_generated.dbc` a partir das
   tres arvores (base, HEAD, upstream) com o `generator.py` de cada uma
   (`audit2\a2_gen_dbcs.py`) e comparacao estrutural completa com cantools
   (`audit2\a2_dbc_compare.py`): id, dlc, start bit, tamanho, ordem, sinal,
   fator, offset, min/max, unidade, receptores, VAL_.
3. **Decodificacao de GEARBOX 0x191** em TODOS os 6116 quadros do bus 0 com
   os dois DBCs; verificacao do patch proposto por regeneracao do DBC
   corrigido e nova decodificacao (`audit2\a2_make_gearbox_patch.py`).
4. **Safety**: `git diff HEAD 43006b9a` de `opendbc/safety/modes/honda.h`,
   `safety.h`, `safety_declarations.h`, `board/can_declarations.h`,
   `tests/test_honda.py`, lido hunk a hunk para o modo `hondaBosch` com
   param `RADARLESS|BOSCH_LONG` (10) e `RADARLESS` (8).
5. **Firmware do panda**: `git diff --stat e462c34d 3dc21386` (27 commits) e
   leitura dos hunks que tocam CAN classico, harness, rele, health, USB.
6. **openpilot**: `git diff 8aadf02b 09aa21390` em `selfdrive/car`,
   `selfdrive/controls`, `common/pid.py`, `selfdrive/pandad`,
   `selfdrive/locationd/torqued.py`, `docs/CARS.md`; e `git diff 8aadf02b
   89df27131` completo do fork.
7. **Identidade/higiene**: bytes dos arquivos tocados pelo port (CRLF,
   newline final, `audit2\a2_crlf_check.py`), `uv.lock`, `.gitmodules`,
   gitlinks, `pyproject.toml`.

Ferramentas e artefatos: `audit2\*.py` (listados na secao 9); rlog e dump em
`%TEMP%\city_rlog\` (`rlog.zst`, `events.pkl`, `replay_head.json`,
`replay_up43.json`, `replay_compare.txt`, `scan1.txt`). O rlog fica para
reuso; os demais rascunhos de `%TEMP%` foram removidos.

---------------------------------------------------------------------------

## 2. Resultado em uma pagina

**Nao foi encontrada nenhuma diferenca de byte, bit, mensagem, limite de
safety, flag ou parametro no caminho do City que esteja presente na rota de
CI** - os quadros TX 0xE4/0x1C8/0x30C/0x33D (incluindo counter e checksum)
produzidos pela arvore do port e pela arvore upstream sao identicos em
100 % dos ciclos (5410 + 2705 + 541 + 541 quadros); todos os campos de
`carState` lidos pelo openpilot sao identicos, exceto dois campos que o
upstream removeu e que a v0.9.9 ainda publica sem consumidor.

Divergencias encontradas (detalhes na secao 7):

| # | Severidade | Onde | Resumo |
|---|---|---|---|
| D-1 | **funcional (risco, nao verificavel na rota)** | opendbc `opendbc/dbc/generator/honda/honda_civic_ex_2022_can.dbc` BO_ 401 | GEARBOX 0x191 decodificado por byte0 one-hot (S=16, L=32) na v0.9.9; upstream decodifica byte5 bits 4..0 (P1 R2 N3 D4 L7 S10). Em P/R/N/D equivalente (6116/6116 quadros); em S/L o comportamento diverge. Patch `0001` (DBC-only, conferido na rota). |
| D-2 | funcional (plataforma, divergencia consciente) | openpilot `selfdrive/locationd/torqued.py` | upstream `839a77334` (2025-08-06) habilitou aprendizado de `latAccelFactor`/`friction` para Honda, ja presente quando o City entrou; no fork fica fixo em `[1.2, 1.2, 0.23]`. Patch `0003` opcional. |
| D-3 | funcional (plataforma, divergencia consciente) | openpilot `common/pid.py`, `selfdrive/controls/lib/latcontrol_torque.py` | O primeiro relatorio afirma que `common/pid.py` e identico entre v0.9.9 e `09aa21390`: **falso** (`455a6a586`, 13+/19-: anti-windup diferente, remocao de `override`/`i_unwind_rate`, `set_limits`). Mesma estrutura linear, mas a saturacao do integrador nao e bit-a-bit igual. Nao e especifico do City; nao portavel isoladamente. Sem patch. |
| D-4 | cosmetica | opendbc `pyproject.toml` | commit `5f439d78` reescreveu as 133 linhas com CRLF (unico repositorio/arquivo do port com CRLF). Patch `0002`. |
| D-5 | cosmetica | opendbc `carstate.py` | `carState.gas` (PEDAL_GAS, 5540 amostras != 0) e `steeringTorqueEps` (0x1AB, 205 amostras != 0) publicados na v0.9.9; upstream nao os publica. Nenhum consumidor em `selfdrive/`, `system/`, `common/` (so `tools/plotjuggler/layouts/tuning.xml`). Sem patch. |
| D-6 | cosmetica | opendbc `values.py` | `HondaBoschPlatformConfig` sem `@dataclass` (igual a base v0.9.9; upstream tem). Sem efeito: herda `__init__` do dataclass pai e o hook `init()` roda (flags=12, specs corretos no replay). Sem patch. |

Afirmacoes do primeiro relatorio refutadas: 2 (secao 8): "`common/pid.py` e
identico" e "`pandad`: mudancas de SPI/CAN-FD, sem efeito" (ha tambem mudanca
de logica de rele por `IsOnroad`, nao especifica do black panda - classificada
como plataforma, nao bloqueante). Tudo o mais foi CONFIRMADO ou e NAO
VERIFICAVEL pelos mesmos motivos (S/L, EPB, estrada).

---------------------------------------------------------------------------

## 3. Area 1 - opendbc Honda (python) em HEAD `052a515f` vs upstream `43006b9a`

Comando base: `git diff HEAD 43006b9a -- opendbc/car/honda` (lido inteiro) e
`git diff --stat e370a036 HEAD` (pegada do port: 14 arquivos).

### 3.1 values.py
- `CAR.HONDA_CITY_7G = HondaBoschPlatformConfig([HondaCarDocs("Honda City
  (Brazil only) 2023", "All")], CarSpecs(mass=3125*LB_TO_KG, wheelbase=2.6,
  steerRatio=19.0, centerToFrontRatio=0.41, minSteerSpeed=23*KPH_TO_MS),
  {Bus.pt: 'honda_civic_ex_2022_can_generated'}, flags=BOSCH_RADARLESS)`:
  textualmente igual ao upstream (nao aparece no diff).
- `HondaFlags`: `BOSCH_EXT_HUD=1, BOSCH_LONG=2, BOSCH=4, BOSCH_RADARLESS=8,
  NIDEC=16, NIDEC_ALT_PCM_ACCEL=32, NIDEC_ALT_SCM_MESSAGES=64,
  BOSCH_ALT_BRAKE=128, HAS_EPB=256`; upstream adiciona `BOSCH_CANFD`/
  `ALLOW_MANUAL_TRANS` (nao usados pelo City). `CP.flags` do City = 12 nos
  dois lados (replay e carParams da rota).
- `HONDA_BOSCH_RADARLESS = CAR.with_flags(BOSCH_RADARLESS)`: City incluido nos
  dois lados. `STEER_THRESHOLD`: City usa default 1200 nos dois lados.
- `CarControllerParams`: `STEER_STEP 1`, `STEER_DELTA_UP 3`,
  `STEER_DELTA_DOWN 3`, `STEER_DRIVER_ALLOWANCE/MULTIPLIER/FACTOR`,
  `BOSCH_ACCEL_MIN -3.5`, `BOSCH_ACCEL_MAX 2.0`, `BOSCH_GAS_LOOKUP_BP/V`,
  `STEER_MAX = torqueV[-1] = 2560` (o City define `torqueBP/V [[0,2560],
  [0,2560]]`): identicos (classe fora do diff).
- `FW_QUERY_CONFIG`: requests, `extra_ecus`, `non_essential_ecus` identicos
  salvo `*HONDA_BOSCH_CANFD` em listas (plataformas CAN-FD inexistentes na
  v0.9.9). `CAR.HONDA_CITY_7G` presente nas duas listas de `non_essential_ecus`
  (`eps`, `vsa`) nos dois lados -> match exato so exige `fwdRadar`, exatamente
  o que a rota mostra (`carFw` com uma entrada, `fingerprintSource=fw`,
  `fuzzyFingerprint=False`).
- `HondaCarDocs.init_make`: harness `bosch_b` para `BOSCH_RADARLESS` nos dois
  lados. Linha gerada em `docs/CARS.md`: `|Honda|City (Brazil only) 2023|All|
  openpilot available|0 mph|14 mph|star-full|star-full|Honda Bosch B
  connector...|` (14 mph = 23 km/h de `minSteerSpeed`; igual ao upstream).

### 3.2 fingerprints.py
Bloco `CAR.HONDA_CITY_7G` comparado byte a byte (string do bloco inteiro,
22 linhas): **identico** - `eps 0x18da30f1 None b'39990-T14-B030\x00\x00'`,
`gateway 0x18daeff1 b'38897-T14-M110\x00\x00'`, `srs 0x18da53f1
b'77959-T00-B830\x00\x00'`, `fwdRadar 0x18dab0f1 b'36161-T14-P050\x00\x00'`,
`vsa 0x18da28f1 b'57114-T14-B030\x00\x00'`, `transmission 0x18da1ef1
b'28101-63B-M420\x00\x00'`. O arquivo so tem `FW_VERSIONS` (sem dicionario de
fingerprint CAN) na v0.9.9 e no upstream: o City depende exclusivamente de FW.

### 3.3 interface.py (`_get_params` para o City, em ordem de execucao)
HEAD: `CAN = CanBus(ret, fingerprint)` -> `dashcamOnly = candidate in
HONDA_BOSCH_CANFD` (False) -> `safetyConfigs=[hondaBosch]` ->
`radarUnavailable=True` (radarless) -> `experimentalLongitudinalAvailable=
True`, `openpilotLongitudinalControl = experimental_long` -> `pcmCruise = not
openpilotLongitudinalControl` -> `HAS_EPB` se 0x1C2 (ausente -> nao) ->
`transmissionType=cvt` (City com 0x191) -> `steerActuatorDelay=0.1` ->
`steerLimitTimer=0.8` -> long tune (BOSCH_LONG kiBP/kiV) -> bloco do City:
`steerActuatorDelay=0.15`, `torqueBP/V [[0,2560],[0,2560]]`,
`configure_torque_tune` (kp 1.0, kf 1.0, ki 0.1, friction 0.23, LAF 1.2),
`ki=0.3` -> `BOSCH_LONG` no param se `openpilotLongitudinalControl` ->
`RADARLESS` no param -> `minEnableSpeed` (-1 para `autoResumeSng`).
Upstream: mesma ordem; diferencas: `dashcamOnly` so via EPS modificado
(fw com `,` - o EPS do City nao tem), `ki` vem do default global 0.3,
`transmissionType` por auto-deteccao (`0x191 -> cvt`, igual para o City),
`init()` com `communication_control`/`deinit` (so Bosch COM radar).
Resultado numerico (replay, 95 chaves): **unica diferenca
`lateralTuning.torque.useSteeringAngle`** (HEAD True; upstream campo
renomeado `useSteeringAngleDEPRECATED=False`). Vs carParams gravado pelo
upstream: + `fingerprintSource` (`can` no replay porque nao passa pelo
card.py; `fw` no log) e `carVin`.
`useSteeringAngle=True` e a UNICA via que restou no upstream
(`latcontrol_torque.py` em `09aa21390` usa sempre
`VM.calc_curvature(steeringAngleDeg...)`; `20fdb686c` removeu o ramo do
localizer) -> comportamento identico.

### 3.4 carstate.py (City: `cp` = bus 0, `cp_cam` = bus 2, sem `cp_body`)
Lista estatica da v0.9.9 (`get_can_messages` + `cam`): `ENGINE_DATA 0x158
100`, `POWERTRAIN_DATA 0x17C 100`, `STEERING_SENSORS 0x14A 100`, `STEER_STATUS
0x18F 100`, `GEARBOX 0x191 100`, `WHEEL_SPEEDS 0x1D0 50`, `VSA_STATUS 0x1A4
50`, `STEER_MOTOR_TORQUE 0x1AB 0`, `CRUISE_FAULT_STATUS 0x1D3 50`,
`SCM_BUTTONS 0x296 25`, `SEATBELT_STATUS 0x305 10`, `CRUISE 0x324 10`,
`CAR_SPEED 0x309 10`, `SCM_FEEDBACK 0x326 10`; cam: `STEERING_CONTROL 0xE4
100`, `ACC_HUD 0x30C 10`, `LKAS_HUD 0x33D 10`. Todas presentes na rota nas
taxas (secao 5). Replay: todos os campos de `carState` identicos entre HEAD e
upstream (0 diffs em 33 campos) exceto `gas` (HEAD publica PEDAL_GAS; upstream
removeu o campo) e `steeringTorqueEps` (HEAD le 0x1AB `MOTOR_TORQUE`;
upstream nao le) - D-5. `vEgoRaw` difere so por ruido float (<=1e-5, 136
amostras; `np.mean` vs media manual).
Gear: HEAD `GEARBOX.GEAR_SHIFTER` (byte0) -> `shifter_values` {1 P,2 R,4 N,
8 D,16 S,32 L}; upstream `GEARBOX_CVT.GEAR_SHIFTER` (byte5 bits 4..0) ->
{1 P,2 R,3 N,4 D,7 L,10 S}. Ver D-1.
`doorOpen`: HEAD `SCM_FEEDBACK.DRIVERS_DOOR_OPEN`; upstream idem (confirmado
que `SCM_BUTTONS` upstream nao tem `DRIVERS_DOOR_OPEN`). `parkingBrake`: so
com `HAS_EPB` (ausente) -> False nos dois lados.

### 3.5 hondacan.py / carcontroller.py
`CanBus` radarless: `pt=0`, `radar=1`, `camera=2` (Bosch B no black panda:
CAN1 = carro, CAN3 = camera). `create_steering_control`,
`create_acc_commands` (radarless: `ACC_CONTROL 0x1C8` a cada 2 frames,
`ACC_HUD 0x30C` a cada 10), `create_ui_commands` (`LKAS_HUD 0x33D`),
`spam_buttons_command` (`0x296` bus 2): quadros identicos byte a byte no
replay (counter e checksum inclusos). Unicas diferencas textuais: rename
`SET_ME_X48` -> `LDW_OFF`+`SET_ME_X1` (0x48 = bits 30 e 27 - mesmos bytes) e
`get_cruise_speed_conversion` -> `CS.v_cruise_factor`.
Arredondamento do packer: C++ `round()` (half away from zero) vs upstream
`floor(x+0.5)` - difere so em -x.5 exato; nenhum quadro da rota foi afetado.

### 3.6 interfaces.py / lateral.py / override.toml
`"HONDA_CITY_7G" = [1.2, 1.2, 0.23]` identico. `torque_from_lateral_accel_
linear` (v0.9.9: friccao em torque) vs upstream (`get_friction` em
`lateral.py` multiplica por `latAccelFactor`, e `latcontrol_torque` divide a
saida do PID por `latAccelFactor`): algebricamente iguais para o modelo
linear; ver D-3 para o que NAO e igual (pid.py).

---------------------------------------------------------------------------

## 4. Area 2 - DBC `honda_civic_ex_2022_can_generated.dbc`

Comparacao HEAD vs upstream (`%TEMP%\audit2_dbc\cmp_head_up43.txt`,
reproduzivel com `a2_gen_dbcs.py` + `a2_dbc_compare.py`):

- Mensagens usadas pelo City (RX e TX): `0x158, 0x17C, 0x14A, 0x18F, 0x1D0,
  0x1A4, 0x1AB, 0x1D3, 0x296, 0x305, 0x324, 0x309, 0x326, 0xE4, 0x30C, 0x33D,
  0x1C8`: todos os sinais lidos/escritos com mesmo id, dlc, start bit,
  tamanho, ordem (big-endian), sinal, fator, offset. Diferencas apenas em
  nomes (`SET_ME_X48` vs `LDW_OFF`/`SET_ME_X1` em 0x33D) e em sinais nao
  usados (0x326 ganha `REVERSE_LIGHT`/`PARKING_BRAKE_ON`; 0x1B0 `STANDSTILL`
  range; 0x221 rename; 0x372 so na v0.9.9; 0x1FA so no upstream; 0x1A3 so na
  v0.9.9 - ausente na rota).
- **0x191**: layout diferente (D-1). Checksum/counter nas mesmas posicoes
  (59|4, 61|2) nos dois.
- TX: alem do packer proprio do primeiro auditor, esta auditoria usou o
  packer REAL de cada arvore via replay (secao 5.3): 0 diferencas.

---------------------------------------------------------------------------

## 5. Area 3 - Evidencia da rota (rlog upstream, comma three + Bosch B)

### 5.1 Inventario (bus 0 = carro, bus 2 = camera; bus 1 vazio)
`0x158 99.96 Hz`, `0x17C 99.98`, `0x14A 99.95`, `0x18F 99.95 (dlc 7)`,
`0x191 99.96`, `0x1D0 49.88`, `0x1A4 49.88`, `0x1AB 49.95 (dlc 3)`, `0x1D3
50.01`, `0x296 24.99 (dlc 4)`, `0x305 10.0 (dlc 7)`, `0x324 10.0`, `0x309
10.0`, `0x326 10.0`; bus 2: `0xE4 99.93`, `0x1C8 49.97`, `0x30C`/`0x33D`
(os do openpilot aparecem em `sendcan`, no `can` do bus 2 ficam os da camera
bloqueados pelo rele). Ausentes no bus 0: `0x1C2` (EPB), `0x1A3`, `0x1BE`,
`0x1FA`, `0x1DF`, `0x372`, `0x33DA/0x33DB`, BSM. 0 falhas de checksum nos
parsers das duas arvores. O parser C++ da v0.9.9 (`parser.cc`): timeout por
mensagem = 10x o periodo declarado; frequencia 0 (0x1AB) = sem timeout; o
black panda numera os buses igual ao comma three (0 carro / 2 camera via
harness Bosch B).

### 5.2 pandaStates
611 amostras: `('tres', 'hondaBosch', 10, altExp 0, harness normal,
controlsAllowed True) x521`, `(... hondaBosch, 10, ..., False) x19`,
`elm327 x71` (antes do onroad). `carParams.safetyConfigs = [hondaBosch, 10]`,
`alternativeExperience = 0`. O openpilot v0.9.9 aplica exatamente isso via
`panda_safety.cc` (`set_safety_model(model, param)` + `set_alternative_
experience`), sem transformacao.

### 5.3 Replay (codigo real; `%TEMP%\city_rlog\replay_compare.txt`)
- CarParams HEAD vs upstream: 95 chaves, 2 diffs (ambas o rename de
  `useSteeringAngle`).
- CarState HEAD vs upstream (mesmo CAN): 0 diffs em 33 campos; `gas`
  5540 diffs, `steeringTorqueEps` 205 diffs (D-5), `vEgoRaw` ruido float.
- CarState HEAD vs carState GRAVADO pelo upstream (janela de 4 amostras):
  campos discretos (`gearShifter`, `cruiseState.*`, `brakePressed`,
  `blinkers`, `doorOpen`, `steerFault*`, `accFaulted`, `canValid`) iguais
  apos a inicializacao (os unicos mismatches estao nas primeiras amostras,
  antes do parser do carro ter todas as mensagens, e em `seatbeltUnlatched`/
  `cruiseState.available` nos 9 primeiros ciclos pelo mesmo motivo).
- TX HEAD vs upstream (mesmo `carControl`, mesma cadencia): `0xE4 5410/5410`,
  `0x1C8 2705/2705`, `0x30C 541/541`, `0x33D 541/541` identicos.
- TX vs `sendcan` gravado: as duas arvores produzem EXATAMENTE as mesmas
  estatisticas (`0x30C`/`0x33D` 100 % iguais; `0x1C8` 2658/2705, 47
  explicados por jitter de 1 ciclo do `carControl`; `0xE4` 4949/5410, 461
  residuais com o MESMO padrao nas duas arvores = artefato de agendamento do
  harness - o rate limiter de torque depende do instante exato em que o
  `carControl` chega ao card.py, que nao esta no log). Logo: nenhum residual
  e atribuivel ao port.

### 5.4 GEARBOX 0x191 (6116 quadros bus 0)
byte0 = 0x08 em 100 %; byte5 = 0x24 em 100 % (bits 4..0 = 4 = D,
`SHIFTER_POSITION_VALID` = 1, `SELECTED_D` = 1). HEAD -> `drive` 100 %;
upstream -> `drive` 100 %. DBC corrigido pelo patch 0001 -> `drive` 100 %,
layout e VAL_ identicos ao `GEARBOX_CVT` upstream (verificado por cantools).

---------------------------------------------------------------------------

## 6. Area 4 - Safety e firmware do panda

### 6.1 opendbc/safety (compilado no firmware do black panda)
`git diff HEAD 43006b9a -- opendbc/safety/modes/honda.h safety.h
safety_declarations.h board/can_declarations.h tests/test_honda.py`:
refatoracao pura (`GET_BYTE` -> `msg->data[]`, campo `frequency` posicional
na `CanMsgCheck`, `bus` unsigned, modo PSA, param `BOSCH_CANFD=16`). Para
`hondaBosch` param 10 (e 8):
- RX: `HONDA_COMMON_RX_CHECKS(0)` = `0x1A6/0x296 bus 0 25 Hz`, `0x158 100`,
  `0x17C 100`, `0x326 10`, `max_counter 3`, `ignore_quality_flag`;
  `+0x1BE 50 Hz` so com `ALT_BRAKE` (nao e o caso). Identico.
- TX: `HONDA_RADARLESS_LONG_TX_MSGS = {0xE4,0,5},{0x33D,0,8},{0x1C8,0,8},
  {0x30C,0,8}` (param 10) / `HONDA_RADARLESS_TX_MSGS = {0xE4,0,5},
  {0x296,2,4},{0x33D,0,8}` (param 8). Identicos (addr/bus/len).
- Torque: `HONDA_STEERING_LIMITS` (Bosch: steer so com `controls_allowed`,
  sem rate limit no firmware), `HONDA_BOSCH_LONG_LIMITS` (`max_accel 200`,
  `min_accel -350`, `max_gas 2000`, `inactive_gas -30000`), botoes (`0x296`
  TX so com `!controls_allowed`), gas/brake cancel, `honda_fwd_hook`, rele,
  heartbeat (`safety.h`): sem mudanca de logica.
- `test_honda.py`: so renames e novas classes CAN-FD; a cobertura radarless
  (`...RadarlessSafetyBase`, `...AltBrake`, `...Long`) e a mesma.

### 6.2 Firmware panda `e462c34d` vs `3dc21386` (27 commits)
- `3d272335` "Deprecate white and black pandas" e `1020d355` (uno/grey):
  upstream APAGOU `board/boards/black.h` -> `e462c34d` e o ultimo firmware
  que compila para o black panda. A escolha do fork e portanto obrigatoria.
- `board/drivers/bxcan.h`, `llbxcan.h` (driver CAN classico do F4): fora do
  diff -> identicos.
- Demais: remocao de `has_harness` (todos os boards restantes tem harness),
  ADC generico, rename `spi_checksum_error_count_pkt` ->
  `spi_error_count_pkt` (mesmo tamanho em `health_t`; o `pandad.cc` da v0.9.9
  usa o nome antigo = struct do `e462c34d`, coerente), remocao dos endpoints
  UART `0xe1/0xe2/0xe4/0xf2`, gating CAN-FD em `0xf9/0xfc`, "Tie CAN0 and CAN2
  enable lines" (H7). Classificacao: F4-irrelevante ou H7-only; **nenhum
  item "relevante e faltando"**.
- `black.h` em `e462c34d`: `has_harness=true`, `has_canfd=false`,
  `has_spi=false`, CAN3 em A8/A15 (camera), CAN2 chaveado por harness
  flipped - caminho do Bosch B coberto.
- `python/__init__.py` upstream: `DEPRECATED_DEVICES` (white/black) recusa
  flash; irrelevante porque o fork usa o python do submodule `e462c34d`.
- USB usados pelo `pandad` v0.9.9 (`panda.cc`: `0xdc` safety, `0xdf`
  alternative experience, `0xf3` heartbeat, `0xd2` health, `0xc2` can health,
  `0xc1` hw type, `0xd0` serial, `0xd3/0xd4` assinatura do fw, `0xde/0xf9/0xfc`
  velocidade CAN, `0xe7` power saving, `0xe8` enable bus, `0xc0` can reset,
  `0xb0/0xb1/0xb2` IR/fan, `0xe0` leitura de bulk, `0xe4/0xe5` uart/loopback):
  todos existem em `board/main_comms.h` de `e462c34d`; `0xfb` (deepsleep)
  nao existe em `e462c34d` nem em `3dc21386` (ignorado nos dois). O `pandad`
  v0.9.9 nao usa `0xdb` (multiplexacao OBD e feita por `ELM327` param 1).

---------------------------------------------------------------------------

## 7. Area 5 - openpilot v0.9.9 (fork `89df27131`) vs upstream `09aa21390`

Diff do fork vs v0.9.9 (`git diff 8aadf02b 89df27131`): `.github/workflows/
selfdrive_tests.yaml` (skip `build_release` em forks), `.gitmodules` (url
do opendbc -> fork), `README.md`, `RELEASES.md`, `docs/CARS.md` (+1 linha
City, "313 Supported Cars"), `selfdrive/car/car_specific.py` (1 linha:
`extra_gears=[GearShifter.sport]` para honda = hunk de `bae7a610f`),
`uv.lock` (**somente** o hash sha256 do wheel `metadrive_simulator-0.4.2.4`,
1 linha), gitlink `opendbc_repo`.

Diff upstream `8aadf02b..09aa21390` relevante para um Bosch radarless:

| Mudanca upstream | Afeta o City? | No fork | Classificacao |
|---|---|---|---|
| `bae7a610f` sport gear Honda | sim (CVT com S) | aplicado (`c3e422ae9`), identico | paridade |
| `839a77334` torqued Honda | sim (aprendizado LAF/friction) | nao aplicado | D-2, divergencia consciente; patch 0003 |
| `ab44c9a4f`+`455a6a586`+`bc7d6f267`+`20fdb686c` latcontrol_torque em espaco de accel + pid.py | sim (todo carro torque) | nao (v0.9.9) | D-3, plataforma; ganhos equivalentes no modelo linear; anti-windup difere |
| `pandad.cc`: rele para NO_OUTPUT quando `!IsOnroad` (alem de ignicao off), IR, `spi_error_count` | nao especifico do City/black panda | nao | plataforma |
| `pandad.py`: janela de espera do panda interno 35 s -> 60 s | so comma three interno | nao | irrelevante (black panda e USB externo) |
| `selfdrived`/`events`/`helpers`/`longitudinal_planner` | genericos (todas as marcas) | nao | plataforma |
| `card.py` `params.get` sem encoding | nao | nao | cosmetica |
| `lagd` fora do shadow em release (`44c8cc4cb`) | nao (branch nao e release) | nao | irrelevante |

`parkingBrake`/`HAS_EPB`: City sem 0x1C2 -> False nos dois lados; a
`selfdrived` v0.9.9 so usa `parkingBrake` para o evento `parkBrake`.
`PandaType.blackPanda`: `pandad.cc` v0.9.9 so distingue `DOS`/`RED_PANDA`
(comma three + red panda); o black panda cai no caminho generico USB, igual
ao que a v0.9.9 fazia em producao para ele.

---------------------------------------------------------------------------

## 8. Tabela de afirmacoes do primeiro relatorio

| # | Afirmacao (../auditoria-port-city-v099.md) | Veredito | Evidencia desta auditoria |
|---|---|---|---|
| 1 | D1: `steerActuatorDelay` 0.15 so apos `d42db044` | CONFIRMADO | replay `get_params` HEAD = 0.15 = carParams da rota |
| 2 | D2: `ki = 0.3` efetivo para o City; default global 0.1 nao muda outras marcas | CONFIRMADO | `interface.py` l.~150 `ret.lateralTuning.torque.ki = 0.3` apos `configure_torque_tune`; replay ki 0.3; `interfaces.py` igual a `e370a036` |
| 3 | D3: `bae7a610f` aplicado verbatim | CONFIRMADO | hunk identico em `car_specific.py` l.60 |
| 4 | Bloco de fingerprints identico byte a byte | CONFIRMADO | comparacao de string do bloco: True |
| 5 | `FW_QUERY_CONFIG` identico salvo CAN-FD; match exato so exige `fwdRadar` | CONFIRMADO | diff + carFw da rota (1 entrada) |
| 6 | Lista de mensagens/taxas v0.9.9 e todas presentes na rota | CONFIRMADO | scan1: taxas 99.9/49.9/25/10 Hz, 0 falhas de checksum |
| 7 | 0x1AB freq 0 => sem timeout; `steeringTorqueEps` sem consumidor | CONFIRMADO | `git grep steeringTorqueEps` -> so `tools/plotjuggler/layouts/tuning.xml` |
| 8 | GEARBOX P/R/N/D equivalentes; S/L nao verificaveis | CONFIRMADO (e tratado como D-1 com patch) | 6116/6116 quadros D nos dois layouts; nenhum S/L na rota |
| 9 | Sinais RX usados: mesmo bit/fator/offset | CONFIRMADO (mais forte) | replay com codigo real: 0 diffs em 33 campos de carState |
| 10 | TX identicos (1036 quadros, packer proprio) | CONFIRMADO (mais forte) | 9197 quadros com os packers reais das duas arvores: 0 diffs; `0x30C`/`0x33D` 100 % iguais ao sendcan gravado |
| 11 | Safety RX/TX/limites identicos para RADARLESS(+BOSCH_LONG) | CONFIRMADO | secao 6.1 |
| 12 | Nenhum commit de safety a retroportar | CONFIRMADO | diff honda.h/safety.h = refactor |
| 13 | CarParams: 80 iguais / 2 explicadas | CONFIRMADO | replay: 95 chaves, so `useSteeringAngle` + campos do card.py |
| 14 | `useSteeringAngle=True` == comportamento upstream | CONFIRMADO | `latcontrol_torque.py` upstream so tem o ramo do angulo |
| 15 | "`common/pid.py` e identico entre v0.9.9 e `09aa21390`" | **REFUTADO** | `git diff 8aadf02b 09aa21390 -- common/pid.py`: 13+/19- (`455a6a586`): anti-windup `i_upper/lowerbound` vs clip de `control_no_i`; `override`/`i_unwind_rate`/`error_integral` removidos; `set_limits`. Consequencia: D-3 (plataforma) |
| 16 | Erro do PID em torque (v0.9.9) equivale a erro em accel (upstream) com friccao `* latAccelFactor` | CONFIRMADO (so para o termo linear) | `lateral.py` upstream `get_friction` multiplica por LAF; `torque_from_lateral_accel_linear` divide por LAF; integrador em espacos diferentes muda apenas quando LAF muda ao vivo (torqued, desligado no fork) |
| 17 | `torqued` Honda nao aplicado, divergencia residual | CONFIRMADO | `ALLOWED_CARS = ['toyota','hyundai','rivian']` no fork; `+ 'honda'` em `09aa21390` (`839a77334`, 2025-08-06) |
| 18 | "`pandad`: mudancas de SPI/CAN-FD, sem efeito no black panda USB" | **REFUTADO** (parcial) | `pandad.cc` tambem muda a logica de rele (`should_close_relay = !ignition || !is_onroad`), IR e `spi_error_count`; nenhum e especifico de black panda nem muda o comportamento onroad com ignicao ligada -> plataforma, nao bloqueante |
| 19 | `HAS_EPB`/`parkingBrake` False nos dois lados | CONFIRMADO | 0x1C2 ausente; replay `parkingBrake` 0 diffs |
| 20 | `deinit` so para Bosch com radar | CONFIRMADO | `init()` upstream condicionado a `HONDA_BOSCH - HONDA_BOSCH_RADARLESS` |
| 21 | Process replay do fork nao muda para Civic/Accord por D1/D2 | NAO VERIFICAVEL aqui | depende do CI do fork (nao roda no Windows); logica plausivel (so City usa torque tune entre as Hondas da v0.9.9: confirmado por leitura do `interface.py`) |
| 22 | `uv.lock` so muda o hash do metadrive | CONFIRMADO | diff de 1 linha (sha256 `fbf0ea9b...` -> `d0afaf3b...`) |
| 23 | `ruff` pin nao faz parte do port | CONFIRMADO, mas introduziu CRLF | D-4 |
| 24 | Nomes `SET_ME_X48` vs `LDW_OFF`+`SET_ME_X1`: mesmos bytes | CONFIRMADO | replay 0x33D 541/541; 0x48 = bits 30 e 27 |
| 25 | `honda_checksum` python == C++ v0.9.9 | CONFIRMADO | 0 falhas de checksum RX e counters/checksums TX identicos no replay |
| 26 | Parser estatico == dinamico no conjunto de mensagens | CONFIRMADO | upstream acessa o mesmo conjunto para o City; `canValid` igual no replay |
| 27 | "Em L o upstream gera `wrongGear`" | CONFIRMADO | `extra_gears=[GearShifter.sport]` apenas |
| 28 | `e462c34d` e o ultimo firmware com black panda | CONFIRMADO | `3d272335` apaga `black.h` |
| 29 | Nada testado no carro | CONFIRMADO | idem aqui |

---------------------------------------------------------------------------

## 9. Divergencias e patches propostos (`audit2\proposed-patches\`)

| # | Severidade | Arquivo | Patch | `git apply --check` |
|---|---|---|---|---|
| D-1 | funcional (risco) | opendbc `opendbc/dbc/generator/honda/honda_civic_ex_2022_can.dbc` | `0001-honda-civic-ex-2022-gearbox-cvt-layout.patch` - troca o layout de BO_ 401 pelo `GEARBOX_CVT` upstream (9ef0b1fb) mantendo o nome `GEARBOX` (carstate.py intocado); remove `VAL_ 401 GEAR`; checksum/counter inalterados. Afeta tambem `HONDA_HRV_3G` (mesmo DBC, mesmo 0x191 - o upstream decodifica o HR-V 3G do mesmo jeito). Apos aplicar: regenerar `opendbc/dbc/honda_civic_ex_2022_can_generated.dbc` e rodar `test_models` do City e do HR-V 3G no CI. | OK (HEAD `052a515f`) |
| D-2 | funcional (consciente) | openpilot `selfdrive/locationd/torqued.py` | `0003-openpilot-torqued-allow-honda.patch` (1 linha; opcional, exige regenerar refs de process replay do torqued) | OK (HEAD `89df27131`) |
| D-3 | funcional (plataforma) | openpilot `common/pid.py`, `latcontrol_torque.py` | sem patch: portar `ab44c9a4f`/`455a6a586` muda todos os carros torque da v0.9.9 e os refs de process replay; divergencia de plataforma a registrar | - |
| D-4 | cosmetica | opendbc `pyproject.toml` | `0002-opendbc-pyproject-restore-lf.patch` (CRLF -> LF; `git apply --whitespace=nowarn` neste clone, que tem `core.autocrlf=true`) | OK |
| D-5 | cosmetica | opendbc `carstate.py` | sem patch (campos extras sem consumidor; remover `gas`/`steeringTorqueEps` quebraria `car.capnp` da v0.9.9 por nada) | - |
| D-6 | cosmetica | opendbc `values.py` | sem patch (sem efeito) | - |

Scripts desta auditoria (`audit2\`): `a2_common.py`, `a2_gen_dbcs.py`,
`a2_dbc_compare.py`, `a2_scan1_inventory.py`, `a2_dump_rlog.py`,
`a2_v099_shim.py`, `a2_replay.py`, `a2_replay_compare.py`,
`a2_crlf_check.py`, `a2_make_gearbox_patch.py`, `a2_make_misc_patches.py`.
Para re-executar o replay e preciso recriar os worktrees
(`git worktree add %TEMP%\audit2_wt\up43 43006b9a`) e os DBCs gerados
(`a2_gen_dbcs.py`), que foram removidos na limpeza.

---------------------------------------------------------------------------

## 10. O que NAO pode ser verificado sem hardware / dados de estrada

1. Posicoes P/R/N/S/L de `GEARBOX` 0x191 no City: a rota so contem D (byte0
   0x08 / byte5 0x24 constantes). O patch 0001 reproduz a decodificacao do
   upstream, mas o upstream tambem so a validou com as rotas que tinha.
2. Comportamento em S/L sem o patch (drive vs unknown/wrongGear).
3. EPB: o City da rota nao emite 0x1C2; se alguma versao emitir, `HAS_EPB`
   e o `EPB_STATUS` portado em `07add98b` passam a ser usados sem rota de
   referencia.
4. Temporizacao real do bxCAN do black panda com o trafego do City (buffers,
   rele, `canRxErrs`): o rlog e de um comma three (red panda H7); so o
   firmware e o safety sao iguais por construcao.
5. Residual de 0xE4 vs `sendcan` (356 ciclos com torque diferente nas DUAS
   arvores): atribuido ao agendamento do harness; nao prova nada sobre o
   port, mas tambem nao e reproduzivel sem o instante exato do `carControl`.
6. `test_models`, process replay e compilacao do firmware/libsafety: nao
   rodam no Windows; dependem do CI do fork (verde segundo o LEIA-ME; nao
   re-executado aqui).
7. Qualquer efeito de D-3 (anti-windup do PID) na pista: so com dados do
   carro.

## 11. Fechamento (HEAD b4125fe6 / e841f3cc3)

Passagem final apos o dono aplicar os tres patches propostos em 7.
Mesmo metodo da secao 2 (worktrees, DBCs regenerados, replay com o codigo
real de cada arvore sobre o rlog da rota CI do City). CI run 40525385443
estava em andamento no momento desta passagem e NAO foi consultado aqui.

### 11.1 Identidade dos HEADs auditados

- opendbc fork `firmwarecityg7-v0.9.9`: `b4125fe6` "honda: backport
  GEARBOX_CVT layout for radarless Bosch (audit2 D-1)" sobre `052a515f`.
  `git show --stat`: apenas `opendbc/dbc/generator/honda/honda_civic_ex_2022_can.dbc`
  (+12/-11) e `pyproject.toml` (266 linhas, so terminador de linha).
  `git apply --check --reverse` dos patches 0001 e 0002 contra `b4125fe6`:
  exit 0 para ambos -> o conteudo commitado e exatamente o resultado dos
  patches (o dono reescreveu a mensagem do commit, nao o diff).
- openpilot fork `v0.9.9-cityg7-blackpanda`: `8be62bc95` (torqued, 1 linha)
  e `e841f3cc3` (gitlink `opendbc_repo` 052a515f -> b4125fe6). `ls-tree`:
  opendbc_repo = b4125fe6, panda = e462c34d (inalterado).
- Nenhum `*_generated.dbc` e versionado no v0.9.9 (0 arquivos em
  `opendbc/dbc/`); o DBC e gerado no build, logo o commit do gerador basta.
- Working trees: ambos os clones mostram `README.md` modificado e NAO
  commitado (nota de fork do dono, +26 e +29/-10 linhas). Nao e meu; nao
  faz parte dos HEADs auditados.

### 11.2 Check 1 - replay nas novas arvores (a2_gen_dbcs / a2_replay / a2_replay_compare)

Worktrees `%TEMP%\audit2_wt\head` (b4125fe6) e `%TEMP%\audit2_wt\up43`
(43006b9a); DBCs regenerados em `%TEMP%\audit2_dbc\{head,up43}` (18 e 17
arquivos honda).

| Item | head b4125fe6 | up43 43006b9a | Resultado |
|---|---|---|---|
| TX 0xE4 STEERING_CONTROL | 5410 | 5410 | 5410/5410 identicos (payload, counter, checksum) |
| TX 0x1C8 BOSCH_SUPPLEMENTAL_1 | 2705 | 2705 | 2705/2705 identicos |
| TX 0x30C ACC_HUD | 541 | 541 | 541/541 identicos |
| TX 0x33D LKAS_HUD | 541 | 541 | 541/541 identicos |
| TX vs sendcan logado | 0xE4 4949/5410, 0x1C8 2658/2705, 0x30C 541/541, 0x33D 541/541 | identico | igual nas duas arvores (artefato de agendamento do harness, secao 2.4) |
| carState campos comuns | 33 campos | | 0 diffs |
| carState `gearShifter` | `drive` 100% | `drive` 100% | 0 diffs (antes do patch ja era 0 por coincidencia em D; agora o layout e o mesmo) |
| carState `gas` / `steeringTorqueEps` | presentes | ausentes no capnp upstream | 5540 / 205 "diffs" = campo so existe no v0.9.9 (igual secao 2.3) |
| carState `vEgoRaw` | | | 136 diffs <= 1e-5 (float32 vs float64) |
| carParams get_params head vs up43 | 95 chaves | | 2 diffs: `useSteeringAngle` vs `useSteeringAngleDEPRECATED` (rename de campo, mesmo valor logico: upstream usa sempre angulo) |
| carParams head vs carParams logado na rota | | | 3 diffs: `carVin` (ausente no replay), `fingerprintSource` can/fw (replay sem FW query), `useSteeringAngle` True vs False (rename; ver 2.2) |
| Excecoes em `apply`/`update` | 0 | 0 | |

Nota: a lista "esperada" do dono dizia "apenas HAS_EPB e campos de
plataforma"; o `HAS_EPB` NAO aparece como diff aqui porque o rlog do City
nao tem 0x1C2 e o replay calcula `flags` por fingerprint nas duas arvores
(ambas resultam sem HAS_EPB). O unico diff de carParams continua sendo o
rename `useSteeringAngle`, como na secao 2.2. Sem regressao em relacao a
passagem anterior; nenhum numero piorou.

### 11.3 Check 2 - DBC estrutural BO_ 401 e caminho de codigo HRV_3G / CIVIC_2022

`a2_dbc_compare.py head/honda_civic_ex_2022_can_generated.dbc up43/honda_civic_ex_2022_can_generated.dbc`
(no 43006b9a o arquivo ainda tem esse nome; o rename para
`honda_bosch_radarless_generated.dbc` e posterior e nao muda o conteudo
de BO_ 401):

- 0x191: UNICO diff = nome da mensagem `GEARBOX` -> `GEARBOX_CVT`
  (intencional; carstate do v0.9.9 referencia "GEARBOX"). Todos os 13
  sinais (SELECTED_P/R/N/D, FORWARD_DRIVING_MODE, CVT_UNKNOWN_1/2/3,
  GEAR_SHIFTER 44|5@0+, SHIFTER_POSITION_VALID, NOT_FORWARD_GEAR,
  CHECKSUM 59|4, COUNTER 61|2) e a VAL_ `1 P 2 R 3 N 4 D 7 L 10 S` sao
  byte-identicos ao `_gearbox_common.dbc` upstream (conferido tambem por
  `git show 43006b9a:opendbc/dbc/generator/honda/_gearbox_common.dbc`).
- Total de diffs do arquivo: 47, USED(City)=0. Todos os 47 restantes sao
  0x1A3 (`GEARBOX_ALT` v0.9.9 vs `GEARBOX_AUTO` upstream: GEAR_SHIFTER
  29|6 VAL 32 D/16 N/8 R/4 P/0 B vs 35|4 VAL 1 P/2 R/3 N/4 D, mais sinais
  REGEN_*/TRANS_* so no upstream) e outras mensagens fora do caminho do
  City, ja listadas na secao 3.

Consistencia dos tres carros que usam este DBC (carstate.py b4125fe6
l.83-96 vs upstream 43006b9a):

| Carro | v0.9.9: transmissionType -> gearbox_msg | upstream 43006b9a | Mesmo frame/layout? |
|---|---|---|---|
| HONDA_CITY_7G | cvt (0x191 no fingerprint) -> "GEARBOX" (0x191) | 0x191 presente -> cvt -> "GEARBOX_CVT" (0x191) | SIM (apos b4125fe6) |
| HONDA_HRV_3G | default automatic -> "GEARBOX" (0x191) | 0x191 presente -> cvt -> "GEARBOX_CVT" (0x191) | SIM (mesmo 0x191, mesmo layout; so o enum transmissionType difere: automatic vs cvt, sem efeito em `gearShifter`) |
| HONDA_CIVIC_2022 | 0x1A3 presente -> cvt -> "GEARBOX_ALT" (0x1A3, layout antigo) ; sem 0x191/0x1A3 -> manual -> "GEARBOX_ALT_2" | 0x1A3 sem 0x191 -> automatic -> "GEARBOX_AUTO" (0x1A3, layout novo 35|4) | NAO: 0x1A3 segue com o layout pre-43006b9a no fork. Divergencia de plataforma do Civic 2022, fora do escopo City (nao toca 0x191). |

Ou seja: para os dois carros que leem 0x191 (City e HR-V 3G) o patch
deixa o fork igual ao upstream; o Civic 2022 le 0x1A3 e continua com a
definicao antiga do v0.9.9 (registrado como plataforma, abaixo).

### 11.4 Check 3 - torqued.py

- `git show 8be62bc95 -- selfdrive/locationd/torqued.py` vs
  `git show 839a77334 -- selfdrive/locationd/torqued.py` (hardware/reference):
  as linhas +/- sao identicas (`ALLOWED_CARS = ['toyota', 'hyundai',
  'rivian']` -> `[..., 'honda']`). Restante do arquivo vs upstream
  09aa21390: so 2 mudancas nao relacionadas (import de
  ACCELERATION_DUE_TO_GRAVITY movido para `openpilot.common.constants` e
  `liveTorqueParameters.calPerc`, campo que nao existe no cereal v0.9.9).
- `a2_closing_lattune.py` (CarInterface.get_params real na arvore
  b4125fe6, com `self.use_params = CP.brand in ALLOWED_CARS and
  CP.lateralTuning.which() == 'torque'` do torqued v0.9.9):

| Plataforma | brand | lateralTuning.which() | torqued.use_params |
|---|---|---|---|
| HONDA_CITY_7G | honda | torque (kp=1.0 ki=0.3 friction=0.23 latAccelFactor=1.2) | True |
| HONDA_ACCORD | honda | pid | False |
| HONDA_CIVIC | honda | pid | False |

Logo os segmentos de process-replay (Civic Nidec, Accord Bosch) nao
mudam de comportamento com D-2; so o City passa a ter `useParams=True`
como no upstream.

### 11.5 Check 4 - CRLF

`a2_crlf_check.py` sobre e370a036..b4125fe6 e 8aadf02b..e841f3cc3: nenhum
arquivo com CRLF>0 (lista completa de 24 arquivos tocados, todos
CRLF=0). `pyproject.toml`: HEAD CRLF=0 LF=133, base CRLF=0 LF=133.
D-4 fechado.

### 11.6 Tabela final D-1..D-6

| ID | Achado | Status |
|---|---|---|
| D-1 | BO_ 401 GEARBOX layout v0.9.9 (byte0 one-hot) vs upstream GEARBOX_CVT (byte5) -> S/L decodificam diferente | fechado em b4125fe6 (opendbc) + e841f3cc3 (gitlink); replay: gearShifter 0 diffs, estrutura 0x191 identica |
| D-2 | torqued.py sem 'honda' em ALLOWED_CARS (upstream 839a77334) | fechado em 8be62bc95; use_params True so para o City |
| D-3 | common/pid.py anti-windup 455a6a586 ausente no v0.9.9 (latcontrol_torque) | registrado - divergencia de plataforma (todos os carros torque do v0.9.9); nao e bug do port; sem acao proposta |
| D-4 | pyproject.toml reescrito em CRLF por 5f439d78 | fechado em b4125fe6 |
| D-5 | HondaBoschPlatformConfig sem @dataclass (igual a base e370a036) | sem acao (sem efeito funcional; herdado) |
| D-6 | pandad.cc relay/IsOnroad e demais mudancas de pandad v0.9.9..09aa21390 | sem acao (comportamento do v0.9.9 para todos os carros; firmware e safety identicos) |

### 11.7 Divergencias de plataforma remanescentes (NAO sao bugs do City)

Comportam-se igual para todos os carros do v0.9.9; o City herda o que
qualquer Honda Bosch radarless herdaria se o v0.9.9 o suportasse:

1. `common/pid.py` sem anti-windup (D-3) e `latcontrol_torque` do v0.9.9
   (secao 6.2) vs upstream 09aa21390.
2. `selfdrive/pandad/pandad.cc`: rele/`IsOnroad`, SPI, CAN-FD (D-6).
3. `selfdrived`/events/planner/controlsd genericos entre v0.9.9 e
   09aa21390 (secao 6).
4. Parser CAN: C++ estatico (v0.9.9) vs Python dinamico (upstream);
   timeouts e `canValid` conforme secao 3.2.
5. carState com campos extra `gas`, `steeringTorqueEps` (capnp v0.9.9).
6. ki global torque 0.1 (v0.9.9) vs 0.3 (upstream fb5ac6d3): City
   ajustado para 0.3 em 052a515f; demais carros torque do v0.9.9 ficam
   em 0.1 por decisao do port.
7. 0x1A3 GEARBOX_ALT (Civic 2022 CVT) com layout pre-43006b9a; e o
   enum `transmissionType` do HR-V 3G = automatic (upstream: cvt).
   Nenhum dos dois toca o City.
8. `useSteeringAngle` (v0.9.9, True) vs `useSteeringAngleDEPRECATED`
   (upstream, sempre angulo): rename de campo, mesmo efeito.

### 11.8 O que falhou / regrediu

Nada regrediu em relacao a secao 2: todos os contadores TX, checksums,
counters, campos de carState e carParams reproduzem os numeros
anteriores; `gearShifter` continua 0 diffs e agora pela mesma
definicao de sinal. Nenhum check desta passagem falhou. Permanecem as
limitacoes da secao 10 (nenhum teste de hardware, CI 40525385443 nao
consultado, `test_models`/process-replay nao executaveis no Windows).

Artefatos desta passagem: `audit2\a2_closing_lattune.py`;
`%TEMP%\city_rlog\{replay_head.json, replay_up43.json, replay_compare.txt}`
(regenerados). Worktrees `%TEMP%\audit2_wt\*` e `%TEMP%\audit2_dbc`
removidos ao final; `%TEMP%\city_rlog` mantido.
