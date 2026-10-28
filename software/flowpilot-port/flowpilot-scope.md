# flowpilot-scope.md - Fase A: pesquisa e escopo do port do Honda City G7 2023 (BR) para flowpilot

Data da pesquisa: 2026-10-27. Fonte: API do GitHub (`gh api`), READMEs e wikis dos
repositorios, codigo-fonte baixado por API (copias em `api_cache\`). Nada aqui foi
testado em carro ou em telefone; ver secao 9 (nao verificado).

Alvo do dono: Honda City G7 2023 (Brasil) + Xiaomi Poco F3 (Snapdragon 870, Android 11-13)
+ black panda (STM32F4). Base ja existente: port fiel do City em openpilot v0.9.9
(`software\openpilot-port\`, relatorios `../openpilot-port/auditoria-port-city-v099.md`,
`../openpilot-port/audit2/auditoria2-independente.md`, `../openpilot-port/readme.md`).

## 1. Estado do projeto flowpilot

### 1.1 Repositorio original: flowdriveai/flowpilot

| Item | Valor |
|---|---|
| URL | https://github.com/flowdriveai/flowpilot |
| Branch padrao | `master` |
| Ultimo release | v0.2.4 (premium), 2023-08-24 |
| Releases anteriores | v0.0.1 (2022-09) ... v0.2.3 |
| Ultimo commit com codigo | 2024-05 (apenas bumps de `requirements`) |
| `FLOWPILOT_VERSION` | "0.2.3" |
| Origem | hard-fork de openpilot commit `05b37552f3a38f914af41f44ccc7c633ad152a15` (openpilot ~0.8.13/0.8.14, 2022) |
| Submodulo `panda` | commaai/panda `f120999e` (2022-09-15) |
| Submodulo `opendbc` | flow-drive-ai/opendbc `7d966b5c` (2022-09; ja contem `honda_civic_ex_2022_can_generated.dbc`) |
| Submodulo `cereal` | 2023-06 |
| Instalacao Android | APK + termux/proot (ambiente Linux dentro do Android), com um "flowinit" que instala o ambiente python |
| Status | **abandonado**. README diz que os desenvolvedores nao tem tempo e aponta para o fork phr00t |

Conclusoes: nao ha CI, nao ha process replay, nao ha manutencao. O codigo de carro e
de ~openpilot 0.8.x; nao tem controle lateral por torque (`latcontrol_torque.py`) na
forma usada pelo City em v0.9.9, nem fingerprint por FW em producao.

### 1.2 Forks mais recentes (busca `gh search repos flowpilot --sort updated` + inspecao)

| Fork | Ultimo commit | O que muda | Relevancia para o City |
|---|---|---|---|
| hamidi2/flowpilot | 2026-08 | Correcoes de build Linux | nenhuma (sem Honda) |
| PiotrTopa/priuspilot | 2024 | Toyota Prius | nenhuma |
| ValKara01/flowpilot | 2024 | Ford | nenhuma |
| **phr00t/flowpilot** | 2024-06-10 (60 estrelas) | Tarball para LG G8; `panda`/`opendbc`/`cereal` achatados dentro da arvore (sem submodulos); wiki/FAQ | FAQ: "I have seen it running on a Xiaomi Poco F3"; exige Snapdragon 855+, Android 11+; recomenda o fork jagheterfredrik como "o futuro" |
| **jagheterfredrik/flowpilot** | 2025-03-04, master `9ea918ea` ("check for both panda vendor IDs and product IDs"), 42 estrelas | Fork do phr00t. APK unico (`android-release.apk`), sem root/termux. Releases alpha1..alpha5 (nov/2024). Build por Docker (`scripts/build.sh full` -> scons + buildozer pacote python `flowy` + gradle). Panda achatada em commaai/panda `abdc4185` (2024-10-04). Camada de carro ~openpilot 0.9.2-0.9.4 | **Base escolhida** (ver 1.3) |

Nenhum fork encontrado adiciona Honda City ou Honda radarless alem do CIVIC_2022 que
ja veio do upstream.

### 1.3 Base escolhida: jagheterfredrik/flowpilot master `9ea918ea`

Motivos:
1. Unico caminho de instalacao sem root/termux (APK) e com evidencia de funcionar
   em Poco F3 (via linha phr00t, da qual e fork).
2. Panda `abdc4185` (2024-10) e a mais nova entre os forks: tem `board/boards/black.h`,
   `safety_honda.h` com `HONDA_PARAM_RADARLESS` e `HONDA_PARAM_BOSCH_LONG`,
   protocolo CAN v4 / HEALTH v16 / CAN_HEALTH v5.
3. Camada de carro ja tem `HONDA_BOSCH_RADARLESS`, `CIVIC_2022`, `HRV_3G`,
   `torque_data/{params,override,substitute}.yaml`, `latcontrol_torque.py`,
   `configure_torque_tune`, cereal `LateralTorqueTuning` e `GearShifter.sport`.

Limitacoes aceitas:
- Fork pequeno (1 mantenedor), sem CI, ultimo commit 2025-03. Historico git nao foi
  obtido (clone trava no proxy corporativo); a arvore foi importada por tarball do
  `master` como snapshot (commit de importacao local). O dono deve criar o fork a
  partir de `jagheterfredrik/flowpilot@9ea918ea` e aplicar os commits locais por cima.

## 2. Camada panda

### 2.1 flowdriveai (panda `f120999e`, 2022-09)
- `python/__init__.py`: CAN packet v2 (sem checksum v4), `health` v? (2022), flags
  Honda `HONDA_ALT_BRAKE`/`BOSCH_LONG`/`NIDEC_ALT`; `safety_honda.h` de 2022-09 **ja**
  tem `HONDA_PARAM_RADARLESS` (introduzido em 2022-08 para o Civic 2022), mas nao
  tem o tratamento posterior de 0x1AB/`STEER_MOTOR_TORQUE` nem as correcoes de 2023+.
- Incompativel com o firmware v0.9.9 (protocolo CAN diferente). Descartado junto com
  a base flowdriveai.

### 2.2 jagheterfredrik (panda `abdc4185`, 2024-10-04, achatada em `flowpilot/panda/`)
- `python/__init__.py`: `CAN_PACKET_VERSION = 4`, `HEALTH_PACKET_VERSION = 16`,
  `CAN_HEALTH_PACKET_VERSION = 5`; `FLAG_HONDA_ALT_BRAKE=1`, `FLAG_HONDA_BOSCH_LONG=2`,
  `FLAG_HONDA_NIDEC_ALT=4`, `FLAG_HONDA_RADARLESS=8`; `flash()`, `recover()`,
  `can_send_many`, assinatura de firmware (`get_signature` vs `get_signature_from_firmware`).
- `board/safety/safety_honda.h`: `HONDA_PARAM_RADARLESS`, listas TX radarless
  `{0xE4,0,5},{0x296,2,4},{0x33D,0,8}` + long `{0x1C8,0,8},{0x30C,0,8}`;
  `HONDA_BOSCH` + `HONDA_BOSCH_LONG`. Igual, no essencial, ao `opendbc/safety`
  usado em v0.9.9 para o City (mesmos IDs e DLCs; ver AUDITORIA secao 6).
- `board/boards/black.h` presente; `board/SConscript` gera `panda` (F4) e `panda_h7`.
- Fluxo de flash no app: `ServicePandad.java` -> `libpandaflash` ->
  `PythonRunner.run(0, app_root + "/panda/board/obj/")`: **o app regrava a panda
  automaticamente** se a assinatura do firmware da placa diferir da do firmware
  embutido no APK. Firmware nao assinado (sem chave da comma), igual ao nosso build.

### 2.3 Veredito de compatibilidade
- Firmware v0.9.9 (panda `e462c34d` + opendbc/safety) usa tambem CAN v4 / HEALTH 16 /
  CAN_HEALTH 5 (verificado em `hardware\reference\panda_legacy_f4`), portanto a lib python do
  jag conseguiria falar com ele. **Porem e irrelevante**: o app regrava a panda com o
  firmware da propria arvore. Logo o firmware **tem de ser construido da arvore
  `flowpilot/panda`** (alvo F4 `panda`), e e esse que vai no APK. Nosso toolchain
  `arm-none-eabi-gcc` em Windows ja compilou F4 antes (`hardware\research\pandarevive-scope.md`,
  `../../hardware/research/local-build-windows.scons`).
- Safety: `HONDA_BOSCH` com param `RADARLESS (8)` existe na arvore jag. Nao e preciso
  portar codigo de safety; e preciso garantir que `interface.py` do City envie
  `safetyParam |= FLAG_HONDA_RADARLESS` (o codigo generico do radarless ja faz isso
  para o conjunto `HONDA_BOSCH_RADARLESS`).

## 3. Camada de carro (arvore jag, `selfdrive/car/honda/`)

| Item | flowdriveai (0.8.x) | jag (0.9.2-0.9.4) | City v0.9.9 precisa |
|---|---|---|---|
| `CAR` enum | strings | strings (`CAR.CIVIC_2022 = "HONDA CIVIC 2022"`) | adicionar `CAR.CITY_7G = "HONDA CITY 7G"` |
| Radarless | nao | `HONDA_BOSCH_RADARLESS = {CIVIC_2022, HRV_3G}` | adicionar City |
| DBC `honda_civic_ex_2022_can_generated` | sim | sim | OK; precisa layout `GEARBOX_CVT` em BO_ 401 |
| Fingerprint | CAN legado + FW | `car_helpers.py` **pula** consulta de FW e VIN; fingerprint = CAN legado (`FINGERPRINTS`) ou fixo (`FINGERPRINT` env / param `Mycar` de `allcars.txt`) | FW_VERSIONS (6 ECUs) para doc/testes + **fingerprint CAN** derivado do rlog + entrada em `allcars.txt` |
| EPB (0x1C2) | n/a | radarless adiciona `EPB_STATUS` incondicionalmente (carstate 81-82, 230) | **condicional** (upstream 6fa346ed): City nao tem 0x1C2 |
| Marcha (0x191) | GEARBOX byte0 one-hot | idem | City e CVT com layout `GEARBOX_CVT` (byte5 `44|5@0+`, 1P 2R 3N 4D 7L 10S): patch no gerador + regenerar |
| Marcha S | - | cereal tem `sport`; verificar `wrongGear` em controlsd | aceitar S |
| Controle lateral torque | nao | sim (`latcontrol_torque.py`, `configure_torque_tune`, `override.yaml`) | `latAccelFactor 1.2, friction 0.23, ki 0.3`, `steerActuatorDelay 0.15` |
| 0x1AB STEER_MOTOR_TORQUE 50 Hz | - | DBC e checks existentes | verificar frequencia esperada no carstate |
| 0x33DA BSM | - | nao usado por radarless | nada |
| STEER_THRESHOLD | 1200 | dict por carro | 600 para City |
| CarParts / harness | nao | `CarParts`, `Harness.bosch_b` | `HondaCarInfo("Honda City 2023", ..., harness bosch_b)` |
| docs/CARS.md | - | verificar `selfdrive/car/docs.py` | regenerar se existir |
| Testes | - | `selfdrive/car/tests/{test_models,test_car_interfaces,test_fw_fingerprint,test_fingerprints,test_docs,test_lateral_limits,routes}.py`, `panda/tests/safety` | rodar em venv; adicionar rota do City |

## 4. Lista de lacunas (gap list) e classificacao

Mapeamento com os commits upstream da tabela de 73 commits em
`../openpilot-port/auditoria-port-city-v099.md` secao 2 (so os que afetam o City; os demais ja estao
no upstream da arvore jag ou nao se aplicam).

| # | Lacuna | Commit(s) upstream (opendbc/openpilot) | Classe | Esforco | Risco |
|---|---|---|---|---|---|
| G1 | `CAR.CITY_7G`, CarInfo, conjuntos HONDA_BOSCH/RADARLESS, DBC, STEER_THRESHOLD 600 | `values.py` do port (HONDA_CITY_7G HondaBoschPlatformConfig) | backport direto (adaptacao de sintaxe 0.9.3) | baixo | baixo |
| G2 | FW_VERSIONS do City (6 ECUs) | `fingerprints.py` do port | backport direto | baixo | baixo (nao usado em runtime no jag) |
| G3 | Fingerprint CAN legado + `allcars.txt` | nao existe upstream (upstream usa FW) | **adaptacao**: derivar `{addr: dlc}` do bus 0 do rlog `56b2cf1dacdcd033/00000017` | baixo | medio: fingerprint CAN e fragil (opcionais, versoes); mitigado pelo `Mycar` fixo |
| G4 | Tune torque (1.2 / 0.23 / ki 0.3), delay 0.15 | `override.toml` + `interface.py` do port | backport direto (`override.yaml`, `configure_torque_tune`) | baixo | baixo |
| G5 | `GEARBOX_CVT` em `honda_civic_ex_2022_can` BO_ 401 | opendbc `audit2\proposed-patches\0001-*.patch` (upstream Civic/HRV CVT) | adaptacao (gerador do opendbc jag + regenerar) | medio | medio: afeta CIVIC_2022/HRV_3G (igual ao upstream, que tambem usa CVT nesses) |
| G6 | `HAS_EPB` condicional (sem 0x1C2) | openpilot 6fa346ed | adaptacao (flag por presenca de 0x1C2 no fingerprint) | baixo | baixo |
| G7 | Marcha S aceita | openpilot (GearShifter sport) | verificar/ajustar | baixo | baixo |
| G8 | `transmissionType = cvt` quando 0x191 presente, `minSteerSpeed 23 km/h` | `interface.py` do port | backport direto | baixo | baixo |
| G9 | Firmware panda F4 (black) a partir de `flowpilot/panda` | panda `abdc4185` | build local Windows (scons + arm-none-eabi) | medio | medio: build Windows exige shim; APK e montado por Docker no Linux |
| G10 | Testes (car tests, safety tests) | - | rodar em `.venv_fp` (python 3.11 preferivel; so 3.13 instalado) | medio | medio: deps antigas podem nao instalar em 3.13; safety tests precisam de libpanda (gcc/clang) |
| G11 | docs CARS.md + rota de teste | `routes.py`, `docs.py` | backport direto se infra existir | baixo | baixo |
| G12 | Build do APK e instalacao no Poco F3 | - | documentar (Docker `build.sh full` + `adb install`) | - | alto (nao executavel nesta maquina: sem Docker/Android SDK) |

Bloqueios de framework: **nenhum absoluto**. Torque control e radarless existem na
arvore jag; fingerprint por FW nao e usado em runtime (adaptacao G3).

Esforco total estimado: 2-3 dias de trabalho de engenharia + validacao em carro
(nao feita aqui).

## 5. O que a abandonment implica
- Sem CI, sem process replay, sem comparacao com rotas. Os unicos testes sao os
  unitarios que ja existem na arvore (`selfdrive/car/tests`, `panda/tests/safety`).
- Qualquer bug do flowpilot (modelo, camera, UI, latencia) nao sera corrigido por
  terceiros.
- A camada panda/safety e de 2024-10, portanto razoavelmente recente; o restante
  (controlsd, modelo) e de 2022-2023.

## 6. Build e instalacao (Poco F3) - resumo do que foi apurado (nao executado)
- APK: `scripts/build.sh full` em Docker (Ubuntu); gera `android/app/build/outputs/apk/release/android-release.apk`.
- Instalacao: `adb install -r android-release.apk`; na primeira execucao o app pede
  permissao USB (OTG) para a panda e regrava o firmware automaticamente.
- Requisitos: Snapdragon 855+ (Poco F3 = 870), Android 11+, OTG. Evidencia de Poco F3:
  FAQ do phr00t. Nenhum relato sobre HyperOS.

## 7. Decisao
Fase B prossegue na arvore jag, branch local `flowpilot-city-g7-brazil`, sem push.
Detalhes do port em `port-city-flowpilot.md`.

## 8. Arquivos de referencia
- `api_cache\` - copias dos arquivos consultados por API (flowdriveai e jag).
- `..\software\openpilot-port\auditoria-port-city-v099.md` - fatos do City.

## 9. Nao verificado
- Funcionamento do flowpilot (qualquer versao) em Poco F3 com MIUI/HyperOS.
- Build do APK (Docker nao disponivel nesta maquina).
- Qualquer comportamento em carro.
