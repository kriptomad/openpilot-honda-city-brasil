# Gravar uma panda preta (STM32F413) para o Honda City G7 2023 (Brasil)

Passo a passo para colocar o firmware do fork numa panda preta recem montada, de modo que ela
funcione com o port do Honda City G7. Versao em ingles: `flash-black-panda-city-g7.md`.

Situacao: este procedimento NAO foi executado em hardware real ainda. Foi escrito a partir do
codigo dos repositorios abaixo e dos arquivos da PCB. Trate cada passo como "esperado", nao
como "verificado", ate a primeira placa ser gravada.

## 0. Caminho rapido da opcao A (APK do flowpilot + panda preta do Loetkolben)

Windows PowerShell, Python 3.11+ instalado. Tudo abaixo esta explicado em detalhe nas secoes
seguintes; aqui e so a ordem das operacoes.

```
git clone -b flowpilot-city-g7-brazil --depth 1 https://github.com/kriptomad/flowpilot-city-g7.git
git clone --depth 1 https://github.com/kriptomad/openpilot-honda-city-brasil.git hub
cd flowpilot-city-g7
pip install libusb1 pyusb

# 1. segure SW1, conecte o USB-C, solte. Zadig: 0483:df11 -> WinUSB
python -c "from panda import PandaDFU; print(PandaDFU.list())"
python -c "from panda import PandaDFU; PandaDFU(None).recover()"

# 2. a placa volta como bbaa:ddee. Zadig: WinUSB
python -c "from panda import Panda; Panda().flash(fn=r'..\hub\firmware\prebuilt\flowpilot-black-panda\panda.bin.signed')"

# 3. a placa volta como bbaa:ddcc. Zadig: WinUSB
python -c "from panda import Panda; p=Panda(); print(p.get_type(), p.get_version(), p.health()['uptime'])"
# esperado: b'\x03' DEV-a2f1983c-DEBUG <numero>
```

Depois desconecte do PC, conecte no celular com o cabo OTG e abra o app do flowpilot; ele
regrava a area da aplicacao sozinho se o APK trouxer um build mais novo.

## 1. O que e necessario

| Item | Observacoes |
|---|---|
| PCB da panda preta | "Open Source BlackPanda" v2 do Lukas Loetkolben (OpenpilotHardware/BlackPanda), STM32F413RGT6 (U7). `SW1` liga `BOOT0` ao 3V3 (botao de DFU), `R14` e o pull-down. `NRST` nao vai a nenhum botao. |
| Harness box + chicote do carro | OpenpilotHardware/HarnessBox + chicote Honda Bosch **B** (o City G7 e Bosch radarless). |
| Cabo USB | USB-C com dados ate o PC para a primeira gravacao; USB-C OTG para o celular depois. |
| PC | Windows 10/11 ou Linux, Python 3.11+ (3.13 funciona), `pip install libusb1 pyusb`. |
| So no Windows | Zadig (https://zadig.akeo.ie) para associar WinUSB a `0483:df11` (DFU da ST), `bbaa:ddee` (bootstub da panda) e `bbaa:ddcc` (aplicacao da panda). |
| So no Linux | regras udev do README da panda (`/etc/udev/rules.d/11-panda.rules`, VIDs `bbaa`/`3801`, PIDs `ddcc`/`ddee`) mais `0483:df11` para o DFU, ou rodar como root. |

## 2. Escolher o firmware: tres arvores, nao intercambiaveis

O City G7 nao exige nenhuma alteracao dentro do firmware da panda: o carro e coberto por
`SAFETY_HONDA_BOSCH` com a flag radarless, que todas as arvores abaixo ja tem. O que muda e a
**versao do protocolo** que o firmware fala com o software do outro lado do cabo USB (pacote
de health, pacote CAN, requests de controle USB). Grave a arvore que corresponde ao software
que voce vai rodar.

| Opcao | Usar com | Fonte | Binarios prontos |
|---|---|---|---|
| **A - flowpilot** (celular) | APK de `kriptomad/flowpilot-city-g7` (branch `flowpilot-city-g7-brazil`) | pasta `panda/` dentro desse repo (commaai/panda `abdc4185`, alvo F4 generico `panda`) | hub repo `firmware/prebuilt/flowpilot-black-panda/` (`panda.bin.signed` SHA256 `A067B0A1...3CB02`, `bootstub.panda.bin` `C3FDFE02...75E76`, versao `DEV-a2f1983c-DEBUG`) |
| **B - port openpilot 0.9.9** (dispositivo tipo comma ou PC) | `kriptomad/openpilot@v0.9.9-cityg7-blackpanda` | submodulo `panda` desse branch (commaai/panda `e462c34d`, ultimo upstream com suporte nativo a panda preta) | nenhum aqui. `scons -j8 panda` na raiz do openpilot gera `panda/board/obj/`; o `pandad` do openpilot tambem grava sozinho ao iniciar |
| **C - pandarevive** (este branch `revive-f4`) | futuro openpilot master + panda preta; o lado openpilot ainda esta pendente (`hardware/research/pandarevive-scope.md` secao 7) | `kriptomad/panda@revive-f4` (STM32F4 restaurado no panda master atual, alvo `panda`) | hub repo `firmware/prebuilt/revive-f4-black-panda/` (`panda.bin.signed` SHA256 `EB07FF3F...991AF`, `bootstub.panda.bin` `3C49135B...EB221`, versao `DEV-e78c41e6-DEBUG`) |

Hub repo = `kriptomad/openpilot-honda-city-brasil` (este repositorio).

Neste momento o caminho celular/flowpilot e o que esta em teste, entao **use a opcao A**. A
opcao C so faz sentido para testes de bancada do proprio firmware (enumeracao USB, `health()`,
loopback CAN) enquanto o lado openpilot do pandarevive nao existe. Para trocar de arvore
depois, repita o procedimento completo de DFU (secao 5); nao basta regravar a aplicacao.

Todas as arvores sao assinadas com a chave publica de **debug** da comma (`certs/debug`). Nosso
bootstub aceita aplicacoes assinadas com debug; um bootstub de release da comma nao aceitaria,
o que e irrelevante aqui porque a placa comeca vazia.

## 3. (Opcional) compilar os binarios

Pule se for usar os arquivos prontos da tabela acima.

### 3.1 Opcao A (arvore do flowpilot)

```
# Linux / WSL2 (precisa de gcc-arm-none-eabi e scons)
cd flowpilot
scons -j8 panda            # gera panda/board/obj/{bootstub.panda.bin,panda.bin.signed}

# Windows (PowerShell, arm-none-eabi-gcc no PATH, venv do repo ativo)
cd flowpilot\panda
python -m SCons -f local_build_windows.scons -j8   # helper versionado no fork do flowpilot; original em hardware/research/local-build-windows.scons
```

### 3.2 Opcao B (arvore do openpilot 0.9.9)

```
# Linux / WSL2, dentro do clone do openpilot (submodulos baixados, toolchain instalada)
scons -j8 panda            # gera panda/board/obj/{bootstub.panda.bin,panda.bin.signed}
```

### 3.3 Opcao C (este branch, `revive-f4`)

Requisitos: `arm-none-eabi-gcc` no PATH, `scons` e o pacote `opendbc` importavel
(`pip install -e <clone do opendbc>` ou `PYTHONPATH=<clone do opendbc>`; os headers de safety
vem de `opendbc.INCLUDE_PATH`).

```
# Linux / WSL2
cd panda
scons -j8                  # compila panda (F4), panda_h7, body_h7 e tests/libpanda

# Windows (PowerShell)
cd panda
$env:PATH = "<toolchain>\bin;" + $env:PATH
$env:PYTHONPATH = "<clone do opendbc>"
python -m SCons -j8 board
# As ultimas linhas reclamam que tests/libpanda nao consegue gerar .dll no Windows. E so a
# biblioteca de teste do lado do PC; o firmware em board\obj\ esta completo.
```

Saidas: `board/obj/bootstub.panda.bin` (bootstub, 0x08000000) e `board/obj/panda.bin.signed`
(aplicacao, 0x08004000). `board/obj/version` guarda a string de versao (`DEV-<git>-DEBUG`).

## 4. Preparar o lado Python no PC

Cada arvore traz o pacote Python `panda` junto com o firmware; use o da arvore escolhida para
que `FW_PATH` aponte para o `board/obj/` certo.

```
pip install libusb1 pyusb

# Opcao A: rodar a partir da raiz do repo flowpilot (o pacote e flowpilot/panda)
cd flowpilot

# Opcao B: rodar a partir da raiz do repo openpilot (o pacote e openpilot/panda)
cd openpilot

# Opcao C: instalar este branch em modo editavel
cd panda
pip install -e .
```

Teste rapido (ainda sem placa conectada):

```
python -c "from panda import Panda, PandaDFU; print(Panda.list(), PandaDFU.list())"
# esperado: [] []
```

Windows: na primeira vez que cada identidade USB aparecer (`0483:df11`, `bbaa:ddee`,
`bbaa:ddcc`), abra o Zadig, selecione o dispositivo, escolha **WinUSB** e clique em
Install/Replace Driver. Isso acontece ate tres vezes durante a secao 5.

## 5. Primeira gravacao de uma placa vazia (DFU)

Um STM32F413 novo nao tem bootstub, entao a unica porta de entrada e o bootloader de ROM da
ST por USB (DFU).

1. Placa sem energia (nada no USB, harness box desconectado).
2. Segure `SW1` (a chave tactil pequena ligada ao `BOOT0`).
3. Com a chave pressionada, conecte o cabo USB-C no PC. Solte `SW1` depois de cerca de um
   segundo.
4. Confirme o dispositivo DFU:
   - Windows: o Gerenciador de Dispositivos mostra "STM32 BOOTLOADER" (ou um dispositivo
     desconhecido `0483:df11`). Associe WinUSB com o Zadig se necessario.
   - Linux: `lsusb | grep 0483:df11`.
   - Python: `python -c "from panda import PandaDFU; print(PandaDFU.list())"` imprime um serial.
5. Grave o bootstub. `recover()` apaga os setores 0 e 1, programa `bootstub.panda.bin` em
   0x08000000 e salta para ele. **Ele NAO grava a aplicacao.**

   ```
   python -c "from panda import PandaDFU; PandaDFU(None).recover()"
   ```

6. A placa reenumera como bootstub da panda `bbaa:ddee` (Windows: Zadig/WinUSB de novo).
   Conferir: `python -c "from panda import Panda; p=Panda(); print(p.bootstub, p.get_type())"`
   -> `True b'\x03'` (`HW_TYPE_BLACK_PANDA`).
7. Grave a aplicacao a partir de `board/obj/panda.bin.signed` (caminho padrao de `flash()`):

   ```
   python -c "from panda import Panda; p=Panda(); p.flash(); print('ok')"
   ```

   Para gravar um arquivo de outro lugar (por exemplo o binario pronto do hub repo):

   ```
   python -c "from panda import Panda; Panda().flash(fn=r'<caminho>\panda.bin.signed')"
   ```

8. A placa reinicia na aplicacao `bbaa:ddcc` (Windows: Zadig/WinUSB pela ultima vez).
   Verificar:

   ```
   python -c "from panda import Panda; p=Panda(); print(p.get_type(), p.get_version(), p.get_signature().hex()[:16], p.health()['uptime'])"
   ```

   Esperado: `b'\x03' DEV-a2f1983c-DEBUG ...` na opcao A, `DEV-<git>-DEBUG` do submodulo panda
   do openpilot na opcao B, ou `b'\x03' DEV-e78c41e6-DEBUG ...` na opcao C (o hash git
   acompanha o commit que voce compilou). `health()` nao pode lancar excecao.

Scripts equivalentes no Linux (eles rodam `scons` antes, logo precisam da toolchain):
`python board/recover.py` (DFU -> bootstub) seguido de `python board/flash.py` (aplicacao).

Se a placa nao aparecer como `0483:df11` no passo 4: confira se `SW1` estava mesmo pressionada
na energizacao, confira 3V3 no MCU e confira as linhas de dados do USB (cabo USB-C com dados,
nao so carga). Um dispositivo `bbaa:xxxx` significa que ja existe bootstub/aplicacao e o
botao nao foi segurado.

## 6. Atualizacoes seguintes

- **Opcao A (celular)**: nada a fazer. Quando a panda e conectada ao celular, o
  `ServicePandad` executa o `pandaflash`, que compara a assinatura em execucao com o
  `panda.bin.signed` empacotado no APK e regrava a area da aplicacao se for diferente. Ele
  nunca toca no bootstub. Assim, qualquer APK novo (sempre assinado com debug) e aceito.
- **Opcao B (openpilot 0.9.9)**: tambem nada a fazer. `selfdrive/pandad/pandad.py` confere a
  assinatura a cada inicio e grava `panda/board/obj/panda.bin.signed` quando difere (tambem
  recupera uma placa presa no bootstub).
- **Opcao C (PC)**: `python board/flash.py` (ou `Panda().flash()` apos recompilar).
- **Trocar de arvore (A / B / C)**: coloque a placa de volta em DFU com `SW1` e refaca a secao 5,
  para que bootstub e aplicacao venham da mesma arvore.
- **Entrar em DFU por software** quando ja existe firmware rodando (sem botao):
  `python -c "from panda import Panda; p=Panda(); p.reset(enter_bootstub=True); p.reset(enter_bootloader=True)"`.

## 7. Primeira conexao no carro (checklist, ainda nao executado)

1. Harness box no carro, chicote Bosch B entre camera e carro, panda no harness box, celular
   (opcao A) no USB-C da panda via OTG. Ignicao ligada, motor pode ficar desligado.
2. Opcao A: nas configuracoes do flowpilot selecione o carro `HONDA CITY 7G` (param `Mycar`,
   ver `../../software/flowpilot-port/port-city-flowpilot.md` secao 8.3) ou deixe o fingerprint CAN escolher.
3. Estado esperado da panda depois que o `controlsd` sobe (consultar de um PC com a panda
   temporariamente no PC, ou ler o log do flowpilot): `health()['safety_mode'] == 20`
   (`SAFETY_HONDA_BOSCH` na arvore do flowpilot) e `safety_param` com o bit 8 ligado
   (`FLAG_HONDA_RADARLESS`). Na arvore `revive-f4` os ids numericos vem do opendbc
   (`opendbc/safety`); confira la.
4. Observe `carState` (velocidade, angulo do volante, pedais, botoes do cruise) antes de
   qualquer engate.
5. Nao engate ate o fingerprint dizer `HONDA CITY 7G`, `canErrorCounter` ficar em 0 e os
   alertas estarem limpos por alguns minutos de conducao com o openpilot desengatado.

## 8. Referencias

- `python/constants.py` (`F4Config`: setores, bootstub 0x08000000, aplicacao 0x08004000),
  `python/dfu.py` (`recover()`), `python/__init__.py` (`Panda.flash()`, `get_mcu_type()`).
- `SConscript` (`base_project_f4`, alvo `panda`).
- Lado flowpilot: `wrappers/pandaflash.cpp`, `android/.../ServicePandad.java`,
  `panda/python/__init__.py` (`FLAG_HONDA_RADARLESS = 8`).
- PCB: `OpenpilotHardware/BlackPanda/kicad_project/BlackPanda.kicad_pcb` (net `Net-(U7-BOOT0)`,
  componentes `SW1`, `R14`).
