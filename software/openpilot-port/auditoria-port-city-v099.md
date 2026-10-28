# Auditoria do port Honda City G7 2023 (BR) para openpilot v0.9.9 / black panda

Data: 2026-10-28. Escopo: tudo que o City usa no upstream commaai/opendbc
`43006b9a` ("Honda: Honda City (Brazil only) 2023 (#2425)", 2025-08-19) precisa
se comportar identicamente no branch `firmwarecityg7-v0.9.9` (base
`e370a036` = opendbc da v0.9.9) e no openpilot `v0.9.9-cityg7-blackpanda`.

Aviso honesto: nada aqui foi testado no carro. Todas as evidencias sao de
codigo, DBC gerado, firmware de seguranca lido, e do rlog publico da rota de CI
do upstream (`56b2cf1dacdcd033/00000017--d24ffdb376`, segmento 0, 61,2 s).

## 0. Resultado em uma pagina

Classe D (faltava e foi corrigido nesta auditoria):

| # | Commit upstream | O que mudava para o City | Correcao local |
|---|---|---|---|
| D1 | opendbc `28a16218` (2025-08-05) | `ret.steerActuatorDelay = 0.1` ficava DEPOIS do bloco por carro e sobrescrevia o `0.15` do City. Upstream (e o carParams da rota) usa 0.15. | opendbc `d42db044` |
| D2 | opendbc `fb5ac6d3` (2025-06-27) | `configure_torque_tune` passou de `ki = 0.1` para `ki = 0.3`. O City usa essa funcao; o carParams da rota mostra `lateralTuning.torque.ki = 0.3`. Decisao do dono: NAO alterar o default global; `ki = 0.3` setado so no bloco do City em `honda/interface.py` (desvio deliberado do upstream, restrito ao City). | opendbc `052a515f` |
| D3 | openpilot `bae7a610f` (2025-08-04) | `GearShifter.sport` passou a ser aceito para Honda em `car_specific.py`. O City (CVT) tem posicao S; sem isso, S gera `wrongGear` e desengaja. Upstream ja tinha isso quando o City entrou (`09aa21390`). | openpilot `c3e422ae9` |

Novo HEAD opendbc: `052a515f`; o gitlink do submodule `opendbc_repo` em
openpilot foi atualizado para ele (ver secao 10). Novo HEAD openpilot: ver
secao 10.

**Adendo 2026-10-28 (auditoria 2 independente, `audit2/AUDITORIA2_INDEPENDENTE.md`):**
duas das diferencas residuais abaixo foram fechadas - GEARBOX S/L (opendbc
`b4125fe6`, layout `GEARBOX_CVT` upstream) e `torqued` para Honda (openpilot
`8be62bc95`); gitlink em openpilot `e841f3cc3`. Correcoes a este relatorio:
`common/pid.py` NAO e identico ao upstream (13+/19-, anti-windup de
`455a6a586`/`ab44c9a4f`, diferenca de plataforma, nao portada) e o `pandad`
upstream tambem difere em logica de relay/IsOnroad (plataforma). Ver secao 9.

Diferencas residuais (nao corrigidas, explicadas na secao 9): decodificacao de
S/L em `GEARBOX` 0x191 (byte0 one-hot na v0.9.9 vs byte5 no upstream; P/R/N/D
sao equivalentes) **[fechada em `b4125fe6`]**, `torqued` desabilitado para Honda no openpilot v0.9.9
(upstream `839a77334` habilitou) **[fechada em `8be62bc95`]**, `steeringTorqueEps` ainda preenchido na
v0.9.9, nomes de sinais do LKAS_HUD, `useSteeringAngle` (campo removido no
upstream), `carState.gas` ainda publicado.

## 1. Metodo

1. Lista dos 73 commits upstream `e370a036..43006b9a` que tocam
   `opendbc/car/honda`, `opendbc/dbc/generator/honda`,
   `opendbc/safety/modes/honda.h`, `opendbc/safety/tests/test_honda.py`,
   `opendbc/car/torque_data` (`git log --reverse ...`), mais os commits dos
   arquivos genericos usados pelo caminho Bosch radarless (`interfaces.py`,
   `__init__.py`, `lateral.py`, `car.capnp`, `safety.h`, `ecu_addrs.py`,
   `docs_definitions.py`, `opendbc/can/*`).
2. Leitura do diff real de cada commit (`git show`), e do diff consolidado
   `HEAD..43006b9a` por arquivo, isolando o que afeta o City (plataforma
   `HondaBoschPlatformConfig`, flags `BOSCH | BOSCH_RADARLESS` = 12, DBC
   `honda_civic_ex_2022_can_generated`, harness Bosch B, CVT com 0x191).
3. Geracao dos DBCs `honda_civic_ex_2022_can_generated.dbc` a partir de tres
   arvores (base `e370a036`, HEAD do port, upstream `43006b9a`) com
   `tools/gen_dbc_from_tree.py` e comparacao estrutural (`tools/dbc_struct_compare.py`:
   id, dlc, start bit, tamanho, ordem, sinal, fator, offset, VAL_).
4. Scan do rlog da rota (`tools/route_scan4_audit.py`): `carParams` escrito pelo
   upstream (verdade de referencia), `carFw`, fingerprint, taxas por id/bus,
   bytes de `GEARBOX`, presenca dos ids criticos.
5. Calculo do `CarParams` do City com a arvore v0.9.9 (parser Cython stubado,
   `tools/carparams_compare.py`) e comparacao campo a campo com o `carParams`
   da rota.
6. Equivalencia byte a byte dos quadros TX (`tools/tx_byte_compare.py`): packer
   proprio big-endian + checksum Honda, mesmo conjunto de valores aplicado aos
   dois DBCs (1036 quadros; cross-check do packer com cantools em
   STEERING_CONTROL e SCM_BUTTONS).
7. Diff de `opendbc/safety/modes/honda.h`, `safety.h`, `safety_declarations.h`
   e `test_honda.py` entre `e370a036` e `43006b9a`, lido com os flags do City.
8. Comparacao byte a byte das entradas de FW e do `FW_QUERY_CONFIG`.
9. `tools/audit_port_hunks.py` depois de cada commit novo.
10. Lado openpilot: `git diff 8aadf02b 09aa21390` em `selfdrive/car`,
    `selfdrive/controls/lib/latcontrol_torque.py`, `common/pid.py`,
    `selfdrive/locationd/{torqued,lagd}.py`.

Classes: A = portado; B = nao se aplica ao City; C = aplicavel mas equivalente
na v0.9.9 (mesmos bytes/valores); D = faltava (corrigido).

## 2. Tabela dos commits Honda (73) e genericos relevantes

| Hash | Data | Titulo | Classe | Evidencia |
|---|---|---|---|---|
| 05c66756 | 2025-06-05 | Add Ford Expedition Mk4 | B | so `torque_data` de Ford; linha do City em `override.toml` identica (`[1.2, 1.2, 0.23]`). |
| f41a3c83 | 2025-06-11 | Add format_fingerprints.py | B | ferramenta de formatacao; bytes das entradas nao mudam. |
| 16c08fb4 | 2025-06-11 | Car docs: fix year test | B | docs/teste. |
| d8abecb8 | 2025-06-12 | [bot] Fingerprints | B | FW de outros carros. |
| aacf554c | 2025-06-17 | Fix a few dbc typos | B/C | comentarios/VAL_ sem mudanca de bits nos sinais lidos pelo City (dbc_struct_compare). |
| 334d06f4 | 2025-06-27 | fingerprints: auto-formatted note | B | comentario. |
| 9d7e4b96 | 2025-07-01 | Car Port for Thai HR-V 2023 (3G) | B | so HR-V 3G (cvt por 0x1A3 + `GEARBOX_ALT`, FW, rota); nenhuma linha do caminho do City. |
| 3824e2b4 | 2025-07-02 | Add FW 2018 Civic Hatchback | B | FW de outro carro. |
| 15fd03ac | 2025-07-13 | ecu disable: remove magic bytes | C | so muda o literal da mensagem de desabilitar ECU (EPS mod); o City nao tem EPS modificado e `eps` e non-essential. |
| 9afca5bd | 2025-07-13 | Add deinit for re-enabling ECUs | B/C | `deinit` reativa radar so para Bosch nao radarless; City radarless nao desabilita nada. Acoplado ao openpilot (card.py chama `CI.deinit`). |
| 6fa346ed | 2025-07-13 | EPB message refactor | A | opendbc `ae690dd7` + `07add98b` (python + 6 hunks de DBC). Necessario: City nao envia 0x1C2 (0 quadros na rota). |
| 300d2cb3 | 2025-07-14 | Door open refactor part 1 | C | City nao tem `HAS_ALL_DOOR_STATES`; nos dois lados `doorOpen = SCM_FEEDBACK.DRIVERS_DOOR_OPEN` (0x326, mesmo bit; `SCM_BUTTONS` 0x296 nao tem `DRIVERS_DOOR_OPEN` em nenhum dos DBCs). |
| a1867e62 | 2025-07-14 | Standstill refactor part 1 | C | City nao parseia `STANDSTILL` (radarless usa `CRUISE_FAULT_STATUS` 0x1D3, 50 Hz na rota); so range/`CONTROLLED_STANDSTILL` mudaram no DBC. |
| c0f4a6f3 | 2025-07-14 | Add FW 2024 Pilot | B | FW de outro carro. |
| a23ad982 | 2025-07-14 | Door open refactor part 2 | C | idem 300d2cb3. |
| aa08e499 | 2025-07-14 | Door open refactor part 3 | C | idem 300d2cb3 (Nidec). |
| bf9763b6 | 2025-07-14 | Decommission China Odyssey | B | outra plataforma. |
| ef4e1ba5 | 2025-07-16 | Alternate brake refactor | C | City sem `BOSCH_ALT_BRAKE` (0x1BE: 0 quadros na rota); `brakePressed` via `POWERTRAIN_DATA.BRAKE_PRESSED` 0x17C nos dois lados, mesmo bit. |
| 827569a0 | 2025-07-16 | Steering sensors refactor | C | so `crv_executive`/`fit_hybrid`; `STEERING_SENSORS` 0x14A identica nos dois DBCs (dbc_struct_compare: 0 diffs). |
| 0f9d9876 | 2025-07-21 | Revert Bolt EUV lat values | B | toml de outro carro. |
| cdf3e4a1 | 2025-07-21 | Slimming carState part 1 | B | car.capnp; acoplado ao openpilot. |
| 019038b3 | 2025-07-21 | Slimming carState part 2 | B | idem. |
| e4fd4686 | 2025-07-21 | Slimming carState part 4 | B | idem. |
| b1856fd8 | 2025-07-21 | Revert Slimming part 1 | B | idem. |
| de7d108f | 2025-07-21 | Slimming carState part 6 | B | idem. |
| e1409d59 | 2025-07-21 | Revert Slimming part 6 | B | idem. |
| 36812afa | 2025-07-21 | Reapply Bolt EUV lat values | B | toml de outro carro. |
| 08469e94 | 2025-07-22 | Update docs 2025 Civic Hybrid | B | docs. |
| d4172ceb | 2025-07-22 | Misc generator cleanup | C | reorganizacao de arquivos do gerador; DBC gerado equivalente para os sinais do City. |
| 0f1141fd | 2025-07-22 | Bosch SCM message refactor | C | `SCM_FEEDBACK` 0x326 e `SCM_BUTTONS` 0x296: todos os sinais lidos (`CRUISE_BUTTONS`, `CRUISE_SETTING`, `MAIN_ON`, `LEFT/RIGHT_BLINKER`, `DRIVERS_DOOR_OPEN`, `SEATBELT`...) identicos em bit/tamanho; 0x326 so ganhou `REVERSE_LIGHT`/`PARKING_BRAKE_ON`, nao usados pelo City. |
| 9ef0b1fb | 2025-07-22 | Gear position message refactor | C* | ver secao 4.3: P/R/N/D equivalentes (bits 0-3 de byte0 sao `SELECTED_P/R/N/D` no proprio upstream); S/L nao verificaveis. Nao portavel verbatim (depende da cadeia de refactors e do DBC compartilhado com Civic 2022/HR-V 3G). |
| 0dced73a | 2025-07-22 | Acura RDX is a snowflake | B | RDX; `transmissionType` do City coberto por `ae690dd7` (`elif candidate == CAR.HONDA_CITY_7G and 0x191 in fingerprint -> cvt`). |
| 5191332e | 2025-07-22 | Reapply Slimming part 6 | B | openpilot-coupled. |
| f81bcb34 | 2025-07-22 | fix honda vEgo scaling | C | corrige regressao do proprio upstream (slimming); v0.9.9 usa `get_wheel_speeds(... )` com `wheelSpeedFactor = 1.0` e `KPH_TO_MS`, mesmo valor. |
| f8d6e46f | 2025-07-23 | opendbc/can little cleanups | B | infra do parser. |
| 2e0b5df9 | 2025-07-23 | Tesla HW4 Model X | B | toml de outro carro. |
| 68b76701 | 2025-07-23 | update_strings -> update | B | API do parser (openpilot-coupled). |
| c966a2be | 2025-07-23 | Move checksum to car modules | C | `honda_checksum` em python e identico ao `honda_checksum` C++ de `opendbc/can/common.cc` da v0.9.9 (mesmo algoritmo nibble a nibble, +3 para id estendido). |
| 9dbf1a0a | 2025-07-23 | Dynamic CANParser | C | conjunto de mensagens acessadas pelo City e o mesmo que a lista estatica da v0.9.9 (secao 4.1); todas presentes na rota nas taxas exigidas. |
| 848c679a | 2025-07-23 | Dynamic CANParser all brands | C | idem. |
| 723b8e43 | 2025-07-23 | revert RIs for now | B | radar interfaces de outras marcas. |
| 245e58ad | 2025-07-24 | Common platform config CAN-FD | B | CAN-FD. |
| d0e1a299 | 2025-07-24 | Revert revert Slimming part 1 | B | openpilot-coupled. |
| e7470dea | 2025-07-24 | safety: misc cleanups | C | refactor sem mudanca de logica (secao 6). |
| 26c1277c | 2025-07-24 | Revert Slimming part 2 | B | openpilot-coupled. |
| dc99b8e1 | 2025-07-24 | revert gas/brake deprecation | B | openpilot-coupled. |
| be29072c | 2025-07-24 | remove EPS torque causing CAN error | C | ver secao 4.2: o City transmite 0x1AB a 50 Hz (3056 quadros, dlc 3); na v0.9.9 esta na lista com frequencia 0 (sem timeout); `steeringTorqueEps` nao e usado por nenhum processo do openpilot v0.9.9. |
| 698ca0ad | 2025-07-25 | safety: to_push/to_send -> msg | C | rename. |
| a2067d04 | 2025-07-25 | Deprecate carState.gas | B | openpilot-coupled; v0.9.9 continua publicando `gas`. |
| 229324c7 | 2025-07-25 | Simplify cruise speed units | C | `v_cruise_factor = MPH_TO_MS if radarless and not is_metric else KPH_TO_MS` == `get_cruise_speed_conversion` da v0.9.9; usado no mesmo lugar (`cruiseState.speed` e `hud_v_cruise`). |
| c0c1b634 | 2025-07-25 | safety: cleanup frequency spec | C | reordena campo `.frequency`; valores iguais. |
| af390239 | 2025-07-26 | Bump min steer speed CR-V 5G | B | CR-V. |
| 24a6cf3c | 2025-07-28 | rm GET_BUS | C | macro. |
| 34210c7f | 2025-07-28 | safety: rm GET_ADDR | C | macro. |
| 379e8bac | 2025-07-28 | safety: rm GET_BYTE | C | macro. |
| 7ba3c144 | 2025-08-04 | Cleanup LKAS_HUD overlaps | C | `SET_ME_X48 = 0x48` (bits 31..24) == `LDW_OFF` (bit 27) + `SET_ME_X1` (bit 30); 1036 quadros TX identicos (secao 5). |
| 1302e1bb | 2025-08-04 | ruff preview rules | B | estilo. |
| c26c4a68 | 2025-08-05 | DBC signals regen braking | B | sinais 0x1A3/regen, City nao tem 0x1A3. |
| 48172250 | 2025-08-05 | Disengage stock ACC on regen paddle | B | revertido em 040c6123. |
| 28a16218 | 2025-08-05 | CAN-FD platform cleanup | **D (hunk steerActuatorDelay)** / B (dashcamOnly) | corrigido em opendbc `d42db044`. |
| faf74fe7 | 2025-08-06 | Bosch safety cleanup | C | refactor de honda.h; RX/TX do radarless identicos (secao 6). |
| 806ae2cf | 2025-08-06 | Bosch CAN-FD platform safety | B | flag `BOSCH_CANFD = 16` do safety; City nao usa. |
| eb9c0725 | 2025-08-06 | CAN-FD cleanup part 2 | B | CAN-FD. |
| 065fa021 | 2025-08-06 | Accord 2023-2025 (canfd) | B | CAN-FD. |
| 1d4a8455 | 2025-08-07 | Nidec SCM message refactor | B | Nidec. |
| 040c6123 | 2025-08-09 | Revert regen paddle | B | - |
| d01d4a32 | 2025-08-12 | Pilot 2023-2025 (canfd) | B | CAN-FD. |
| 7dc76cf6 | 2025-08-13 | Acura MDX 2025 (canfd) | B | CAN-FD. |
| 48ce21e8 | 2025-08-13 | bump canfd Accord to 2025 | B | CAN-FD. |
| 9a23366d | 2025-08-13 | CAN-FD car updates | B | CAN-FD. |
| fa210c3f | 2025-08-14 | CRV 2023-2025 (canfd) | B | CAN-FD. |
| 4b117c0a | 2025-08-14 | Add FW 2025 HR-V | B | FW de outro carro. |
| 74bfaa2c | 2025-08-15 | Torque controller in accel space | C | ver secao 7: PID da v0.9.9 em espaco de torque com `erro = e_a / latAccelFactor` e friccao em torque equivale ao upstream (erro em accel, friccao `* latAccelFactor`, divisao final por latAccelFactor); `common/pid.py` e identico entre v0.9.9 e `09aa21390`. Acoplado ao openpilot, nao portavel isoladamente. |
| 28982878 | 2025-08-17 | PSA initial support | B | outra marca. |
| f65e5c9f | 2025-08-17 | remove EPS mod support | C | City nao tem EPS modificado (FW `39990-T14-B030`, sem `,` no FW). Na v0.9.9, EPS modificado pularia o tuning; no upstream vira `dashcamOnly`. Sem efeito para FW original. |
| 5dd7a35e | 2025-08-19 | Package availability Civic | B | docs. |
| 43006b9a | 2025-08-19 | Honda City (Brazil only) 2023 | A | opendbc `34dd823b` (cherry-pick), `256ff78c` (rota/CARS.md). Blocos do City em `values.py`, `fingerprints.py`, `interface.py`, `override.toml` identicos ao upstream (nao aparecem no `git diff HEAD 43006b9a`). |

Genericos adicionais:

| Hash | Data | Titulo | Classe | Evidencia |
|---|---|---|---|---|
| fb5ac6d3 | 2025-06-27 | Torque control defaults: more integrator | **D** | corrigido em opendbc `052a515f` (ki 0.3 so no bloco do City; default global mantido em 0.1 por decisao do dono). |
| df1dd86a | 2025-07-08 | Torque control: rm localizer option | C | remove `useSteeringAngle`; v0.9.9 passa `use_steering_angle=True` (default) e `latcontrol_torque` usa curvatura do angulo de direcao, que e o unico caminho que sobrou no upstream. |
| d70e2029 | 2025-07-21 | car interfaces: clean up friction | C | move friccao para o openpilot; mesma formula (`np.interp(erro, [-0.3, 0.3], [-friction, friction])`). |
| e196c9f1 | 2025-08-01 | remove numpy.mean | C | identico numericamente. |
| a517b997 / adb60016 / 194b3dbc | 2025-08 | lateral.py moves / angle limits | B | City e torque, nao angle. |
| 7ff7798a / b32f4f09 / 47d83d46 | 2025-07 | CANParser auto-freq / python rewrite | B | parser; na v0.9.9 o parser C++ com lista estatica cobre o mesmo conjunto (secao 4.1). |
| 2f5d02ee / 8cdc66a3 / ace1115c / e7e92943 / d4ca46c3 | 2025-07 | car.capnp cleanup/slimming | B | openpilot-coupled. |
| f30165a0 / fcf851ae | 2025-07 | safety RX invalid on unset frequency (+revert) | B | revertido. |
| a8a6ca48 | 2025-08-12 | PSA unpadded tester present | B | `ecu_addrs.py`: relaxa tamanho minimo da resposta tester-present; Honda responde padded; sem efeito. |
| 54c17f03 / 50e4b63e / fa6a2ee0 / 221274a9 | 2025-07 | docs_definitions | B | docs. |
| fw_versions.py, fw_query_definitions.py, vin.py | - | - | - | **sem commits** no intervalo (regras de match exato/fuzzy, VIN identicas). |

## 3. Reconhecimento de firmware

- Bloco `CAR.HONDA_CITY_7G` em `fingerprints.py`: **identico byte a byte** ao de
  `43006b9a` (comparacao textual do bloco inteiro): `eps 0x18da30f1
  b'39990-T14-B030\x00\x00'`, `gateway 0x18daeff1 b'38897-T14-M110\x00\x00'`,
  `srs 0x18da53f1 b'77959-T00-B830\x00\x00'`, `fwdRadar 0x18dab0f1
  b'36161-T14-P050\x00\x00'`, `vsa 0x18da28f1 b'57114-T14-B030\x00\x00'`,
  `transmission 0x18da1ef1 b'28101-63B-M420\x00\x00'`; sub-address `None` em todos.
- `FW_QUERY_CONFIG`: requests (UDS_VERSION bus 1; HONDA_ALT logging bus 1;
  UDS bus 0; UDS bus 1 `obd_multiplexing=False`), `extra_ecus`
  (`combinationMeter 0x18da60f1`, `programmedFuelInjection 0x18da10f1`) e
  `non_essential_ecus` identicos; unica diferenca textual e `*HONDA_BOSCH_CANFD`
  no fim das listas `eps`/`vsa` (plataformas CAN-FD inexistentes aqui).
  `CAR.HONDA_CITY_7G` esta nas duas listas nos dois lados.
- `fw_versions.py` nao mudou no intervalo: match exato exige todas as ECUs
  essenciais (`ESSENTIAL_ECUS`) que nao estejam em `non_essential_ecus`. Para o
  City sobra apenas `fwdRadar` (camera). A rota confirma: `carFw` tem **uma**
  entrada (`fwdRadar 0x18DAB0F1`, request `b'"\xf1\x81'`), e mesmo assim
  `fingerprintSource = fw`, `fuzzyFingerprint = False`. Na v0.9.9 o resultado e
  o mesmo (mesmas regras, mesma tabela).

## 4. carstate: mensagens, bits e frequencias

### 4.1 Conjunto de mensagens e taxas (v0.9.9 lista estatica vs rota)

Bus 0 (PT): `ENGINE_DATA 0x158` 100 Hz, `POWERTRAIN_DATA 0x17C` 100,
`STEERING_SENSORS 0x14A` 100, `STEER_STATUS 0x18F` 100 (dlc 7), `GEARBOX 0x191`
100, `WHEEL_SPEEDS 0x1D0` 50, `VSA_STATUS 0x1A4` 50, `STEER_MOTOR_TORQUE 0x1AB`
50 (dlc 3; exigido com freq 0), `CRUISE_FAULT_STATUS 0x1D3` 50, `SCM_BUTTONS
0x296` 25, `SEATBELT_STATUS 0x305` 10, `CRUISE 0x324` 10, `CAR_SPEED 0x309` 10,
`SCM_FEEDBACK 0x326` 10. Bus 2 (camera): `STEERING_CONTROL 0xE4` 100, `ACC_HUD
0x30C` 10, `LKAS_HUD 0x33D` 10. Todas medidas na rota nessas taxas
(`_scratch/route_scan4.txt`, taxas 99,9-100 / 49,9-50 / 25,0 / 10,0 Hz).
Ausentes na rota (0 quadros): 0x1C2 EPB_STATUS, 0x1BE BRAKE_MODULE, 0x1A3,
0x33DA/0x33DB, 0xE5, 0x1FA, 0x1DF. O parser dinamico do upstream acessa
exatamente esse mesmo conjunto para o City (sem `EPB_STATUS` por `HAS_EPB`
ausente, sem `BRAKE_MODULE`, sem `DOORS_STATUS`, sem `STANDSTILL`, sem BSM).

### 4.2 0x1AB STEER_MOTOR_TORQUE (be29072c)

- O City **transmite** 0x1AB: 3056 quadros / 61,2 s = 49,9 Hz, dlc 3.
- v0.9.9 `get_can_messages`: `("STEER_MOTOR_TORQUE", 0)` - frequencia 0 significa
  sem verificacao de timeout no parser C++. `ret.steeringTorqueEps =
  MOTOR_TORQUE` e preenchido.
- Upstream removeu o sinal porque em alguns carros a mensagem nao existe e o
  parser dinamico (que exige receber tudo que e acessado) falhava. Para o City
  nao ha diferenca funcional: `steeringTorqueEps` nao e consumido por nenhum
  processo do openpilot v0.9.9 (so por layouts do plotjuggler).

### 4.3 GEARBOX 0x191 (9ef0b1fb) - diferenca residual

- v0.9.9 (`GEARBOX`): `GEAR_SHIFTER 5|6@0+` = byte0 bits 5..0, `VAL_ 1 P, 2 R,
  4 N, 8 D, 16 S, 32 L`.
- Upstream (`GEARBOX_CVT`): `GEAR_SHIFTER 44|5@0+` = byte5 bits 4..0, `VAL_ 1 P,
  2 R, 3 N, 4 D, 7 L, 10 S`; e define em byte0 `SELECTED_P 0|1`, `SELECTED_R
  1|1`, `SELECTED_N 2|1`, `SELECTED_D 3|1` (one-hot, exatamente os valores
  1/2/4/8 que a v0.9.9 decodifica).
- Rota: 100% dos 6116 quadros com byte0 & 0x3F = 8 (D) e byte5 & 0x1F = 4 (D).
  Nenhum quadro em P/R/N/S/L no segmento disponivel.
- Conclusao: P/R/N/D equivalentes por construcao; S e L **nao verificaveis**.
  A reengenharia do upstream nao encontrou bits de S/L em byte0, portanto na
  v0.9.9 em S o resultado mais provavel e `drive` (byte0 = 8) ou `unknown`
  (`wrongGear`), enquanto o upstream reporta `sport` (aceito apos D3). Em L o
  upstream gera `wrongGear` (`low` nao esta em `extra_gears` de Honda); a
  v0.9.9 pode reportar `drive`. Portar 9ef0b1fb verbatim nao aplica
  (`git apply --check` falha em carstate/interface/values por depender de
  0f1141fd, 300d2cb3 etc.) e o DBC e compartilhado com Civic 2022 e HR-V 3G,
  cuja decodificacao tambem mudaria sem possibilidade de validar aqui.
  Recomendacao: gravar uma rota curta passando por P/R/N/D/S/L antes de
  qualquer uso, e so entao decidir entre manter ou portar a cadeia de refactors.

### 4.4 Portas, standstill, freio alternativo, sensores de direcao, SCM

`tools/dbc_struct_compare.py` (HEAD vs upstream) sobre todos os sinais usados
pelo carstate do City: `ENGINE_DATA.XMISSION_SPEED/ENGINE_RPM`,
`WHEEL_SPEEDS.*`, `STEERING_SENSORS.STEER_ANGLE/STEER_ANGLE_RATE`,
`STEER_STATUS.STEER_TORQUE_SENSOR/STEER_STATUS/STEER_CONTROL_ACTIVE`,
`POWERTRAIN_DATA.PEDAL_GAS/BRAKE_PRESSED/BRAKE_SWITCH/ACC_STATUS`,
`VSA_STATUS.ESP_DISABLED/USER_BRAKE`, `SEATBELT_STATUS.SEATBELT_DRIVER_LAMP/
SEATBELT_DRIVER_LATCHED`, `CRUISE.*`, `CAR_SPEED.IMPERIAL_UNIT`,
`SCM_FEEDBACK.DRIVERS_DOOR_OPEN/MAIN_ON/LEFT_BLINKER/RIGHT_BLINKER`,
`SCM_BUTTONS.CRUISE_BUTTONS/CRUISE_SETTING`, `CRUISE_FAULT_STATUS.CRUISE_FAULT`,
`STEERING_CONTROL.*`, `ACC_HUD.CRUISE_SPEED/...`, `LKAS_HUD.LKAS_PROBLEM`:
**mesmo id, start bit, tamanho, fator e offset**. Diferencas estruturais
encontradas e por que nao afetam o City: 0x191 (secao 4.3), 0x1A3 (ausente),
0x1B0 `STANDSTILL` (range e `CONTROLLED_STANDSTILL`; nao parseado), 0x221
rename, 0x296 so VAL_, 0x326 ganha `REVERSE_LIGHT`/`PARKING_BRAKE_ON` (nao
lidos), 0x33D (secao 5), 0x372 `CRUISE_PARAMS` so na v0.9.9 (nao lido), 0x1FA
`LEGACY_BRAKE_COMMAND` so no upstream (Civic Bosch, nao City).

## 5. TX: equivalencia byte a byte

`tools/tx_byte_compare.py _scratch/dbc_head/... _scratch/dbc_up/...`:

- `STEERING_CONTROL 0xE4`: 56 combinacoes (torque -2560..2560, request 0/1,
  counter 0..3) - identicos. Exemplo: torque -1234, request 1, counter 2 ->
  `fb2e800022` (igual ao cantools).
- `LKAS_HUD 0x33D`: 32 combinacoes - identicos. v0.9.9 escreve `SET_ME_X48 =
  0x48` em bits 31..24; upstream escreve `LDW_OFF = 1` (bit 27) e `SET_ME_X1 =
  1` (bit 30): 0x48 = 0b0100_1000 = bits 30 e 27. Exemplo: `415500481800003e`.
- `SCM_BUTTONS 0x296` (spam no bus 2 para radarless): 20 combinacoes - identicos.
- `ACC_CONTROL 0x1C8` (long do openpilot, radarless): 160 combinacoes
  (`ACCEL_COMMAND`, `STANDSTILL`, `CONTROL_ON`, `IDLESTOP_ALLOW`) - identicos.
- `ACC_HUD 0x30C` (long do openpilot): 768 combinacoes - identicos.
- Total 1036 quadros, 0 diferencas; ids/dlc de `BOSCH_SUPPLEMENTAL_1` tambem
  iguais (nao enviado para radarless nos dois lados).
- Logica Python que alimenta os quadros: `create_steering_control`,
  `create_acc_commands` (ramo radarless), `create_ui_commands`,
  `spam_buttons_command` identicos exceto o rename `SET_ME_X48` -> `LDW_OFF +
  SET_ME_X1` e `get_cruise_speed_conversion` -> `CS.v_cruise_factor` (mesma
  formula). `CarControllerParams` (STEER_MAX 4096 via torqueV 2560 do City,
  `STEER_DELTA_UP/DOWN 3`, `STEER_STEP 1`, `BOSCH_ACCEL_MAX 2.0`,
  `BOSCH_GAS_LOOKUP_*`) **identico** (comparacao textual da classe inteira).

## 6. Safety (panda black, firmware da arvore v0.9.9)

Flags do City: `safetyParam = RADARLESS (8)`, mais `BOSCH_LONG (2)` se o long
experimental for ligado (a rota foi gravada com 10). Sem `ALT_BRAKE`, sem
`BOSCH_CANFD` (nao existe na v0.9.9).

- RX checks (`honda_bosch_radarless_rx_checks`, honda.h linhas 360-363 do HEAD):
  `HONDA_COMMON_RX_CHECKS(0)` = 0x1A6/0x296 25 Hz, 0x158 100 Hz, 0x17C 100 Hz,
  0x326 10 Hz, todos bus 0, `max_counter 3`, `ignore_quality_flag`;
  `+ 0x1BE 50 Hz` so com ALT_BRAKE. Upstream `43006b9a`: mesmas entradas, mesma
  ordem, apenas com `.frequency` reposicionado e `bus` unsigned.
- TX allowlist: `HONDA_RADARLESS_TX_MSGS = {0xE4,0,5},{0x296,2,4},{0x33D,0,8}`;
  `HONDA_RADARLESS_LONG_TX_MSGS = + {0x1C8,0,8},{0x30C,0,8}`. Identicos.
- Limites de torque (`HONDA_STEERING_LIMITS`), gating de botoes (`0x296` so com
  `!controls_allowed`), `honda_fwd_hook`, relay/heartbeat: sem mudanca de
  logica; todos os commits `e7470dea`, `698ca0ad`, `c0c1b634`, `24a6cf3c`,
  `34210c7f`, `379e8bac`, `faf74fe7` sao renames/macros; `806ae2cf` e
  CAN-FD (`BOSCH_CANFD = 16`).
- `test_honda.py`: diferencas sao renames e classes CAN-FD; a cobertura
  radarless (`TestHondaBoschRadarlessSafetyBase`, `...AltBrake`, `...Long`)
  e a mesma.
- Nenhum commit do intervalo corrige um bug de safety que afete o City; nao ha
  nada a retroportar para o firmware.

## 7. interface.py / CarParams do City

`tools/carparams_compare.py opendbc_firmwarecityg7 _scratch/route_scan4.json
--alpha-long` (apos D1 e D2): **80 campos iguais, 2 diferentes, 11 so no log**.

- Iguais (entre outros): `mass 1553.47`, `wheelbase 2.6`, `steerRatio 19.0`,
  `centerToFront 1.066`, `tireStiffnessFactor 1.0`, `rotationalInertia 2463.29`,
  `tireStiffnessFront/Rear 200769.6/220549.4`, `minSteerSpeed 6.3889`
  (`CarSpecs.minSteerSpeed = 23 km/h`), `steerActuatorDelay 0.15`,
  `steerLimitTimer 0.8`, `radarDelay 0.1`, `lateralParams.torqueBP/V [0,2560]`,
  `lateralTuning.torque kp 1.0 / ki 0.3 / kf 1.0 / friction 0.23 /
  latAccelFactor 1.2 / latAccelOffset 0 / steeringAngleDeadzoneDeg 0`,
  `maxLateralAccel 1.2`, `longitudinalActuatorDelay 0.5`, `stopAccel -3.5`,
  `vEgoStopping/Starting 0.5`, `stoppingDecelRate 0.8`, `openpilotLongitudinalControl
  True / pcmCruise False` (com alpha long), `radarUnavailable True`, `enableBsm
  False`, `autoResumeSng True`, `minEnableSpeed -1`, `transmissionType cvt`,
  `wheelSpeedFactor 1.0`, `flags 12`, `safetyConfigs [hondaBosch, 10]`,
  `dashcamOnly False`, `steerControlType torque`, `notCar False`.
- Diferentes: `fingerprintSource` (o script nao passa pelo card.py; na v0.9.9 o
  card.py tambem grava `fw`), `lateralTuning.torque.useSteeringAngle` (True na
  v0.9.9, campo removido no upstream e portanto False no log; comportamento
  igual, ver df1dd86a).
- So no log: `carFw`, `carVin`, campos escritos pelo card.py.
- `alphaLongitudinalAvailable` (upstream) == `experimentalLongitudinalAvailable`
  (v0.9.9) = True para radarless; sem alpha long, ambos dao
  `openpilotLongitudinalControl False / pcmCruise True / safetyParam 8`.

Antes de D1/D2 o mesmo script reportava `steerActuatorDelay 0.1 != 0.15` e
`ki 0.1 != 0.3`.

Sobre D2 (ki): `common/pid.py` e identico entre v0.9.9 e `09aa21390`. Na
v0.9.9 `latcontrol_torque` faz `erro = torque(setpoint) - torque(medida) =
(a_set - a_med)/latAccelFactor` e soma friccao em torque; no upstream
(`ab44c9a4f`, 2025-08-15) `erro = a_set - a_med`, friccao `* latAccelFactor`, e
a saida do PID e dividida por `latAccelFactor` no fim. Como o modelo e linear,
`kp`, `ki` e `kf` tem o mesmo significado nos dois; `fb5ac6d3` foi feito em
2025-06-27, quando o openpilot ainda usava o controlador em espaco de torque
(mesmo da v0.9.9).

Decisao do dono sobre o escopo de D2: o default global em
`opendbc/car/interfaces.py` fica em `ki = 0.1` (valor da v0.9.9) para nao
retunar as outras plataformas do branch; `ret.lateralTuning.torque.ki = 0.3`
e setado explicitamente no bloco `HONDA_CITY_7G` de `honda/interface.py`, logo
apos `configure_torque_tune`. E um desvio deliberado do upstream restrito ao
City (commit `052a515f`, que substituiu o `3d49429f` inicial). Verificado:
dentre as plataformas Honda da v0.9.9 so o City usa torque tune (as outras
usam PID), entao nenhuma outra Honda muda; `interfaces.py` esta identico a
`e370a036`, logo as outras marcas mantem ki 0.1.

## 8. Lado openpilot v0.9.9

Diff `8aadf02b..09aa21390` em `selfdrive/car`: `car_specific.py` (sport gear
Honda e Toyota), `card.py` (`params.get` sem encoding), `cruise.py` (import),
`test_models.py`. Em `selfdrive/controls`: `latcontrol_torque.py` (accel
space, secao 7), `pid.py` sem mudanca em `common/pid.py`. `locationd`:
`torqued.py` `ALLOWED_CARS += 'honda'` (`839a77334`), `lagd` deixou de ser
shadow em release (`44c8cc4cb`; irrelevante aqui, o branch nao e release).
`pandad`: mudancas de SPI/CAN-FD, sem efeito no black panda USB.

- D3 aplicado (`c3e422ae9`): hunk verbatim de `bae7a610f`.
- `torqued` para Honda (`839a77334`): **nao aplicado**. E uma linha
  (`ALLOWED_CARS = ['toyota', 'hyundai', 'rivian', 'honda']` em
  `selfdrive/locationd/torqued.py`), mas liga aprendizado ao vivo de
  `latAccelFactor`/`friction`, nao e necessario para o City funcionar e
  invalidaria os refs de process replay de `torqued` para os segmentos Honda
  no CI do fork. Fica registrado como diferenca residual; se o dono quiser
  fidelidade total nesse ponto, aplicar e regenerar os refs.
- `HAS_EPB`/`parkingBrake`: v0.9.9 so preenche `parkingBrake` com `HAS_EPB`;
  City sem 0x1C2 -> False, igual ao upstream.
- `deinit` (`9afca5bd`): so reativa radar em Bosch com radar; nada para o City.
- Process replay do fork: D1/D2 mudam `carParams` e a saida do `controlsd`
  so para o City (D2 e restrito ao City; D1 so afeta carros cujo bloco por
  carro define `steerActuatorDelay`, que na v0.9.9 e so o City). Os refs
  Honda do process replay (Civic/Accord) nao mudam por isso; o CI do fork
  confirma. `test_models` do City nao depende desses valores.

## 9. Veredito: toda diferenca residual entre City na v0.9.9 e no upstream

1. **GEARBOX S/L** (secao 4.3): decodificacao de byte0 (v0.9.9) vs byte5
   (upstream); P/R/N/D equivalentes; S/L nao verificaveis sem rota.
   **Fechada em opendbc `b4125fe6`** (auditoria 2, D-1): o `BO_ 401` do
   `honda_civic_ex_2022_can.dbc` recebeu o layout `GEARBOX_CVT` upstream
   (`GEAR_SHIFTER 44|5@0+`, `VAL_ 1 P 2 R 3 N 4 D 7 L 10 S`); nome da
   mensagem mantido, `carstate.py` intocado; D identico em 6116/6116
   quadros; `tools/check_gearbox_cvt.py` confere os seis valores.
2. **torqued desabilitado para Honda** no openpilot v0.9.9 (upstream habilitou
   em 2025-08-06): no branch os parametros de torque ficam fixos em
   `[1.2, 1.2, 0.23]`; no upstream sao aprendidos ao vivo.
   **Fechada em openpilot `8be62bc95`** (auditoria 2, D-2): `ALLOWED_CARS +=
   'honda'`; so ativa com `lateralTuning == torque` (apenas o City entre os
   Honda da v0.9.9), refs de process replay dos segmentos Honda (PID) nao
   mudam.
2b. **Anti-windup de `common/pid.py` / `latcontrol_torque.py`** (auditoria 2,
   D-3): upstream `455a6a586` e `ab44c9a4f` mudaram o integrador para todos
   os carros com torque tune. Nao portado: e diferenca de plataforma e
   alteraria a lateral de toda a arvore v0.9.9. (A frase "common/pid.py
   identico" da versao anterior deste relatorio estava errada.)
3. **steeringTorqueEps** preenchido na v0.9.9 (0x1AB `MOTOR_TORQUE`), removido
   no upstream; sem consumidor.
4. **carState.gas** publicado na v0.9.9, deprecado no upstream; sem efeito.
5. **useSteeringAngle = True** no CarParams da v0.9.9, campo inexistente no
   upstream; comportamento identico.
6. **Nomes de sinais** `SET_ME_X48` vs `LDW_OFF`/`SET_ME_X1` e `GEARBOX` vs
   `GEARBOX_CVT`: bytes identicos (exceto item 1).
7. **Firmware do panda**: compilado da arvore v0.9.9 + `opendbc/safety` do
   branch; RX/TX/limites identicos aos do upstream para RADARLESS (+BOSCH_LONG).
8. **Parser estatico** (v0.9.9) vs dinamico (upstream): mesmo conjunto de
   mensagens; na v0.9.9 um timeout em qualquer mensagem da lista invalida o
   `canValid`; no upstream idem para mensagens acessadas. 0x1AB tem freq 0 na
   lista (nunca da timeout).
9. **Default global de ki** em `configure_torque_tune`: 0.1 na v0.9.9 vs 0.3
   no upstream (fb5ac6d3). Para o City o valor efetivo e 0.3 (setado no bloco
   do City); para as demais marcas do branch continua 0.1 por decisao do dono.
10. Nada foi validado no carro. Nenhum teste de rua aconteceu.

## 10. Commits feitos nesta auditoria

opendbc `firmwarecityg7-v0.9.9` (HEAD `052a515f`):

- `d42db044` Honda: set steerActuatorDelay before per-car tuning (backport of 28a16218)
- `052a515f` Honda City 7G: torque tune ki 0.3 (City-only deviation from upstream fb5ac6d3)
  (substitui o `3d49429f` inicial, que alterava o default global)

openpilot `v0.9.9-cityg7-blackpanda` (HEAD `89df27131`):

- `c3e422ae9` Honda: allow sport gear (backport of upstream bae7a610f)
- `89df27131` opendbc_repo: bump to 052a515f (City steerActuatorDelay fix, City ki 0.3)

Apos a auditoria 2 (2026-10-28):

- opendbc `b4125fe6` honda: backport GEARBOX_CVT layout for radarless Bosch (audit2 D-1)
  (+ `pyproject.toml` de volta a LF)
- openpilot `8be62bc95` torqued: enable lateral accel factor learning for Honda (audit2 D-2)
- openpilot `e841f3cc3` opendbc_repo: bump to b4125fe6
- HEADs finais: opendbc `b4125fe6`, openpilot `e841f3cc3`; CI `40525385443`.

HybridPanda `main`: este relatorio, `LEIA-ME.md` atualizado, patches
regenerados em `patches/opendbc` e `patches/openpilot`, e as ferramentas
`tools/gen_dbc_from_tree.py`, `tools/dbc_struct_compare.py`,
`tools/route_scan4_audit.py`, `tools/carparams_compare.py`,
`tools/tx_byte_compare.py`.

Verificacoes rodadas apos as mudancas: `ruff check opendbc/car/honda
opendbc/safety` (ok), `ruff check
selfdrive/car/car_specific.py` (ok), `tools/audit_port_hunks.py 28a16218`
(9 discrepancias, todas as linhas de `dashcamOnly`/`HONDA_BOSCH_CANFD`, CAN-FD),
`tools/carparams_compare.py --alpha-long` (80 iguais / 2 explicadas, ki 0.3,
steerActuatorDelay 0.15),
`tools/tx_byte_compare.py` (1036 quadros, 0 diferencas).

Branches enviados aos remotos (`fork firmwarecityg7-v0.9.9`, `origin
v0.9.9-cityg7-blackpanda`, HybridPanda `origin main`); o run de CI
`selfdrive_tests.yaml` disparado pelo push esta registrado no `LEIA-ME.md`.

## 11. O que nao foi possivel verificar e por que

- Posicoes S/L/P/R/N de `GEARBOX` no City: a rota publica so contem D.
- `test_models`/process replay/compilacao do firmware: nao rodam no Windows
  (parser Cython e libsafety nao compilados); dependem do CI do fork.
- Comportamento real do EPS/ACC do City com os quadros do openpilot: sem teste
  de rua.
