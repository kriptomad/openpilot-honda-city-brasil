# Port do Honda City G7 2023 (Brasil) para o flowpilot

Documento de entrega da Fase B. Complementa `flowpilot-scope.md` (Fase A, pesquisa e lista de lacunas).

Nada do que esta descrito aqui foi testado em carro, em celular ou em panda real. A secao 10 lista tudo o
que permanece nao verificado. Este documento descreve apenas o que foi alterado, como foi conferido no PC e
o que falta conferir; nao faz nenhuma afirmacao de aptidao para uso em via publica.

Convencoes: caminhos relativos a `software\flowpilot-port\`; "upstream" = openpilot/opendbc da comma; "port v0.9.9" =
`software\openpilot-port\{../opendbc-v0.9.9-city-g7,../openpilot-v0.9.9-city-g7}` (fontes de verdade dos fatos
do City); "jag" = jagheterfredrik/flowpilot master `9ea918ea` (base escolhida na Fase A).

## 1. Resumo

| Item | Resultado |
|---|---|
| Base | jagheterfredrik/flowpilot master `9ea918ea` (2025-03-04), importado como snapshot tarball (commit local `43eab22`) |
| Branch local | `flowpilot-city-g7-brazil` em `flowpilot\` (panda e opendbc estao achatados no mesmo repo; nao ha submodulos a ramificar) |
| Commits | `a2f1983` (camada do carro), `fd9e846` (build do firmware no Windows), `275df51` (correcao `CarInterface.apply` + `docs/CARS.md`) |
| Firmware panda preta (F4) | compilado da arvore `flowpilot\panda` com arm-none-eabi-gcc; saidas em `..\..\firmware\prebuilt\flowpilot-black-panda\` |
| Testes executados no PC | `test_car_interfaces`, `test_fw_fingerprint`, `test_fingerprints`, `test_lateral_limits`, `test_docs` (via shims Windows em `tests_windows\`); `panda/tests/safety` completo com `libpanda.so` compilado por mingw-w64 (`test_honda.py`: 209 passam, 0 falhas; secao 7) |
| APK | NAO compilado nesta maquina (exige Docker/Linux + NDK); procedimento na secao 8 |
| Push / fork | nao feito, por decisao do dono |

## 2. Base escolhida e caveat do snapshot

A Fase A concluiu que o repositorio oficial `flowdriveai/flowpilot` esta parado desde 2023 e que o fork
`jagheterfredrik/flowpilot` e o mais recente que ainda compila um APK autonomo. Nele o `panda` esta achatado
(sem submodulo) em commaai/panda `abdc4185`, que ja contem `board/boards/black.h` e `HONDA_PARAM_RADARLESS`;
a camada `selfdrive/car` corresponde ao openpilot ~0.9.2-0.9.4 e ja tem o framework de controle lateral por
torque (`latcontrol_torque.py`, `torque_data/*.yaml`, `configure_torque_tune`).

O `git clone` via proxy corporativo travava; o repositorio foi importado via tarball da API do GitHub. Por isso
o commit `43eab22` nao tem historico. Para que o fork do dono tenha historico real, o procedimento sugerido e:

```
git clone https://github.com/jagheterfredrik/flowpilot
cd flowpilot
git checkout -b flowpilot-city-g7-brazil 9ea918ea
# no clone local desta pasta:
git -C <software/flowpilot-port>\flowpilot format-patch 43eab22..flowpilot-city-g7-brazil -o <pasta>
git am <pasta>\*.patch
```

Os tres patches aplicam-se limpos sobre `9ea918ea` porque `43eab22` e exatamente esse tarball (sem `.git`,
mas com os mesmos arquivos). Se `git am` reclamar de CRLF, usar `git am --keep-cr` ou `--ignore-whitespace`.

## 3. Alteracoes arquivo a arquivo e mapeamento para o port v0.9.9

Referencias de commits upstream conforme a tabela de 73 commits em
`software\openpilot-port\auditoria-port-city-v099.md`, secao 2.

### 3.1 Commit `a2f1983` - camada do carro

| Arquivo | O que mudou | Origem no port v0.9.9 |
|---|---|---|
| `selfdrive/car/honda/values.py` | `CAR.CITY_7G = "HONDA CITY 7G"`; `CAR_INFO` ("Honda City (Brazil only) 2023", pacote "All"); `FW_VERSIONS[CAR.CITY_7G]` com 6 ECUs (eps 39990-T14-B030, gateway 38897-T14-M110, srs 77959-T00-B830, fwdRadar 36161-T14-P050, vsa 57114-T14-B030, transmission 28101-63B-M420); `FINGERPRINTS[CAR.CITY_7G]` (36 enderecos do bus 0 com DLC, derivados da rota 56b2cf1dacdcd033/17); `DBC` -> `honda_civic_ex_2022_can_generated`; `STEER_THRESHOLD[CITY_7G] = 600`; incluido em `HONDA_BOSCH` e `HONDA_BOSCH_RADARLESS`; `HondaFlags.HAS_EPB = 2` | 43006b9a / 34dd823b / 256ff78c (City), 6fa346ed (EPB) |
| `selfdrive/car/honda/interface.py` | `HAS_EPB` ligado se 0x1C2 em `fingerprint[0]`; `transmissionType = cvt` para City se 0x191 em bus 0; ramo `CAR.CITY_7G`: massa 3125 lb + carga, entre-eixos 2.6, centerToFront 0.41, steerRatio 19.0, minSteerSpeed 23 km/h, torqueBP/V [0,2560], steerActuatorDelay 0.15, `configure_torque_tune` + `torque.ki = 0.3`; `steerActuatorDelay = 0.1` movido para antes dos ramos (para o City poder sobrescrever); `create_common_events(..., extra_gears=[GearShifter.sport])` | 43006b9a (parametros), 28a16218/d42db044 (delay 0.15), fb5ac6d3 (ki 0.3), bae7a610f (marcha S), 6fa346ed (EPB) |
| `selfdrive/car/honda/carstate.py` | `EPB_STATE`/`EPB_STATUS` so sao pedidos ao parser quando `CP.flags & HAS_EPB`; `ret.parkingBrake` idem; City adicionado ao grupo que le `DRIVERS_DOOR_OPEN` em `SCM_FEEDBACK`; sinal `GEAR` (inexistente no layout CVT) removido da lista comum | 6fa346ed, 9ef0b1fb (refatoracao GEARBOX), 43006b9a |
| `opendbc/generator/honda/honda_civic_ex_2022_can.dbc` e `opendbc/honda_civic_ex_2022_can_generated.dbc` | `BO_ 401 GEARBOX` trocado do layout one-hot (byte 0) para o layout CVT do upstream: `GEAR_SHIFTER : 44|5@0+` com VAL_ 1 P, 2 R, 3 N, 4 D, 7 L, 10 S (mais os demais sinais do GEARBOX_CVT); gerado com `opendbc/generator/generator.py` | 43006b9a (import do GEARBOX_CVT em `_honda_common.dbc`) |
| `selfdrive/car/torque_data/override.yaml` | `HONDA CITY 7G: [1.2, 1.2, 0.23]` (MAX_LAT_ACCEL, latAccelFactor, friction) | override.toml do port v0.9.9 |
| `selfdrive/assets/allcars.txt` | linha `HONDA CITY 7G` (lista do seletor "Mycar" da tela de configuracoes do app) | especifico do flowpilot |
| `selfdrive/car/tests/routes.py` | `CarTestRoute("56b2cf1dacdcd033|00000017--d24ffdb376", HONDA.CITY_7G)` | 43006b9a |

Fatos do City preservados sem alteracao em relacao ao port v0.9.9: DBC `honda_civic_ex_2022_can` (radarless
Bosch), chicote Bosch B (derivado de `HONDA_BOSCH_RADARLESS` em `HondaCarInfo`), sem 0x33DA (flag
`BOSCH_EXT_HUD` permanece desligada porque so e ligada quando 0x33DA aparece), 0x1AB `STEER_MOTOR_TORQUE`
presente no DBC, mensagens TX 0xE4 / 0x1C8 / 0x30C / 0x33D geradas por `hondacan.py` (ja existente no jag
para o CIVIC_2022 radarless, sem mudanca), safety `HONDA_BOSCH` com parametro RADARLESS (ver 3.4).

### 3.2 Commit `fd9e846` - build do firmware do panda no Windows

| Arquivo | O que mudou |
|---|---|
| `panda/local_build_windows.scons` | copia do helper usado no projeto HybridPanda (`hardware/research`), adaptado para a arvore `flowpilot\panda`: compila `panda`, `panda_h7` e `jungle` com `arm-none-eabi-gcc` sem Docker, chamando o `board/SConscript` original. Nao altera nenhum arquivo do firmware. |

### 3.3 Commit `275df51` - correcao transversal + docs

| Arquivo | O que mudou | Motivo |
|---|---|---|
| `selfdrive/car/{body,chrysler,ford,gm,honda,mazda,nissan,subaru,tesla,toyota}/interface.py` | `def apply(self, c, now_nanos)` -> `def apply(self, c, sm, now_nanos)` e `self.CC.update(c, sm, self.CS, now_nanos)` | Bug pre-existente do jag: `controlsd` chama `CI.apply(CC, sm, now_nanos)` e todos os `CarController.update` recebem `sm`, mas so o VW repassava. Sem isso o Honda (e outras 9 marcas) levantava `TypeError` no primeiro frame de controle. Hyundai nao foi tocado (assinatura propria do fork). |
| `selfdrive/car/tests/test_car_interfaces.py` | chama `CI.apply(CC, None, 0)` | acompanha a assinatura acima |
| `selfdrive/car/honda/values.py` | `CarControllerParams.STEER_STEP = 1`, `STEER_DELTA_UP = 3`, `STEER_DELTA_DOWN = 3` | constantes declarativas (como no upstream) exigidas por `test_lateral_limits` para carros com tune de torque; o City e o primeiro Honda com torque nesta arvore. Nao mudam o comportamento do `carcontroller.py` do Honda, que nao as usa. |
| `docs/CARS.md` | gerado por `tests_windows\gen_cars_md.py` (nao existia no jag) | `test_docs` exige o arquivo; linha do City: `Honda | City (Brazil only) 2023 | All | ... | 0 mph | 14 mph | Bosch B connector` |

### 3.4 Safety do panda (sem alteracao de codigo)

`flowpilot\panda\board\safety\safety_honda.h` (commaai/panda `abdc4185`) ja contem:

- `HONDA_PARAM_RADARLESS = 8`, `HONDA_PARAM_BOSCH_LONG = 2`, `HONDA_PARAM_ALT_BRAKE = 1`, `HONDA_PARAM_NIDEC_ALT = 4`;
- `HONDA_RADARLESS_TX_MSGS = {{0xE4, 0, 5}, {0x296, 2, 4}, {0x33D, 0, 8}}`;
- `HONDA_BOSCH_RADARLESS_LONG_TX_MSGS` para o caso longitudinal (nao usado pelo City: `openpilotLongitudinalControl` fica falso, radarless sem long por padrao).

O `interface.py` do Honda no jag ja monta `safetyConfigs` com `SafetyModel.hondaBosch` e
`safetyParam |= HondaSafetyFlags.RADARLESS` quando `candidate in HONDA_BOSCH_RADARLESS`, e o City foi incluido
nesse conjunto. Portanto o par (modo, parametro) enviado ao panda e o mesmo do port v0.9.9
(`HONDA_BOSCH` + `RADARLESS`). Diferenca em relacao ao v0.9.9: as mensagens TX permitidas no v0.9.9 ja estao
em `opendbc/safety` (reorganizacao posterior), mas o conteudo da lista radarless e o mesmo.

## 4. Desvios em relacao ao port v0.9.9 (e por que)

| # | Desvio | Justificativa / impacto |
|---|---|---|
| D1 | Identificacao do carro por CAN (FPv1) ou selecao fixa "Mycar", e nao por firmware (FPv2) | `car_helpers.fingerprint()` do flowpilot pula a consulta de FW (`fw_candidates` fica vazio). As `FW_VERSIONS` foram mantidas para documentacao e para `test_fw_fingerprint`, mas em campo so valem o dicionario CAN ou o seletor. O dicionario CAN foi conferido contra a rota (`tests_windows\check_city_fingerprint.py`: 36 enderecos, 0 faltando, 0 divergentes) e a simulacao `sim_city_fp.py` mostra que as mensagens do City reduzem os 44 candidatos legados a exatamente `['HONDA CITY 7G']`. Mesmo assim, recomenda-se fixar "HONDA CITY 7G" no seletor do app (secao 8.3). |
| D2 | `HAS_EPB` e um flag detectado (0x1C2 presente no bus 0), em vez do flag de plataforma do upstream | O jag nao tem `PlatformConfig`/`HondaFlags` por plataforma; o mesmo efeito do commit 6fa346ed e obtido por deteccao. Para os Hondas Bosch que tem EPB (todos os que estao na arvore), 0x1C2 esta presente e o comportamento nao muda. Se o CAN do City nao estiver fluindo nos ~2 s de fingerprint, o flag fica desligado - que e o estado correto para o City. |
| D3 | `ki = 0.3` do controlador de torque aplicado so no ramo do City | O commit fb5ac6d3 do upstream mudou o default global; aplicar globalmente alteraria o comportamento dos outros carros desta arvore (que seguem com ki 0.1). |
| D4 | Framework de torque e o da epoca 0.9.2-0.9.4 (`latcontrol_torque.py` com `latAccelFactor`/`friction` em `torque_data`), nao a versao do v0.9.9 (torque em espaco de aceleracao, 74bfaa2c) | Os parametros do City (1.2 / 0.23) vem do `override.toml` do v0.9.9 e sao interpretados da mesma forma (lat accel factor e friction). Nao ha forma de portar 74bfaa2c sem reescrever o controlador; sinalizado como nao verificado. |
| D5 | `steerActuatorDelay = 0.15` aplicado no ramo do City, e o valor comum 0.1 movido para antes dos ramos | No jag o 0.1 era atribuido depois dos ramos, o que sobrescreveria o valor do City. Comportamento dos outros carros identico. |
| D6 | Correcao de `CarInterface.apply(c, sm, now_nanos)` em 10 marcas | Nao e do City, mas sem ela o Honda nao funciona no jag (secao 3.3). Mudanca minima e mecanica. |
| D7 | `docs/CARS.md` criado | O jag nao o tinha; necessario para `test_docs`. |
| D8 | Nenhum teste de replay de processos, nenhuma CI | O flowpilot nao tem a infraestrutura de `process_replay`; os testes possiveis foram executados com shims (secao 6). |
| D9 | Longitudinal: `openpilotLongitudinalControl = False` para o City (padrao do jag para radarless) | Mesmo estado do port v0.9.9 (radarless sem long experimental). O ACC de serie do carro continua responsavel pela velocidade. |
| D10 | `GEAR` removido da lista comum de sinais do `carstate` | O layout CVT do upstream para 0x191 nao tem o sinal `GEAR`; o jag nao o usava para nada alem de parse. Afeta todos os Hondas que usam `GEARBOX` desta mesma lista apenas no sentido de nao mais pedir um sinal que nao era lido. |

## 5. Firmware da panda preta (STM32F4)

Compilado a partir de `flowpilot\panda` (commaai/panda `abdc4185`, alvo `panda` = F4 generico com deteccao
de hardware em tempo de execucao; a panda preta e detectada por `detect_board_type()` em `board/board_declarations.h`
/ `boards/black.h`).

Comando (PowerShell, toolchain `arm-none-eabi-gcc` no PATH, venv `.venv_fp` ativo):

```
cd software\flowpilot-city-g7\panda
python -m SCons -f local_build_windows.scons -j8
```

Saidas copiadas para `..\..\firmware\prebuilt\flowpilot-black-panda\`:

| Arquivo | Tamanho | SHA256 |
|---|---|---|
| `panda.bin.signed` | 52048 B | A067B0A1109CF6BE29719964B3DBEBBFF999012DB8F87560B1177469B9D3CB02 |
| `bootstub.panda.bin` | 13936 B | C3FDFE023B8D10F366EA40E78729D7A2ED224498FD331E7AA33A1E70BCA75E76 |
| `panda.bin` | 51912 B | (nao assinado, nao usar) |
| `version` | - | `DEV-a2f1983c-DEBUG` |

Pontos importantes:

- A assinatura e feita com a chave de DEBUG (`certs/debug`), porque a chave de release da comma nao e publica.
  O bootstub de release da comma (que vem numa panda nova) REJEITA firmware assinado com a chave de debug.
  Logo, uma panda com bootstub de release precisa receber primeiro o bootstub de debug (`bootstub.panda.bin`
  acima) via DFU; a partir dai o app atualiza o firmware sozinho. Ver secao 9.
- O app do flowpilot (`wrappers/pandaflash.cpp`, chamado por `ServicePandad.java`) compara a assinatura do
  firmware em execucao com `panda/board/obj/panda.bin.signed` empacotado no APK e, se diferente, poe a panda em
  bootstub e grava so a area da aplicacao (0x8004000). Ele nunca grava o bootstub.
- O firmware compilado aqui e identico ao que o APK compilaria no Docker se o mesmo commit fosse usado (mesmo
  `SConscript`, mesmas flags); a unica diferenca possivel e a versao do GCC. O hash acima vale para o binario
  gerado nesta maquina.
- Nao houve nenhuma alteracao no firmware; o City so depende de `HONDA_BOSCH` + `RADARLESS`, ja presentes.

## 6. Testes executados no PC (Windows, Python 3.13, `.venv_fp`)

O flowpilot depende de modulos Cython e de bibliotecas compiladas (parser CAN, Params, messaging) que nao
existem no Windows. `tests_windows\fp_shims.py` registra substitutos em Python puro (parser/packer baseados em
`cantools`, Params em memoria, messaging nulo, KF1D, etc.) antes de importar o pacote. Os resultados abaixo
valem com essa ressalva: eles exercitam a logica Python do `selfdrive/car`, nao os modulos nativos.

Comando: `python tests_windows\run_car_tests.py flowpilot <args do unittest>` (logs em `tests_windows\log_*.txt`).

| Suite | Resultado | Observacoes |
|---|---|---|
| `selfdrive/car/tests/test_car_interfaces.py` | 208 executados; os 29 casos Honda/Acura passam (inclui `test_car_interfaces_144_HONDA_CITY_7G ... ok`); Toyota, GM, Ford, Chrysler, Subaru, Mazda, Nissan, Tesla, VW passam | 56 erros, todos Hyundai/Kia/Genesis: `ELECT_GEAR` sem check (enforce_checks), `CarInterface.apply` com assinatura propria do fork (`VM, c, sm, vcruise, now_nanos`), `CRUISE_INACTIVE`/`CLU11` ausentes nos DBCs - pre-existentes e independentes do City (`log_test_car_interfaces.txt`, `log_test_car_interfaces_honda.txt`) |
| `selfdrive/car/tests/test_fw_fingerprint.py` | 192 executados, 188 passam | 4 falhas sao apenas de medicao de tempo ("Performance seems to have improved, update test refs") |
| `selfdrive/car/tests/test_fingerprints.py` (script) | sem inconsistencias envolvendo o City | unica inconsistencia: CHEVROLET TRAILBLAZER 2021 com fingerprint `{}` (pre-existente) |
| `selfdrive/car/tests/test_lateral_limits.py` | 212 OK (102 pulados), City passa | exige as constantes `STEER_*` adicionadas em `275df51` |
| `selfdrive/car/tests/test_docs.py` | 7 OK (1 pulado) | precisa de `PYTHONUTF8=1` (o runner ja define) |
| `panda/tests/safety` | ver secao 7 | `test_honda.py`: 209 passam, 0 falhas |
| `tests_windows\check_city_fingerprint.py` | 36 mensagens, 0 faltando, 0 divergentes, 0 extras | compara `FINGERPRINTS[CITY_7G]` com o scan da rota |
| `tests_windows\sim_city_fp.py` | 44 candidatos legados -> `['HONDA CITY 7G']` | simula `eliminate_incompatible_cars` com as mensagens do City |
| `py_compile` de todos os arquivos tocados | OK | |

Nao existem testes de `carcontroller`/`hondacan` especificos no jag alem dos acima; nao ha `process_replay`.

## 7. Testes de safety do panda (`panda/tests/safety`)

A arvore tem `tests/safety/test_honda.py` com as classes `TestHondaBoschRadarlessSafety`,
`TestHondaBoschRadarlessAltBrakeSafety` e `TestHondaBoschRadarlessLongSafety`
(`SAFETY_HONDA_BOSCH` + `FLAG_HONDA_RADARLESS`); a primeira e exatamente a combinacao do City. Elas exigem
`tests/libpanda/libpanda.so` compilado com GCC de host (cffi). Esta maquina nao tinha compilador de host;
foi instalado o WinLibs mingw-w64 (GCC 16.2.0, UCRT, zip oficial, SHA256 conferido) em
`%LOCALAPPDATA%\winlibs-mingw64\mingw64`, fora do repositorio.

Build usado (a unica diferenca em relacao ao `tests/libpanda/SConscript` e a remocao de `-nostdlib`, que no
Windows impede o link da DLL porque `printf`/`getenv` precisam da CRT; o codigo compilado e o mesmo):

```
cd flowpilot\panda\tests\libpanda
gcc -shared -fno-builtin -std=gnu11 -Wfatal-errors -Wno-pointer-to-int-cast -w -I. -I..\..\board -o libpanda.so panda.c
```

Execucao (`tests_windows\run_panda_safety.py` instala os shims - o `CANPacker` do shim replica o
`opendbc/can/packer.cc`: COUNTER automatico e CHECKSUM de todas as familias, incluindo o de Honda - e chama
o pytest sem o xdist do `pyproject.toml`):

```
set HW_TYPE=6  (e depois 9, como em tests\safety\test.sh)
python tests_windows\run_panda_safety.py flowpilot panda\tests\safety
```

| Suite | Resultado | Log |
|---|---|---|
| `test_honda.py` completo | 209 passam, 204 pulados (classes-base abstratas e testes de regen nao aplicaveis), 0 falhas | `log_panda_safety_radarless.txt` (filtro Radarless: 79 passam, 35 pulados) |
| `tests/safety` inteiro, HW_TYPE=6 | 1968 passam, 49 falham, 1019 pulados, 58208 subtestes passam | `log_panda_safety_hw6.txt` |
| `tests/safety` inteiro, HW_TYPE=9 | 1968 passam, 49 falham, 1019 pulados | `log_panda_safety_hw9.txt` |

As 49 falhas sao todas de outras marcas e tem a mesma causa: os testes do panda `abdc4185` foram escritos
para um opendbc mais novo do que o que o flowpilot carrega (`opendbc/` do jag). Casos: Toyota
`TestToyotaSecOcSafety` (30) exige `toyota_rav4_prime_generated.dbc`, que nao existe na arvore; Toyota LTA (4)
usa o sinal `TORQUE_WIND_DOWN`, ausente no DBC; Hyundai CAN FD `HDA2EVAltSteering` (8) usa `LKAS_ALT`/`ECM_5`;
Tesla Raven (3) usa `EPAS3P_sysStatus`; Subaru longitudinal (4) depende de `Cruise_Throttle` com 13 bits
(aqui 12). Em Linux, com o parser nativo, essas mesmas 49 falham pelo mesmo motivo. Nenhuma falha envolve
Honda, e nenhum arquivo de safety foi alterado.

## 8. Compilar e instalar o APK no Poco F3

### 8.1 Compilar (Linux ou WSL2 com Docker; nao e possivel nesta maquina Windows)

```
git clone <fork do dono>/flowpilot -b flowpilot-city-g7-brazil
cd flowpilot
scripts/build.sh full        # usa a imagem Docker do jag; compila nativos, panda fw e o APK
# saida: android/app/build/outputs/apk/release/android-release.apk
```

O `scripts/build.sh` do jag compila tambem `panda/board/obj/panda.bin.signed` dentro do Docker; esse binario
e o que vai no APK e e o que o app grava na panda. Conferir que o hash dele coincide com o de
`..\..\firmware\prebuilt\flowpilot-black-panda\panda.bin.signed` (secao 5); se o GCC do Docker for diferente, o hash muda sem mudar o
comportamento, mas nesse caso a panda sera regravada pelo app na primeira conexao (normal).

### 8.2 Instalar no Poco F3 (Android 11-13, MIUI/HyperOS)

1. Ativar Opcoes do desenvolvedor (tocar 7x em "Versao do MIUI"), ligar "Depuracao USB" e "Instalar via USB"
   (MIUI exige conta Xiaomi logada para "Instalar via USB"; alternativa: copiar o APK e instalar pelo gerenciador
   de arquivos com "Fontes desconhecidas" permitido).
2. No PC: `adb install -r android-release.apk`.
3. Desligar otimizacao de bateria para o app (Configuracoes > Apps > flowpilot > Economia de bateria > Sem
   restricoes) e permitir "Iniciar em segundo plano"/"Exibir pop-ups" (MIUI mata servicos sem isso).
4. Conectar a panda por cabo USB-C OTG (USB-A femea -> panda). No primeiro plug o Android pergunta permissao
   de acesso USB ao app; marcar "usar por padrao".
5. O app precisa de GPS/camera; conceder as permissoes quando pedidas.

Requisitos do dispositivo: o jag documenta Android 9+, 64 bits, OpenCL. O Poco F3 (Snapdragon 870, Adreno 650)
atende aos requisitos nominais; nao ha relato especifico desse aparelho nos issues (ver `flowpilot-scope.md`).

### 8.3 Selecionar o carro

Configuracoes do app > "Car" (lista vinda de `selfdrive/assets/allcars.txt`) > `HONDA CITY 7G`. Isso grava o
param `Mycar`, que `car_helpers.fingerprint()` usa como fingerprint fixo (o CAN continua sendo lido durante
~1-2 s para preencher o dicionario `fingerprint` usado por `interface.py` para detectar CVT/EPB/0x33DA).
Alternativa: deixar sem selecao e confiar no dicionario CAN (D1). Em ambos os casos a ignicao precisa estar
ligada e o CAN fluindo antes de o app iniciar o `controlsd`.

### 8.4 APK compilado (GitHub Actions)

Workflow "Build" do repo kriptomad/flowpilot-city-g7, branch `flowpilot-city-g7-brazil`:

- Run: 40697331404 (2026-10-28), commit `ffd228c`.
- Artefato `android-release.apk`, copiado para `software/flowpilot-port/apk_out/android-release.apk` e publicado no release
  `v0.1-city-g7-brazil` como `flowpilot-city-g7-brazil-ffd228c.apk` (+ `SHA256SUMS.txt`).
- Tamanho: 235.399.803 bytes. SHA256: `493891cd62d3f2eaf094e414489d7b0dae8bde297a673c305fba6eef298d4adb`.
- Conteudo verificado: `assets/private.tar` (18,5 MB, 797 entradas: selfdrive/, panda/, opendbc/, common/, cereal/,
  system/, rednose/, flowreset.pyc, messaging_pyx.so, acados_ocp_solver_pyx.so), `lib/arm64-v8a` com libmessaging,
  libpandad, libpandaflash, libthneedrunner, libmodelparser, libusb-1.0, liblmdb, libjson11, libpython3.11;
  `assets/allcars.txt` contem `HONDA CITY 7G`. Nao testado no celular nem no carro.
- O APK anterior (run 40683947737, commit `d079568`) estava incompleto (sem arvore Python e sem as libs do scons,
  travava em "Booting Flowpilot") e foi removido do release.

Causas raiz corrigidas no branch (a importacao por tarball e a deriva do toolchain desde 2025-03):

- `d079568`: `build>=1.4.3` (pypa) limpa o PYTHONPATH do ambiente PEP 517 e quebra o hostpython do p4a
  (`_posixsubprocess`/mesonpy no numpy) -> `PIP_CONSTRAINT` com `build==1.2.2`, `virtualenv==20.29.3`.
- `41801d8`: 16 symlinks (`flowy/src/{cereal,common,opendbc,panda,rednose,selfdrive,system}`, `laika`, `rednose`,
  kernels do modeld, aliases libqpOASES_e) e arquivos ignorados (`panda/board/obj/.placeholder`,
  `third_party/CL/libOpenCL.so`, ...) perdidos no tarball -> restaurados; CI confere as libs nativas.
- `973e185`: buildozer 1.6.0 instala `cython<3`, que os headers Cython do numpy 2 rejeitam -> venv com
  `cython==3.0.12` e `numpy==2.2.3`.
- `ffd228c`: bit de execucao perdido em 164 arquivos (`panda/crypto/sign.py`, `third_party/acados/*/t_renderer`).

Pins do toolchain em vigor: p4a develop `b0efb9f3`, `android.ndk = 25b`, Python 3.11.5 (host e alvo),
buildozer 1.6.0, Cython 3.0.12 + numpy 2.2.3 no venv do Docker (ubuntu:24.04), `build==1.2.2`,
`virtualenv==20.29.3`, no alvo numpy 1.26.5, setuptools 69.2.0, pycapnp 2.0.0, capnp 1.0.1, libzmq 4.3.5,
pyzmq 25.1.2, casadi 3.8.2 (venv) / acados_template 0.2.2. Nao restaurado: `libs/linux/x86_64/*.so` (so desktop).

## 9. Gravar a panda preta - passo a passo

Hardware: panda preta (STM32F413), chicote Bosch B ligado no carro, cabo USB. Primeira gravacao no PC
(Windows ou Linux); depois o celular mantem o firmware atualizado.

### 9.1 Primeira vez (PC) - bootstub de debug + firmware via DFU

Necessario porque a panda vem com bootstub de release (secao 5).

1. Instalar driver WinUSB para o modo DFU (`0483:df11`) com Zadig, se for Windows. No Linux, regras udev do
   `panda/board/` ou rodar como root.
2. Com o venv ativo: `pip install pyusb libusb1`.
3. Colocar a panda em DFU: desconectar, manter o botao de boot pressionado (ou curto entre BOOT0 e 3V3 nas
   pandas sem botao) e conectar o USB; ou, se ja houver firmware funcional, `python -c "from panda import Panda; Panda().reset(enter_bootloader=True)"`.
4. Gravar o bootstub (a partir da raiz `flowpilot\`, com `panda\board\obj\` ja compilado pela secao 5).
   `PandaDFU.recover()` apaga os setores 0 e 1, grava `bootstub.panda.bin` em 0x8000000 e salta para ele;
   ele NAO grava a aplicacao:

```
python -c "from panda import PandaDFU; PandaDFU(None).recover()"
```

   A placa reenumera como bootstub (`bbaa:ddee`; no Windows, Zadig/WinUSB de novo). Em seguida gravar a
   aplicacao (`panda.bin.signed`, 0x8004000):

```
python -c "from panda import Panda; Panda().flash()"
```

   Equivalente no Linux: `python board/recover.py` seguido de `python board/flash.py` (ambos chamam `scons`
   antes). Passo a passo completo, incluindo a placa do Lukas (SW1 = BOOT0) e as tres arvores de firmware:
   `docs\flashing\flash-black-panda-city-g7.pt-br.md`.
5. Reconectar e verificar: `python -c "from panda import Panda; p=Panda(); print(p.get_type(), p.get_version(), p.get_signature().hex()[:16])"`.
   Esperado: tipo `b'\x03'` (black), versao `DEV-a2f1983c-DEBUG`.

### 9.2 Atualizacoes seguintes (celular)

Nada a fazer: ao conectar a panda, `ServicePandad` executa `pandaflash` que compara a assinatura do firmware
em execucao com a do `panda.bin.signed` do APK e regrava a aplicacao se for diferente. Como o bootstub ja e de
debug, qualquer build do APK (sempre assinado com a chave de debug) sera aceito.

### 9.3 Conferencia no carro (nao executada)

- Com ignicao ligada, o app deve mostrar o carro reconhecido como "HONDA CITY 7G".
- Verificar no log (`adb logcat | grep -i fingerprint`) a linha `fingerprinted` com `source=fixed` ou `can`.
- Antes de qualquer tentativa de engate, confirmar que a panda esta em `SAFETY_HONDA_BOSCH` com parametro 8
  (`p.health()`, campo `safety_mode`/`safety_param`).

## 10. Lista do que NAO foi verificado

Tudo abaixo esta pendente de verificacao real. Nenhum item foi exercitado em carro, celular ou panda fisica.

1. Comportamento em carro: reconhecimento, engate, controle lateral por torque com [1.2, 0.23] + ki 0.3 no
   framework antigo (D4), steerActuatorDelay 0.15, marcha S, ausencia de EPB, limite de 600 em
   `STEER_THRESHOLD`, LKAS HUD sem 0x33DA.
2. Fingerprint CAN em campo (D1): o dicionario reproduz a rota 56b2cf1dacdcd033/17; outro carro/outra versao
   de software pode ter mensagens a mais no bus 0, o que eliminaria o candidato - por isso a recomendacao de
   fixar "Mycar".
3. Deteccao de `HAS_EPB` em tempo de execucao (D2) e de CVT (0x191 em `fingerprint[0]` quando o fingerprint
   e fixo).
4. APK nao compilado: nenhum teste de que `scripts/build.sh full` do jag ainda funciona em 2026 (imagens
   Docker, NDK, dependencias Python), nem de que o Poco F3 roda o app (OpenCL, camera, modelo).
5. Firmware da panda: compilado mas nao gravado nem executado em hardware; a assinatura de debug e o fluxo
   DFU da secao 9 sao os descritos no codigo, nao testados aqui.
6. `pandaflash.cpp` com a panda preta via OTG no Poco F3 (permissao USB, libusb no Android).
7. Testes de safety do panda: `TestHondaBoschRadarlessSafety` passa no PC com `libpanda.so` compilado pelo
   mingw-w64 (secao 7); isso exercita o mesmo `safety_honda.h` que vai para a panda, mas compilado para x86-64,
   nao o binario ARM gravado. As 49 falhas restantes (outras marcas) vem do descompasso entre o opendbc do
   flowpilot e os testes do panda `abdc4185`.
8. Modulos nativos (parser CAN Cython, Params, messaging): os testes rodaram com shims; a unica garantia e que
   a logica Python e consistente com o DBC. O DBC gerado foi carregado pelo `cantools` e pelo shim sem erro.
9. Falhas pre-existentes do jag nao tratadas (fora do escopo City): Hyundai/Kia/Genesis em
   `test_car_interfaces` (assinatura propria de `apply`, `ELECT_GEAR` sem check, DBCs sem `CRUISE_INACTIVE`/
   `CLU11`), Trailblazer com fingerprint vazio, e as 49 falhas de safety de outras marcas descritas na secao 7.
10. Qualidade do modelo de visao / desempenho no Snapdragon 870: nao avaliada.
11. O flag `HAS_EPB` e detectado em tempo de execucao; para os demais Hondas Bosch da arvore ele depende de
    0x1C2 aparecer durante a janela de fingerprint (nao foi possivel testar em carro que isso ocorre sempre).

## 11. Estrutura da pasta `software\flowpilot-port\`

| Caminho | Conteudo |
|---|---|
| `flowpilot-scope.md` | Fase A (pesquisa, versoes, compatibilidade, lacunas G1-G12) |
| `port-city-flowpilot.md` | este documento |
| `flowpilot\` | repositorio (branch `flowpilot-city-g7-brazil`) |
| `..\..\firmware\prebuilt\flowpilot-black-panda\` | firmware F4 compilado + `SHA256SUMS.txt` |
| `tests_windows\` | shims (`fp_shims.py`), runners (`run_car_tests.py`, `run_panda_safety.py`, `run_script.py`), scripts de conferencia e logs |
| `.venv_fp\` | venv Python 3.13 usado para build e testes |
| `api_cache\` | respostas da API do GitHub usadas na Fase A |
| `%LOCALAPPDATA%\winlibs-mingw64\` | GCC de host usado so para `libpanda.so` (fora da pasta do projeto) |
