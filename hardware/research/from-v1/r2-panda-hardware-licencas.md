# Relatório de Pesquisa: Família de Hardware "Panda" (comma.ai) e o Clone Open-Source "OpenBlackPanda"

**Data de acesso de todas as fontes: 22/10/2025 (salvo indicação contrária)**
**Idioma de saída: Português (Brasil)**

---

## Sumário executivo

A pesquisa foi conduzida diretamente nos repositórios oficiais `commaai/panda`, `commaai/hardware` e no clone `lukasloetkolben/OpenpilotHardware` (arquivo histórico de `OpenBlackPanda`), via leitura de arquivos-fonte, histórico de commits (API REST do GitHub) e busca de código. Um achado crítico, não previsto no enunciado original: **em 2025 o repositório `commaai/panda` removeu do branch `master` todo o código das placas legadas baseadas em STM32F4 (white, grey, black, uno, dos)** — commits `1020d35` (PR #2223, 06/06/2025, "Deprecate uno + grey") e `3d27233` (PR #2227, 19/07/2025, "Deprecate white and black pandas"). Por isso, para reconstruir as especificações dessas placas foi necessário consultar commits anteriores a essas remoções. Isso está documentado abaixo, classificação **CONFIRMADO**, com permalinks de commit específicos.

---

## 1. Tabela comparativa dos boards panda

| Característica | White Panda | Grey Panda | Black Panda | Uno | Dos | Red Panda | Tres (comma three interno) | Cuatro (comma 3X / four interno) |
|---|---|---|---|---|---|---|---|---|
| **MCU** | STM32F4 (STM32F413, conforme `startup_stm32f413xx.s`) | STM32F4 (mesma família; reaproveita init do white) | STM32F413 | STM32F4 | STM32F4 | **STM32H725** | STM32H7 (família H725/H723, detectado por pacote) | STM32H7 (família H725/H723, detectado por pacote) |
| **Canais CAN** | 3x CAN + 1x GMLAN (classic CAN via bxCAN) | 3x CAN + 2x LIN + 1x GMLAN | 3x CAN + 1 CAN multiplexado | 3x CAN (bxCAN) | 3x CAN (bxCAN) | 3x CAN-FD + 1 CAN-FD multiplexado | 3 canais CAN-FD (FDCAN1/2/3) + SPI | 3 canais CAN-FD (FDCAN1/2/3, pinagem própria) |
| **Suporte CAN-FD (periférico FDCAN)** | Não (bxCAN clássico) | Não | Não | Não | Não | **Sim** | **Sim** | **Sim** |
| **Transceivers CAN** | Não documentado no firmware (apenas GPIOs de enable); **NÃO VERIFICADO** o part number exato para o board oficial | Idem White; **NÃO VERIFICADO** | Idem; **NÃO VERIFICADO** (clone usa TJA1042TK-3, ver seção 3) | **NÃO VERIFICADO** | **NÃO VERIFICADO** | **NÃO VERIFICADO** (não publicado no firmware nem em schematic oficial) | **NÃO VERIFICADO** | **NÃO VERIFICADO** |
| **Alimentação (12V/reguladores)** | Entrada 12V via OBD2; reguladores não documentados publicamente no firmware (**NÃO VERIFICADO** partnumbers) | Igual ao White | Igual | Igual | Igual | Entrada 12V via conector OBD-C; regula para 5V ao USB-A | SOM-based (comma three), alimentação interna do dispositivo | SOM-based (comma 3X) com sensor de corrente (`current sensing`), alimentação interna |
| **Interface host** | USB | USB | USB | USB | USB | USB-A (ao EON/PC) | SPI (`has_spi=true`) + fã (`has_fan=true`) | SPI + fã + áudio (SAI4/amplificador) |
| **Conector de harness ("comma harness"/OBD-C)** | OBD2-Port padrão (não é o conector USB-C "OBD-C") | OBD2-Port | OBD-C (estilo USB-C) | Conector proprietário com detecção SBU | Conector proprietário com detecção SBU | **OBD-C** (USB-C físico, USB-C 3.1/3.2 Gen2); detecção de orientação via SBU1 (GPIOC4)/SBU2 (GPIOA1) | Integrado ao dispositivo (SOM), não exposto como conector solto | Integrado ao dispositivo (SOM), FDCAN3 em pinos próprios (PD12/PD13) |
| **USB-A de saída (para alimentar/conectar dispositivo)** | Sim (USB A→EON/PC) | Sim | Sim | Sim, com regulador de "phone power"/chaveamento USB (`uno_set_usb_switch`) | Sim | Sim (USB-A→EON/PC) | N/A (interno ao comma three) | N/A (interno ao comma 3X) |
| **GPS de alta precisão** | **Não** | **Sim** (com antena externa) | **Sim** | Não documentado no firmware atual (**NÃO VERIFICADO**) | Não documentado (**NÃO VERIFICADO**) | **Não** | N/A (GPS é do SOM/comma three, não do chip panda) | N/A |
| **Status/depreciação** | Depreciado do openpilot; ainda vendido na loja comma | Depreciado; **não** vendido na loja | Depreciado; ainda vendido na loja | Depreciado (removido do firmware em 06/06/2025) | Depreciado (removido junto com white/black) | Ativo, vendido na loja, obrigatório para comma three em veículos CAN-FD | Interno ao comma three (não vendido separadamente) | Interno ao comma 3X / comma four |

**Classificação:** CONFIRMADO para MCU, canais CAN, suporte CAN-FD, conectividade USB/host, status de depreciação e GPS (fonte: `commaai/hardware/panda/README.md` — tabela oficial comma — e `board/boards/*.h` do firmware, ambos citados na tabela de fontes). **NÃO VERIFICADO** para os part numbers exatos de transceivers e reguladores dos boards **oficiais** (o firmware só habilita/desabilita pinos GPIO, nunca cita part numbers; nenhum schematic oficial foi encontrado — ver seção 2).

Fontes primárias usadas para montar a tabela:
- `commaai/hardware/panda/README.md` (tabela oficial comma com MCU, conectividade, CAN-FD, GPS) — commit `530b7da136b6a6d4b0d37b95bdb3472c59f672f4`. **CONFIRMADO.**
- `commaai/panda/board/boards/board_declarations.h`, `red.h`, `tres.h`, `cuatro.h` no commit atual `408e14d46ebb7da45a7d21f8db315922e10242a8`. **CONFIRMADO.**
- `commaai/panda/board/boards/white.h`, `black.h`, `dos.h` no commit pré-depreciação `f849893bdcfc6cd05d4547d64d2802b5a83f409c`. **CONFIRMADO.**
- `commaai/panda/board/boards/grey.h`, `uno.h` no commit pré-depreciação `e462c34d3d5402c2c4a274bee7abaafabf516993`. **CONFIRMADO.**
- `commaai/panda/board/stm32f4/board.h` (mesmo commit) — lógica `detect_board_type()` usando pull-ups em GPIOB1/7, GPIOA4-7, GPIOA13, GPIOB15 para diferenciar dos/white/grey/uno/black. **CONFIRMADO.**

---

## 2. Abertura de hardware e licenças

- **Firmware do panda (todo o repositório `commaai/panda`): licença MIT**, arquivo `LICENSE`, Copyright 2016 Comma.ai Inc. — **CONFIRMADO** (permalink: `https://github.com/commaai/panda/blob/408e14d46ebb7da45a7d21f8db315922e10242a8/LICENSE`).
- O `README.md` do repositório afirma explicitamente que o firmware é liberado sob licença MIT e que o board atual roda STM32H725. **CONFIRMADO**.
- **Schematic/PCB do red panda, tres ou cuatro publicados pela comma?** Busca exaustiva em `commaai/panda` (nenhum arquivo `.pdf`/`.sch`/`.kicad_*`/Gerber no repositório de firmware) e em `commaai/hardware/panda/` (pasta oficial de hardware aberto da comma) **não encontrou nenhum schematic ou PCB do red/tres/cuatro panda**. A pasta `panda/` do repo `commaai/hardware` contém apenas:
  - `panda/README.md` (tabela de especificações, sem arquivos de projeto)
  - fotos dos produtos (`white-panda.jpeg`, `grey-panda.jpeg`, `black-panda.jpeg`, `red-panda.jpg`)
  - `panda/white/guide.pdf` — um **guia de usuário**, não um schematic
  - `panda/grey/*.stl` — apenas modelos 3D de um suporte de antena GPS
  - **Nenhuma pasta "red", "tres" ou "cuatro" existe no repositório de hardware.**
  → **Status: NÃO ENCONTRADO** (nenhum schematic/PCB de qualquer panda oficial, incluindo o red panda, foi publicado pela comma). Fonte: listagem de diretório de `commaai/hardware` no commit `530b7da136b6a6d4b0d37b95bdb3472c59f672f4`. **CONFIRMADO** (a ausência foi verificada ativamente, não apenas presumida).
- Em contraste, a comma **publica abertamente os schematics do chicote/harness do carro e do conector OBD-C** (não do panda em si): `commaai/hardware/harness/OBD-C.sch.pdf`, `harness/v3/open_pinout.pdf`, `harness/v3/Harness_Box.pdf` e dezenas de PDFs de chicotes específicos por modelo de carro (Toyota, Honda, Hyundai, GM, Subaru, VW, Tesla etc.). **CONFIRMADO**, fonte: `commaai/hardware/harness/README.md` e listagem de `harness/v3/`.
- **Red panda hardware files (PCB do próprio panda): NÃO ENCONTRADO** publicamente — apenas o firmware é aberto (MIT); o design elétrico/mecânico do red panda permanece proprietário/não publicado, até onde a pesquisa alcançou.

---

## 3. OpenBlackPanda / OpenpilotHardware (lukasloetkolben)

- **Repositório atual**: `github.com/lukasloetkolben/OpenpilotHardware` (o nome antigo "OpenBlackPanda" aparentemente foi incorporado/renomeado para este repositório mais amplo, que também contém `HarnessBox`, `Uno`, `J533-Harness`, `PSA-Harness`, `OBDPower`, `LegacyTeslaOBDC_PreAP`). **CONFIRMADO** via listagem de diretório raiz, commit `9f3c524d187365f6a8f621bb7d86d639cdee7e8c`.
- **Licença**: arquivo `LICENSE` no nível raiz do repositório = **MIT License, Copyright (c) 2023 Lukas**. **CONFIRMADO**.
- O `README.md` raiz declara explicitamente: projeto **não afiliado à comma.ai** (disclaimer). **CONFIRMADO**.
- **Conteúdo da pasta `BlackPanda/`**:
  - `BlackPanda/kicad_project/` contém um **projeto KiCad completo**: `.kicad_pcb`, `.kicad_sch`, `.kicad_pro`, `.step` (modelo 3D), biblioteca de footprints/símbolos. **CONFIRMADO** (hardware totalmente aberto e reproduzível, ao contrário do panda oficial).
  - `BlackPanda/docs/` contém `BlackPanda.pdf` (exportação do schematic) e duas fotos do produto montado. **CONFIRMADO**.
  - Verificação direta do conteúdo do schematic (`BlackPanda.kicad_sch`, baixado e inspecionado via grep) confirma os componentes citados no enunciado:
    - **MCU: `STM32F413RGTx`** (símbolo `MCU_ST_STM32F4:STM32F413RGTx`) — **CONFIRMADO**.
    - **4x transceivers CAN `TJA1042TK-3`** (NXP) — **CONFIRMADO** (4 instâncias do símbolo `Interface_CAN_LIN:TJA1042TK-3` localizadas no schematic).
    - **Reguladores: `TPS5450DDAR`** (rotulado "12V to 5V Regulator") **e `XL1509-3.3`** (rotulado "5V to 3.3V Regulator") — **CONFIRMADO**.
    - **GPS: módulo u-blox `NEO-M8M`** (footprint `RF_GPS:ublox_NEO`, datasheet oficial u-blox referenciado) — **CONFIRMADO**.
    - Conector tipo USB-C ("comma harness"/OBD-C-like): o esquema usa um conector `Conn_02x13_Odd_Even` com rótulo `105450-0101` (parte Molex) adjacente a trilhas de +12V/GND — consistente com um conector estilo USB-C de 26 pinos usado nos harnesses da comma, mas **o part number exato do conector USB-C fêmea voltado ao "comma harness connector" em si não foi isolado com certeza no grep realizado — classificado como INFERÊNCIA**, não CONFIRMADO integralmente.
  - **Status declarado**: `BlackPanda/README.md` afirma literalmente que a placa foi **"tested and works so far without problems"** ("testada e funciona até agora sem problemas"). **CONFIRMADO** (é uma citação direta do autor, não uma afirmação independente de terceiros — a validade técnica da afirmação em si permanece NÃO VERIFICADA por fonte externa).
  - **Issues/PRs conhecidos**: na janela de tempo pesquisada não foi encontrada nenhuma *issue* ou *pull request* aberta especificamente mencionando problemas na pasta `BlackPanda` do repositório `OpenpilotHardware` — **NÃO ENCONTRADO** (busca limitada ao conteúdo indexado acessível; não é garantia de inexistência, apenas de não-localização).
- **Conteúdo da pasta `HarnessBox/`** (necessária para compatibilidade do híbrido):
  - Também contém projeto KiCad completo (`kicad_pcb`, `kicad_sch`, `.step`) e `docs/`.
  - `HarnessBox/README.md` declara **"tested and works perfectly"** ("testada e funciona perfeitamente"). **CONFIRMADO** (citação direta).
  - Inspeção do schematic (`HarnessBox.kicad_sch`) confirma: dois relés `G6K-2P-Y` (DC3 e DC5), conector `RJ45-DB-101PWB`, resistores de terminação CAN de `120R`, diodos `BAV21W_RHG`, transistor `DTC114E`/`DDTC114ECA` para acionamento do relé, e um conector `105450-0101` rotulado com trilhas `+12V`/`GND` — arquitetura consistente com a descrição oficial da comma de uma "harness box" com relé que desconecta o panda sem gerar erro no veículo (ver seção 2, `commaai/hardware/harness/README.md`). **CONFIRMADO**.

---

## 4. Fatos de firmware do STM32H7 em `commaai/panda` (commit master `408e14d46ebb7da45a7d21f8db315922e10242a8`)

- **Arquivos que implementam o suporte STM32H7**: diretório `board/stm32h7/`, incluindo `peripherals.h`, `board.h`, `clock.h`, além de `llfdcan.h`/drivers correlatos. **CONFIRMADO**.
- **Atribuição de pinos FDCAN** (`board/stm32h7/peripherals.h`):
  - `FDCAN1`: PB8/PB9
  - `FDCAN2`: PB5/PB6, remapeável para PB12/PB13 dependendo da orientação do harness
  - `FDCAN3`: PG9/PG10
  — **CONFIRMADO**, permalink: `https://github.com/commaai/panda/blob/408e14d46ebb7da45a7d21f8db315922e10242a8/board/stm32h7/peripherals.h`.
- **Detecção de board** (`board/stm32h7/board.h`, função `detect_board_type()`): lê pull-ups em `GPIOF7-10` (variável `id1`) e `GPIOD4-7` (variável `id2`):
  - `id2 == 3` → `HW_TYPE_CUATRO`
  - `id1 == 0` → `HW_TYPE_RED_PANDA`
  - `id1 == 1` → variante depreciada "RED_PANDA_V2" (hoje mapeada para `HW_TYPE_UNKNOWN`)
  - `id1 == 2` → `HW_TYPE_TRES`
  — **CONFIRMADO**.
- **Detecção de pacote SMPS/LDO** (`board/stm32h7/clock.h`, função `get_package_smps_type()`): lê o registrador `SYSCFG->PKGR`; pacotes `TFBGA100` → `PACKAGE_WITHOUT_SMPS` (implica uso de LDO interno, consistente com **STM32H723**); pacotes `LQFP144`/`UFBGA169` → `PACKAGE_WITH_SMPS` (consistente com **STM32H725**, que possui SMPS integrado). Se o pacote for desconhecido, o código executa `while(true);` — um *hang* infinito proposital, documentado no código como medida de segurança/depuração (comentário `// unknown package, let's hang here`). **CONFIRMADO**.
- **Constantes `HW_TYPE`** — definidas em `board/boards/board_declarations.h` (que o próprio comentário do código declara devem espelhar `cereal/log.capnp` e `python/__init__.py`):
  ```c
  #define HW_TYPE_UNKNOWN 0U
  #define HW_TYPE_RED_PANDA 7U
  #define HW_TYPE_TRES 9U
  #define HW_TYPE_CUATRO 10U
  ```
  Os valores 1–6 e 8, correspondentes a white/grey/black/uno/dos/red_v2, **não aparecem mais no `master` atual** (foram removidos junto com os respectivos arquivos de board nas depreciações de 2025), mas foram confirmados historicamente via `board/stm32f4/board.h` no commit `e462c34d`, que referencia `HW_TYPE_WHITE_PANDA`, `HW_TYPE_GREY_PANDA`, `HW_TYPE_UNO`, `HW_TYPE_BLACK_PANDA`, `HW_TYPE_DOS` nomeadamente (sem o valor numérico explícito nesse arquivo específico). **CONFIRMADO** para os nomes das constantes; **INFERÊNCIA** para seus valores numéricos exatos anteriores à remoção (não foi possível confirmar os números binários antigos no tempo de pesquisa disponível).

---

## 5. Alternativas open-source/DIY de panda com suporte a CAN-FD

- **"Panda Jungle"**: existe e é mantido ativamente como parte do próprio `commaai/panda` (`python/jungle.py`), descrito no código como *"interface Python para os fixtures Jungle pré-flashados usados em testes HITL"*. **CONFIRMADO** que o Jungle existe e usa a mesma base H7/CAN-FD dos pandas atuais (ele é usado para testar red/tres/cuatro no pipeline de HITL da comma, conforme `tests/hitl/base.py`, `test_9_harness.py` etc.). Contudo, **nenhum schematic/PCB do Jungle foi localizado publicado em código-fonte aberto** nos repositórios pesquisados — apenas o driver Python (host-side) está no repositório de firmware. **NÃO ENCONTRADO** para o hardware do Jungle em si (apenas comercializado na loja comma, segundo buscas na web, mas o link do shop não foi diretamente acessível — ver limitações abaixo).
- **OpenBlackPanda/HarnessBox (lukasloetkolben)**: já documentado na seção 3 — é, até onde a pesquisa alcançou, **o único projeto DIY publicamente open-source e completo (KiCad + BOM implícito) de um clone de panda** encontrado, mas é um clone do **black panda (STM32F413, CAN clássico)**, **não** um clone do red panda com FDCAN/H7. **CONFIRMADO** que esse projeto não implementa CAN-FD (usa o mesmo MCU STM32F413 do black panda original, sem periférico FDCAN).
- **Placa DIY baseada em STM32H7 com CAN-FD publicada por terceiros**: nenhuma foi encontrada nas buscas realizadas (GitHub code search e busca web, incluindo termos "red panda clone", "H7 panda PCB", "DIY CAN-FD panda"). → **Status: NÃO ENCONTRADO.**
- **"comma body"**: identificado como um projeto real dentro do próprio ecossistema comma (`python/body.py` referenciado em `commaai/panda/__init__.py`, comentário `# panda body`), mas é um produto robótico (controlador de um robô de duas rodas), **não um CAN-FD interface alternativo**. **CONFIRMADO** sua existência, mas é irrelevante como "alternativa de panda" per se.

---

## 6. Limitações e fontes inacessíveis

- **`comma.ai/shop/*` (páginas da loja oficial)**: todas as tentativas diretas de `fetch` a essas URLs (ex.: `comma.ai/shop/red-panda`, `comma.ai/shop/panda-jungle`) **falharam por erro de transporte/DNS** na ferramenta de busca direta de página. As informações atribuídas a essas páginas neste relatório vêm de uma busca textual (engine de busca web) que retornou trechos com citação de URL, mas o conteúdo da página em si **não pôde ser verificado por leitura direta neste processo** → classificado como **NÃO VERIFICADO** (origem secundária/indireta), exceto onde cruzado com a tabela oficial em `commaai/hardware/panda/README.md`, que é fonte primária direta e foi lida com sucesso.
- Não foi encontrado nenhum post de blog da comma.ai especificamente sobre "red panda CAN-FD" durante a pesquisa (busca via engine de busca web não retornou um artigo de blog dedicado e verificável à parte da documentação do GitHub) → **NÃO ENCONTRADO**.
- O repositório `commaai/panda` não possui nenhuma *GitHub Release* publicada (verificado via fetch de `github.com/commaai/panda/releases`). **CONFIRMADO**.

---

## Tabela de fontes

| # | Título | URL | Data de acesso |
|---|---|---|---|
| 1 | commaai/panda — README.md (master) | https://github.com/commaai/panda/blob/408e14d46ebb7da45a7d21f8db315922e10242a8/README.md | 22/10/2025 |
| 2 | commaai/panda — LICENSE (MIT) | https://github.com/commaai/panda/blob/408e14d46ebb7da45a7d21f8db315922e10242a8/LICENSE | 22/10/2025 |
| 3 | commaai/panda — board/boards/board_declarations.h (HW_TYPE, constantes) | https://github.com/commaai/panda/blob/408e14d46ebb7da45a7d21f8db315922e10242a8/board/boards/board_declarations.h | 22/10/2025 |
| 4 | commaai/panda — board/boards/red.h | https://github.com/commaai/panda/blob/408e14d46ebb7da45a7d21f8db315922e10242a8/board/boards/red.h | 22/10/2025 |
| 5 | commaai/panda — board/boards/tres.h | https://github.com/commaai/panda/blob/408e14d46ebb7da45a7d21f8db315922e10242a8/board/boards/tres.h | 22/10/2025 |
| 6 | commaai/panda — board/boards/cuatro.h | https://github.com/commaai/panda/blob/408e14d46ebb7da45a7d21f8db315922e10242a8/board/boards/cuatro.h | 22/10/2025 |
| 7 | commaai/panda — board/stm32h7/peripherals.h (pinos FDCAN) | https://github.com/commaai/panda/blob/408e14d46ebb7da45a7d21f8db315922e10242a8/board/stm32h7/peripherals.h | 22/10/2025 |
| 8 | commaai/panda — board/stm32h7/board.h (detect_board_type) | https://github.com/commaai/panda/blob/408e14d46ebb7da45a7d21f8db315922e10242a8/board/stm32h7/board.h | 22/10/2025 |
| 9 | commaai/panda — board/stm32h7/clock.h (get_package_smps_type) | https://github.com/commaai/panda/blob/408e14d46ebb7da45a7d21f8db315922e10242a8/board/stm32h7/clock.h | 22/10/2025 |
| 10 | commaai/panda — board/boards/white.h (commit pré-depreciação) | https://github.com/commaai/panda/blob/f849893bdcfc6cd05d4547d64d2802b5a83f409c/board/boards/white.h | 22/10/2025 |
| 11 | commaai/panda — board/boards/black.h (commit pré-depreciação) | https://github.com/commaai/panda/blob/f849893bdcfc6cd05d4547d64d2802b5a83f409c/board/boards/black.h | 22/10/2025 |
| 12 | commaai/panda — board/boards/dos.h (commit pré-depreciação) | https://github.com/commaai/panda/blob/f849893bdcfc6cd05d4547d64d2802b5a83f409c/board/boards/dos.h | 22/10/2025 |
| 13 | commaai/panda — board/boards/grey.h e uno.h (commit pré-depreciação) | https://github.com/commaai/panda/blob/e462c34d3d5402c2c4a274bee7abaafabf516993/board/boards/grey.h | 22/10/2025 |
| 14 | commaai/panda — board/stm32f4/board.h (detecção legada F4) | https://github.com/commaai/panda/blob/e462c34d3d5402c2c4a274bee7abaafabf516993/board/stm32f4/board.h | 22/10/2025 |
| 15 | commaai/panda — PR #2223 "Deprecate uno + grey" | https://github.com/commaai/panda/commit/1020d355 | 22/10/2025 |
| 16 | commaai/panda — PR #2227 "Deprecate white and black pandas" | https://github.com/commaai/panda/commit/3d272335 | 22/10/2025 |
| 17 | commaai/hardware — panda/README.md (tabela oficial de especificações) | https://github.com/commaai/hardware/blob/530b7da136b6a6d4b0d37b95bdb3472c59f672f4/panda/README.md | 22/10/2025 |
| 18 | commaai/hardware — harness/README.md (OBD-C, harness box, car harness) | https://github.com/commaai/hardware/blob/530b7da136b6a6d4b0d37b95bdb3472c59f672f4/harness/README.md | 22/10/2025 |
| 19 | commaai/hardware — harness/OBD-C.sch.pdf (pinout OBD-C) | https://github.com/commaai/hardware/blob/530b7da136b6a6d4b0d37b95bdb3472c59f672f4/harness/OBD-C.sch.pdf | 22/10/2025 |
| 20 | lukasloetkolben/OpenpilotHardware — README.md raiz | https://github.com/lukasloetkolben/OpenpilotHardware/blob/9f3c524d187365f6a8f621bb7d86d639cdee7e8c/README.md | 22/10/2025 |
| 21 | lukasloetkolben/OpenpilotHardware — LICENSE (MIT) | https://github.com/lukasloetkolben/OpenpilotHardware/blob/9f3c524d187365f6a8f621bb7d86d639cdee7e8c/LICENSE | 22/10/2025 |
| 22 | lukasloetkolben/OpenpilotHardware — BlackPanda/README.md | https://github.com/lukasloetkolben/OpenpilotHardware/blob/9f3c524d187365f6a8f621bb7d86d639cdee7e8c/BlackPanda/README.md | 22/10/2025 |
| 23 | lukasloetkolben/OpenpilotHardware — BlackPanda/kicad_project/BlackPanda.kicad_sch | https://github.com/lukasloetkolben/OpenpilotHardware/blob/9f3c524d187365f6a8f621bb7d86d639cdee7e8c/BlackPanda/kicad_project/BlackPanda.kicad_sch | 22/10/2025 |
| 24 | lukasloetkolben/OpenpilotHardware — HarnessBox/README.md | https://github.com/lukasloetkolben/OpenpilotHardware/blob/9f3c524d187365f6a8f621bb7d86d639cdee7e8c/HarnessBox/README.md | 22/10/2025 |
| 25 | lukasloetkolben/OpenpilotHardware — HarnessBox/kicad_project/HarnessBox.kicad_sch | https://github.com/lukasloetkolben/OpenpilotHardware/blob/9f3c524d187365f6a8f621bb7d86d639cdee7e8c/HarnessBox/kicad_project/HarnessBox.kicad_sch | 22/10/2025 |
| 26 | commaai/panda — python/jungle.py (Panda Jungle HITL) | https://github.com/commaai/panda/blob/408e14d46ebb7da45a7d21f8db315922e10242a8/python/jungle.py | 22/10/2025 |
| 27 | commaai/panda — Releases (confirmando ausência de releases) | https://github.com/commaai/panda/releases | 22/10/2025 (fonte acessada; sem releases publicados) |
| 28 | comma.ai/shop — páginas de produto (red panda, panda jungle) | https://comma.ai/shop | 22/10/2025 — **FONTE INACESSÍVEL** via fetch direto (erro de transporte/DNS); dados citados vêm de busca indireta, classificados NÃO VERIFICADO |

---

## Observações finais sobre metodologia e confiabilidade

- Toda informação extraída diretamente de arquivos-fonte lidos neste processo (firmware `.h`, `README.md`, `LICENSE`, `.kicad_sch`) é classificada **CONFIRMADO**.
- Informação derivada de raciocínio sobre o código (ex.: valores numéricos antigos de `HW_TYPE` não mais presentes no `master`) é classificada **INFERÊNCIA**.
- Informação vinda de buscas na web sem leitura direta da página de origem (ex.: páginas da loja comma.ai) é classificada **NÃO VERIFICADO**.
- Itens ativamente procurados e não encontrados (schematic do red panda; DIY H7 CAN-FD clone; blog post específico sobre red panda) são explicitamente marcados **NÃO ENCONTRADO**, distinguindo-se de "não pesquisado".
