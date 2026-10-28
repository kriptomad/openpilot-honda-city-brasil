# R3v2 — Pesquisa de Componentes (STEP 4): Placa CAN-FD com STM32H725ZGT6

**Data de acesso de todas as fontes:** 2026-10-23 (America/Sao_Paulo, UTC-3)
**Projeto:** Retrofit de design KiCad STM32F413 → STM32H725ZGT6 (LQFP144)

## Como ler este documento

- `[F]` = fato verificado diretamente em uma fonte (datasheet do fabricante ou página de distribuidor/mirror acessada).
- `[I]` = inferência do autor (raciocínio sobre dados verificados, não extraído literalmente de uma fonte).
- `NÃO VERIFICADO` = não foi possível confirmar com confiança; **não inventar valores**.
- Muitas páginas de **DigiKey, Mouser, LCSC, ST.com e Alldatasheet bloquearam acesso automatizado direto** (HTTP 403 / timeout / falha de handshake TLS) durante esta pesquisa. Nesses casos, os dados de preço/estoque foram obtidos via resultados de mecanismo de busca com citação explícita da URL de origem (snapshot agregado), e isso está sinalizado em cada item com a nota "(via busca, fetch direto falhou)". **Recomenda-se que o engenheiro responsável reconfirme preço/estoque manualmente antes de fechar o BOM final**, pois são dados voláteis e o método de coleta não permitiu fetch HTML bruto da página.

---

## 1. MCU — STM32H725ZGT6 e alternativas (LQFP144)

### 1.1 STM32H725ZGT6 (escolha primária)

- Fabricante: STMicroelectronics. Core ARM Cortex-M7 até 550 MHz + Cortex-M4, pacote **LQFP144** (20×20 mm), **1 MB Flash**, 564 KB RAM, **SMPS interno** disponível, tensão 1.62–3.6 V, faixa de temperatura padrão −40 °C a +85 °C (grade industrial; não é AEC-Q100 automotive nesta variante). [F] Fonte: página de produto ST — https://www.st.com/en/microcontrollers-microprocessors/stm32h725zg.html (acesso 2026-10-23, via resultado de busca; fetch direto ao st.com falhou por timeout em múltiplas tentativas nesta sessão).
- Datasheet: DS13311 — https://www.st.com/resource/en/datasheet/stm32h725zg.pdf (fetch direto falhou por timeout repetido; conteúdo não pôde ser lido integralmente nesta sessão — **NÃO VERIFICADO em detalhe de seção**, apenas citado via busca).
- LCSC: part **C730156** — https://www.lcsc.com/product-detail/C730156.html [F] (via busca; fetch direto ao lcsc.com falhou por erro de handshake TLS). Estoque reportado ~145 un., preço inicial ~US$10,69/un (quantidade baixa) em 2026-10-23 — **dado não confirmado por fetch direto, tratar como indicativo**.
- JLCPCB: mesmo código C730156, classificado como peça **Extended** (não Basic) — https://jlcpcb.com/partdetail/Stmicroelectronics-STM32H725ZGT6/C730156 [F] (via busca; fetch direto ao jlcpcb.com falhou).
- DigiKey: part 497-STM32H725ZGT6-ND (tray) / 497-STM32H725ZGT6TR-ND (tape&reel, MOQ 500) — https://www.digikey.com/en/products/detail/stmicroelectronics/stm32h725zgt6/13171215 — reportado "fora de estoque, backorder", preço unitário ~US$14 caindo a ~US$7,8 em 300+ un, lead time 15–52 semanas (via busca, fetch direto falhou com HTTP 403). **NÃO VERIFICADO com fetch direto — preço/estoque podem estar desatualizados.**
- Mouser: https://www.mouser.com/ProductDetail/STMicroelectronics/STM32H725ZGT6 — reportado estoque 0 com 715 un. encomendadas, preço unitário ~US$12,4 caindo a ~US$7,8 em 360+ un (via busca, fetch direto falhou por erro de DNS/TLS). **NÃO VERIFICADO com fetch direto.**

### 1.2 STM32H725ZET6 — 512 KB Flash (NÃO ACEITÁVEL para este firmware)

- Mesmo pacote LQFP144, mesma família H725, porém **512 KB Flash** em vez de 1 MB. [F] (nomenclatura ST: sufixo "E" = 512 KB vs "G" = 1 MB, convenção padrão da linha STM32H7 — https://www.st.com/en/microcontrollers-microprocessors/stm32h725-735/documentation.html, acesso 2026-10-23).
- **Marcar como NÃO ACEITÁVEL**: o firmware do projeto requer 1 MB de Flash (conforme especificado na tarefa); o H725ZET6 não atende esse requisito. [I]
- LCSC: part **C730155** — https://www.lcsc.com/product-detail/ST-Microelectronics_STMicroelectronics-STM32H725ZET6_C730155.html [F] (via busca). Reportado "fora de estoque" em 2026-10-23 (via busca, fetch direto falhou). JLCPCB mesmo código C730155.

### 1.3 STM32H735ZGT6 — mesmo pinout, com criptografia extra (alternativa aceitável)

- Mesma família de pacote **LQFP144**, 1 MB Flash, 564 KB RAM. Segundo o seletor de produtos ST, STM32H735 adiciona acelerador de criptografia (AES/HASH) em relação ao STM32H725, mantendo o mesmo pinout LQFP144 — https://www.st.com/en/microcontrollers-microprocessors/stm32h725-735/documentation.html (acesso 2026-10-23, via busca). [F] quanto a "mesma família/pacote 1MB"; a afirmação específica de "pinout 100% idêntico pino-a-pino" **NÃO FOI VERIFICADA diretamente na tabela de pinagem do datasheet** (st.com inacessível nesta sessão) — tratar como **NÃO VERIFICADO** até confirmação cruzando as tabelas de pinagem DS13311 (H725/735) pino a pino.
- DigiKey lista STM32H735ZGT6 sob part 13171219 — https://www.digikey.com/en/products/detail/stmicroelectronics/STM32H735ZGT6/13171219 (via busca, fetch direto não realizado nesta sessão).
- **Conclusão prática**: aceitável como alternativa drop-in *supostamente* (mesma família/pacote/memória), mas a compatibilidade de pinagem exata deve ser confirmada manualmente comparando as tabelas "Pin description" do DS13311 (H725/735) antes de finalizar o layout. [I]

### 1.4 STM32H723ZGT6 — ponto de atenção sobre SMPS (CONFLITO DE FONTES — NÃO VERIFICADO)

- LCSC part **C730146** corresponde a STM32H723ZGT6 — https://www.lcsc.com/product-detail/Microcontrollers-MCU-MPU-SOC_STMicroelectronics-STM32H723ZGT6_C730146.html [F] (via busca; confirma a alegação do enunciado de que C730146 = H723ZGT6). JLCPCB mesmo código.
- **Sobre disponibilidade de SMPS no pacote LQFP144 do STM32H723ZGT6, as fontes encontradas são CONTRADITÓRIAS:**
  - Uma fonte (relacionada à placa de avaliação NUCLEO-H723ZG, que usa pacote LQFP144) indica pino **VLXSMPS no pino 51** e indutor L4 = 2.2 µH no esquema MB1364-H723ZG-E01, sugerindo que o SMPS **está disponível** no LQFP144 do H723ZGT6 — https://community.st.com/stm32-mcus-products-25/schematic-for-nucleo-h723zg-and-nucleo-h743zi2-in-pdf-126138 e https://www.st.com/en/evaluation-tools/nucleo-h723zg.html (acesso 2026-10-23, via busca; fetch direto ao st.com falhou por timeout).
  - Outra síntese de busca afirma o oposto, que a Tabela 5 do datasheet STM32H723/733 (DS13310) marcaria o pacote **LQFP144 como "SMPS NÃO disponível, apenas LDO"**.
  - **Não foi possível acessar diretamente o PDF do datasheet DS13310 nem a página st.com nesta sessão** (timeouts repetidos) para resolver o conflito.
  - **Veredito: NÃO VERIFICADO.** O engenheiro deve abrir manualmente o datasheet DS13310 (STM32H723/733), seção "Pinouts and pin description", tabela de pacotes, e confirmar se o pino VLXSMPS existe fisicamente no LQFP144 do STM32H723ZGT6 antes de decidir se este MCU é aceitável. **Não assumir nenhuma das duas afirmações como verdadeira sem essa confirmação.**
- Quanto à alegação do enunciado de que "firmware clock.h força SMPS no LQFP144, portanto H723ZGT6 NÃO aceitável": esta é uma regra de projeto interna (não uma característica de datasheet) — **mantida como está, não verificável externamente**; cabe ao firmware do projeto, não ao componente.

### 1.5 Tabela resumo — MCU

| MPN | Flash | SMPS (LQFP144) | Pinout vs H725ZGT6 | Aceitável? | LCSC | Fonte |
|---|---|---|---|---|---|---|
| STM32H725ZGT6 | 1 MB | Sim [F] | — (referência) | **Sim (primário)** | C730156 [F] | st.com (via busca) |
| STM32H725ZET6 | 512 KB | Sim (mesma família) [I] | Idêntico (mesma família) [I] | **NÃO (Flash insuficiente)** | C730155 [F] | lcsc.com (via busca) |
| STM32H735ZGT6 | 1 MB | Presumido sim [I] | NÃO VERIFICADO pino-a-pino | Provável sim, **a confirmar** | — não localizado nesta sessão | st.com (via busca) |
| STM32H723ZGT6 | 1 MB | **CONFLITO — NÃO VERIFICADO** | Mesma pin-list da família Value Line [I], não confirmado pino-a-pino | **NÃO VERIFICADO — não decidir sem checar DS13310** | C730146 [F] | lcsc.com (via busca) |

---

## 2. Indutor SMPS interno (2.2 µH)

Requisitos do enunciado: 2.2 µH, Isat ≥ 1.7 A, Irms ≥ 1.4 A, DCR ≤ 150 mΩ, conforme DS13311 §6.3.3 / AN5419.

- **AN5419** — "Getting started with STM32H723/733, STM32H725/735 and STM32H730 Value Line hardware development" é confirmado como o documento correto da ST para esta família — https://www.st.com/resource/en/application_note/an5419-getting-started-with-stm32h723733-stm32h725735-and-stm32h730-value-line-hardware-development-stmicroelectronics.pdf [F] (confirmado via busca cruzada; **o PDF em si não pôde ser aberto nesta sessão** — st.com apresentou timeout em todas as tentativas de fetch direto do PDF). Portanto, os requisitos específicos de corrente/DCR da tabela de indutores recomendados do AN5419 **NÃO FORAM VERIFICADOS diretamente no documento primário** nesta sessão; os valores abaixo vêm de datasheets de fabricante dos indutores candidatos (estes sim, parcialmente verificados via LCSC/busca).

### 2.1 Murata DFE201610E-2R2M (=P2) — candidato 1

- Indutância 2.2 µH, corrente nominal (temp. rise) **1.7 A**, corrente de saturação (Isat) ~2.4 A, DCR máx. **140 mΩ**, pacote 2.0×1.6×1.0 mm (código 0806 métrico/2016), blindado. [F] Fonte: LCSC — https://www.lcsc.com/product-detail/C337891.html (acesso 2026-10-23, via busca; fetch direto ao lcsc.com falhou). LCSC part **C337891**, preço reportado a partir de ~US$0,138/un (5+ un.), estoque reportado ~2.240 un. em 2026-10-23 — **não confirmado por fetch direto**.
- Atende DCR ≤ 150 mΩ (140 mΩ < 150 mΩ) [F]/[I]. Atende Isat ≥ 1.7 A? O valor "1.7 A" aqui é especificamente o rating de *temperature rise*, não necessariamente Isat — **checar no datasheet Murata se o Isat (queda de indutância) é ≥ 1.7 A antes de confirmar adequação total**; o valor de Isat citado (~2.4 A) sugere que sim, mas isso **não foi lido diretamente da tabela técnica completa do datasheet Murata**, apenas de um resumo agregado — marcar como **parcialmente verificado**.

### 2.2 TDK TFM201610ALMA2R2MTAA — candidato 2

- Indutância 2.2 µH ±20%, corrente nominal (40 °C rise) **1.9 A**, Isat típico ~2 A (ΔL=30%), DCR típ. 130 mΩ / máx. **152 mΩ**, pacote 2.0×1.6×1.0 mm, blindado (núcleo metálico), qualificado **AEC-Q200**, faixa de temperatura −55 °C a +150 °C. [F] Fonte: LCSC — https://www.lcsc.com/product-detail/Power-Inductors_SMD_TDK_TFM201610ALMA2R2MTAA_C404810.html (acesso 2026-10-23, via busca; fetch direto falhou). Datasheet oficial TDK: https://product.tdk.com/en/search/inductor/inductor/part/TFM201610ALMA2R2MTAA_en.html (não aberto diretamente nesta sessão).
- Nota: DCR máx. 152 mΩ está **marginalmente acima** do limite de 150 mΩ pedido no enunciado — **atenção**, pode não atender ao requisito estrito dependendo de qual leitura (típica vs máxima) é usada no projeto. [I]
- LCSC part **C404810**.

### 2.3 Coilcraft XFL3012-222 e XAL4020-222 — candidatos de maior corrente (maior footprint)

- **XFL3012-222**: 2.2 µH, Isat ~3.7–4.5 A, DCR típ. ~41 mΩ, pacote maior (3.0×3.0×1.2 mm). [F]/[I] (via busca; dados não confirmados por fetch direto ao datasheet Coilcraft — **NÃO VERIFICADO em detalhe**, apenas citado por busca agregada).
- **XAL4020-222**: 2.2 µH, Isat até ~7.5 A, DCR típ. ~20 mΩ, pacote 4.0×4.0×2.1 mm. [F]/[I] mesma ressalva acima.
- Ambos folgam com margem nos requisitos de corrente/DCR, mas ocupam mais área de PCB; usar apenas se o layout permitir. [I]
- **Estes dois não foram cruzados com uma página LCSC/distribuidor nesta sessão — tratar como NÃO VERIFICADO quanto a disponibilidade/part exato de reel.**

### 2.4 Tabela resumo — indutor SMPS

| MPN | Fabricante | Indutância | Isat | DCR | Pacote | AEC-Q | LCSC |
|---|---|---|---|---|---|---|---|
| DFE201610E-2R2M=P2 | Murata | 2.2 µH | ~2.4 A (rating 1.7A @ΔT) | 140 mΩ máx | 2016 (0806) | NÃO VERIFICADO | C337891 [F] |
| TFM201610ALMA2R2MTAA | TDK | 2.2 µH | ~2 A (ΔL30%) | 152 mΩ máx (⚠ acima do limite 150mΩ) | 2016 (0806) | **AEC-Q200** [F] | C404810 [F] |
| XFL3012-222 | Coilcraft | 2.2 µH | 3.7–4.5 A | ~41 mΩ | 3012 (maior) | NÃO VERIFICADO | NÃO VERIFICADO |
| XAL4020-222 | Coilcraft | 2.2 µH | ~7.5 A | ~20 mΩ | 4020 (maior ainda) | NÃO VERIFICADO | NÃO VERIFICADO |

**Recomendação [I]:** Murata DFE201610E-2R2M=P2 como escolha primária (menor footprint, DCR dentro do limite); TDK TFM201610ALMA2R2MTAA como alternativa de segunda fonte (atenção ao DCR máx. levemente acima do limite).

---

## 3. Transceptor CAN — TJA1042TK/3 e alternativas

### 3.1 NXP TJA1042TK/3 (baseline mantido)

- **Confirmado via datasheet NXP (Rev. 10, 24-Nov-2017), mirror acessado diretamente:** https://html.datasheetq.com/pdf-html/654006/NXP/1page/TJA1042.html e página 3/4 do mesmo mirror (acesso 2026-10-23) [F]:
  - "Timing guaranteed for data rates up to **5 Mbit/s** in the CAN FD fast phase" — confirma que o TJA1042TK/3 **suporta CAN FD até 5 Mbit/s**. [F]
  - Pacote **HVSON8** (SOT782-1), corpo 3.0×3.0×0.85 mm, sem terminais (leadless). [F]
  - Tabela de ordenação (Table 2): TJA1042TK/3 = HVSON8, com pino **VIO** (não tem pino SPLIT). [F]
  - **Pinagem confirmada (Fig. 2c / Table 3, página 4 do datasheet)**: Pino 1 = TXD, Pino 2 = GND, Pino 3 = VCC, Pino 4 = RXD, Pino 5 = VIO, Pino 6 = CANL, Pino 7 = CANH, Pino 8 = STB; pad central exposto = GND (deve ser soldado ao plano de terra). [F] — **Isto confirma exatamente a pinagem informada no enunciado (TXD1 GND2 VCC3 RXD4 VIO5 CANL6 CANH7 STB8).**
  - AEC-Q100 qualificado; ISO 11898-2:2016 e SAE J2284-1 a J2284-5 compliant. [F]
- Datasheet original: https://www.nxp.com/docs/en/data-sheet/TJA1042.pdf (fetch direto retornou PDF binário não decodificável pela ferramenta nesta sessão; o mirror HTML acima foi usado como fonte primária efetiva, mesmo conteúdo/revisão).
- Preço/estoque (via busca, fetch direto a mouser/lcsc/digikey falhou):
  - Mouser: part TJA1042TK/3/1J, ~US$1,93 (1 un.) a ~US$1,01 (2500+ un.), estoque reportado 4.100 un. — https://www.mouser.com/ProductDetail/NXP-Semiconductors/TJA1042TK-3-1J (acesso 2026-10-23). **NÃO VERIFICADO por fetch direto.**
  - LCSC: part **C131480** (TJA1042TK/3/1J), ~US$0,89 (5+) a ~US$0,44 (6000+), estoque reportado 2.740 un. — https://www.lcsc.com/product-detail/C131480.html (acesso 2026-10-23). **NÃO VERIFICADO por fetch direto.**
  - DigiKey: variante /2Z, ~US$1,93 (1 un.) a ~US$0,97 (6000 un. reel) — https://www.digikey.com/en/products/detail/nxp-usa-inc/TJA1042TK-3-2Z/4699737. **NÃO VERIFICADO por fetch direto.**

### 3.2 TI TCAN1044V-Q1 (TCAN1044VDRBRQ1) — NÃO pino-compatível

- Pacote DRB = VSON8, 3.0×3.0 mm. Pinagem reportada (via busca cruzando datasheet TI, **não confirmada por fetch HTML direto do PDF** — a ferramenta de fetch retornou apenas o PDF bruto comprimido/ilegível nesta sessão): Pino1 CANH, Pino2 CANL, Pino3 VCC, Pino4 GND, Pino5 VIO, Pino6 STB, Pino7 TXD, Pino8 RXD.
- **Esta ordem de pinos É DIFERENTE da pinagem do TJA1042TK/3** (que é TXD1/GND2/VCC3/RXD4/VIO5/CANL6/CANH7/STB8). **Portanto, TCAN1044VDRBRQ1 NÃO é pino-a-pino compatível com o footprint HVSON8 existente** — exigiria reroteamento do footprint/rede, mesmo tendo tamanho de pacote nominal semelhante (3×3 mm). [F]/[I] — confiança moderada, pois a tabela de pinos não foi lida diretamente do PDF original (apenas via síntese de busca); **recomenda-se confirmação manual antes de descartar definitivamente.**
- Fonte: https://www.ti.com/lit/ds/symlink/tcan1044-q1.pdf (acesso 2026-10-23, PDF não decodificável pela ferramenta); https://www.ti.com/product/TCAN1044-Q1/part-details/TCAN1044VDRBRQ1.

### 3.3 TI TCAN1042HGV-Q1 — POSSÍVEL compatibilidade pino-a-pino (a confirmar)

- Pacote VSON8 (referido também como DGK/SON-8 em algumas fontes — **NÃO VERIFICADO qual é o código de pacote TI exato e suas dimensões precisas**; checar datasheet).
- Pinagem reportada via busca (TCAN1042-Q1/TCAN1042HGV-Q1, variante "V" com pino VIO): Pino1 TXD, Pino2 GND, Pino3 VCC, Pino4 RXD, Pino5 VIO, Pino6 CANL, Pino7 CANH, Pino8 STB — **esta ordem é IDÊNTICA à pinagem do TJA1042TK/3**. [I]/[F] com ressalva — esta informação vem de síntese de busca sobre o datasheet TI (SLLSEN0 / tcan1042-q1.pdf), **não foi confirmada por leitura direta do PDF ou de um mirror HTML nesta sessão** (todas as tentativas de abrir mirrors HTML de datasheetq.com para TI foram bloqueadas por Cloudflare / erro Java). **Tratar como NÃO VERIFICADO DE FORMA DEFINITIVA, apenas indicativo forte de possível compatibilidade.**
- **Ação recomendada antes de aprovar como substituto drop-in:** abrir manualmente https://www.ti.com/lit/ds/symlink/tcan1042-q1.pdf, seção "Pin Configuration and Functions", e comparar com a Fig. 2c do datasheet NXP TJA1042 (citada acima) para confirmar (a) ordem de pinos idêntica, (b) dimensões de pacote idênticas (3.00×3.00×0.85 mm), e (c) localização/tamanho do pad térmico exposto.
- Fonte: https://www.ti.com/lit/ds/symlink/tcan1042-q1.pdf ; mirror parcial (bloqueado) https://html.datasheetq.com/pdf-html/618324/TI1/TCAN1042.html (acesso 2026-10-23).

### 3.4 Microchip MCP2562FD — DFN8, NÃO confirmado como pino-compatível

- Pacote DFN-8, 3×3 mm. Pinagem reportada via busca: Pino1 TXD, Pino2 GND, Pino3 VDD, Pino4 RXD, Pino5 VIO, Pino6 CANL, Pino7 CANH, Pino8 STBY; pad exposto = GND. [I] — mesma ordem relativa ao TJA1042TK/3, **porém não verificado por leitura direta do datasheet primário** (ww1.microchip.com) nesta sessão (fetch não tentado por restrição de tempo/orçamento de chamadas). **NÃO VERIFICADO — tratar com cautela.**
- Fonte citada: https://ww1.microchip.com/downloads/en/DeviceDoc/MCP2561-2FD-High-Speed-CAN-Flexible-Data-Rate-Transceiver-20005284A.pdf (acesso 2026-10-23, via busca; não aberto diretamente).

### 3.5 Tabela resumo — transceptor CAN

| MPN | Fabricante | Pacote | CAN FD 5 Mbit/s | Pino-compatível c/ TJA1042TK/3 | AEC-Q | LCSC |
|---|---|---|---|---|---|---|
| **TJA1042TK/3** | NXP | HVSON8 3×3×0.85mm | **Sim [F]** | — (referência) | AEC-Q100 [F] | C131480 [F] |
| TCAN1044VDRBRQ1 | TI | VSON8 (DRB) 3×3mm | Sim (até 8 Mbps conforme família) [I] | **NÃO (ordem de pinos diferente)** [I]/NÃO VERIF. definitivo | AEC-Q100 (família "-Q1") [I] | NÃO VERIFICADO |
| TCAN1042HGV-Q1 | TI | VSON8 3×3mm (a confirmar dimensão exata) | Sim [I] | **Provável SIM — NÃO VERIFICADO definitivamente** | AEC-Q100 ("-Q1") [I] | NÃO VERIFICADO |
| MCP2562FD (DFN8) | Microchip | DFN-8 3×3mm | Sim (MCP256x FD family) [I] | Provável sim na ordem relativa — **NÃO VERIFICADO** | NÃO VERIFICADO | NÃO VERIFICADO |

---

## 4. Cristal 25 MHz, SMD 3225, para HSE do STM32H7

- Fórmula de cálculo do capacitor de carga (padrão, aplicável a qualquer MCU STM, conforme AN2867 "Oscillator design guide for STM8 and STM32 microcontrollers"): **C_load = 2 × (CL − C_stray)**, onde CL é o valor de capacitância de carga especificado pelo fabricante do cristal (datasheet) e C_stray é a capacitância parasita estimada de trilhas/pinos (tipicamente ~3–5 pF, deve ser verificada/ajustada pelo projetista). [F]/[I] — fórmula confirmada via referência cruzada de busca ao AN2867 (https://www.st.com/resource/en/application_note/an2867-oscillator-design-guide-for-stm8-and-stm32-microcontrollers-stmicroelectronics.pdf, acesso 2026-10-23; PDF não aberto diretamente nesta sessão, fetch ao st.com indisponível). **A fórmula em si é um fato de engenharia padrão e amplamente documentado, mas o texto exato do AN2867 não foi lido literalmente — marcar o detalhe fino (ex.: valor recomendado de C_stray) como NÃO VERIFICADO.**
- Os requisitos específicos de ESR máximo e "drive level"/gm do oscilador HSE do STM32H725 (seção do DS13311) **NÃO FORAM VERIFICADOS** nesta sessão (st.com inacessível); o projetista deve checar a seção "High-speed external clock signal (HSE)" do DS13311 antes de fechar a escolha do cristal.

### 4.1 YXC (Yangxing) X322525MOB4SI

- 25.000 MHz, pacote SMD 3225 (3.2×2.5×0.7 mm), **CL = 12 pF**, ESR ≤ 50 Ω, tolerância de frequência ±10 ppm (a 25 °C), estabilidade ±20 ppm, faixa de temperatura −40 °C a +85 °C. [F] Fonte: LCSC/JLCPCB — https://www.lcsc.com/product-detail/C9006.html e https://jlcpcb.com/partdetail/YXC_CrystalOscillators-X322525MOB4SI/C9006 (acesso 2026-10-23, via busca; fetch direto não realizado). LCSC part **C9006**.
- Com C_stray ≈ 4 pF (estimativa típica): C_load ≈ 2×(12−4) = **16 pF** (usar valor padrão mais próximo, ex. 15 pF ou 18 pF conforme disponibilidade). [I] — cálculo ilustrativo, ajustar conforme layout real.

### 4.2 ECS-250-8-33-JGN-TR

- 25 MHz, SMD 3225 (3.2×2.5×0.8 mm), **CL = 8 pF**, ESR ≤ 40 Ω, tolerância ±20 ppm, estabilidade ±30 ppm, faixa de temperatura −40 °C a +85 °C. [F] Fonte: LCSC — https://www.lcsc.com/product-detail/C312378.html (acesso 2026-10-23, via busca). LCSC part **C312378**.
- Com C_stray ≈ 4 pF: C_load ≈ 2×(8−4) = **8 pF**. [I]

### 4.3 Abracon ABM8-25.000MHZ-B2-T

- 25.000 MHz, pacote 4-SMD 3225 (3.2×2.5 mm), **CL = 18 pF**, ESR ≤ 50 Ω, tolerância ±20 ppm, estabilidade ±50 ppm, **faixa de temperatura −20 °C a +70 °C** (⚠ mais estreita que o range industrial −40/+85 °C do MCU — atentar se o projeto exigir faixa industrial completa). [F] Fonte: LCSC — https://www.lcsc.com/product-detail/C596899.html (acesso 2026-10-23, via busca). LCSC part **C596899**.

### 4.4 TXC 7V25000

- Reportado como CL = 18 pF típico para a série 7V em pacote 3225, mas **não foi encontrada uma página de datasheet específica e verificável do part exato "7V25000" nesta sessão — NÃO VERIFICADO.** Recomenda-se não usar este MPN sem localizar o datasheet exato da TXC Corporation primeiro.

### 4.5 Tabela resumo — cristal

| MPN | Fabricante | CL | ESR máx | Tolerância | Faixa temp. | LCSC |
|---|---|---|---|---|---|---|
| X322525MOB4SI | YXC | 12 pF | 50 Ω | ±10 ppm | −40 a +85 °C | C9006 [F] |
| ECS-250-8-33-JGN-TR | ECS Inc. | 8 pF | 40 Ω | ±20 ppm | −40 a +85 °C | C312378 [F] |
| ABM8-25.000MHZ-B2-T | Abracon | 18 pF | 50 Ω | ±20 ppm | **−20 a +70 °C** ⚠ | C596899 [F] |
| 7V25000 | TXC | NÃO VERIFICADO | NÃO VERIFICADO | NÃO VERIFICADO | NÃO VERIFICADO | NÃO VERIFICADO |

**Recomendação [I]:** X322525MOB4SI (YXC) como primária (faixa de temperatura industrial completa, ESR baixo, CL=12pF é um meio-termo razoável); ECS-250-8-33-JGN-TR como alternativa de segunda fonte.

---

## 5. Capacitores para alimentação do H7

### 5.1 VCAP — 2.2 µF X5R/X7R 0603 ≥6.3 V (ESR < 100 mΩ requerido)

- **Murata GRM188R60J225** (variante próxima real confirmada: **GRM188R60J226MEA0**, 2.2µF seria "225" no código — nota: o código "225" normalmente indica 2.2 µF (22×10^5 pF); a busca retornou majoritariamente dados do parente "226" = 22 µF, então **há ambiguidade de part number exato**; confirmar o sufixo completo antes de comprar). [I]/NÃO VERIFICADO quanto ao MPN exato — **recomenda-se re-verificar diretamente no part search da Murata (https://www.murata.com) o código exato para 2.2 µF, X5R, 0603, 6.3 V antes de fechar o BOM.**
- Pacote 0603, dielétrico X5R, tensão 6.3 V, faixa de temperatura −55 °C a +85 °C. [I] (dado genérico da família GRM188, não confirmado linha a linha para o valor exato de 2.2 µF).
- Datasheet de referência da família: https://www.lcsc.com/datasheet/C77042.pdf (acesso 2026-10-23, via busca, não confirmado qual exatamente é a variante 2.2µF/6.3V).
- **Recomendação prática [I]:** usar um capacitor 0603 2.2 µF X5R ≥6.3V de catálogo LCSC Basic (ex.: procurar por "2.2uF 0603 X5R 10V" como alternativa de tensão mais alta, que também atende ≥6.3V) — **NÃO foi possível obter um MPN específico 100% confirmado nesta sessão; marcar MPN exato como NÃO VERIFICADO.**

### 5.2 Capacitor 4.7 µF 0603/0805

- **Murata GRM188R61A475KAAJD**: 4.7 µF, 10 V, X5R, pacote 0603 (1.6×0.8 mm), tolerância ±10%, faixa de temperatura −55 °C a +85 °C. [F] Fonte: LCSC — https://www.lcsc.com/product-detail/C668355.html (acesso 2026-10-23, via busca). LCSC part **C668355**.
- Datasheet: https://datasheet.lcsc.com/lcsc/2006251713_Murata-GRM188R61A475KAAJD_C668355.pdf (não aberto diretamente nesta sessão).

### 5.3 Capacitor 10 µF 0805 (VFBSMPS — baixo ESR)

- **Samsung CL21A106KOQNNNG** (nota: LCSC lista a variante irmã **CL21A106KOQNNNE**, part C1713, como equivalente funcional "Basic"): 10 µF, 16 V, X5R, pacote 0805 (2.0×1.25 mm), tolerância ±10%, faixa de temperatura −55 °C a +85 °C. [F] Fonte: LCSC — https://www.lcsc.com/product-detail/C1713.html (acesso 2026-10-23, via busca). **ESR não especificado numericamente no resumo consultado — marcar valor de ESR específico como NÃO VERIFICADO**; datasheet completo necessário para confirmar adequação ao requisito "baixo ESR" do VFBSMPS.
- LCSC part **C1713** (Basic, conforme fonte).

### 5.4 Capacitor 220 pF NP0/C0G 0402/0603 (VLXSMPS)

- **Murata GRM1555C1H221JA01D**: 220 pF, 50 V, dielétrico **C0G (NP0)**, pacote 0402 (1.0×0.5 mm), tolerância ±5%, faixa de temperatura −55 °C a +125 °C. [F] Fonte: LCSC — https://www.lcsc.com/product-detail/C71693.html (acesso 2026-10-23, via busca). LCSC part **C71693**.

### 5.5 Tabela resumo — capacitores de potência H7

| Função | Valor | MPN | Fabricante | Pacote | LCSC | Confiança |
|---|---|---|---|---|---|---|
| VCAP | 2.2 µF X5R ≥6.3V | **MPN exato NÃO VERIFICADO** (família GRM188R6xJ2xx) | Murata | 0603 | NÃO VERIFICADO | Baixa — reconfirmar |
| — | 4.7 µF X5R 10V | GRM188R61A475KAAJD | Murata | 0603 | C668355 [F] | Alta |
| VFBSMPS | 10 µF X5R 16V | CL21A106KOQNNNE (basic) | Samsung E-M | 0805 | C1713 [F] | Média (ESR não confirmado) |
| VLXSMPS | 220 pF NP0/C0G | GRM1555C1H221JA01D | Murata | 0402 | C71693 [F] | Alta |

---

## 6. ESD/TVS para linhas CAN

### 6.1 STMicroelectronics ESDCAN24-2BLY

- Dispositivo TVS dual-line para proteção ESD de barramento CAN, pacote **SOT-23-3L**. Tensão de standoff reversa 24 V, breakdown ~27 V, capacitância ~25–30 pF por linha, potência de pico de pulso ~230 W (8/20 µs), qualificado **AEC-Q101**. [F]/[I] — dados obtidos via síntese de busca referenciando o datasheet oficial ST; **PDF original não aberto diretamente nesta sessão** (st.com inacessível): https://www.st.com/resource/en/datasheet/esdcan24-2bly.pdf (acesso 2026-10-23, via busca).
- **Pinagem reportada (SOT-23-3L): Pino 1 = linha 1 (ex. CAN_H), Pino 2 = GND (pino central/comum), Pino 3 = linha 2 (ex. CAN_L).** [I]/NÃO VERIFICADO em detalhe — esta é uma inferência de busca sobre o datasheet, **não confirmada por leitura direta do PDF ou de um diagrama de pacote**. **Recomenda-se fortemente abrir o datasheet ST diretamente (link acima) e confirmar visualmente a Fig. "Pin configuration" antes de desenhar o footprint**, pois a atribuição exata de GND ao pino central pode variar entre fabricantes de TVS dual-line em SOT-23.
- Preço/estoque (via busca, não confirmado por fetch direto): LCSC listaria estoque elevado (~55 mil un.) a partir de ~US$0,028/un; DigiKey listaria marca alternativa "EVVO" com preços de ~US$0,47 (1un) a ~US$0,10 (3000un). **NÃO VERIFICADO — dados de marca/estoque podem estar incorretos ou desatualizados (note que a listagem DigiKey aparentou referir a um part de marca "EVVO", possivelmente um cross/genérico, não a peça ST original — checar manualmente.)**

### 6.2 Nexperia PESD2CANFD27V-T

- Dispositivo ESD dual-line para CAN FD/CAN/FlexRay/SENT, pacote **SOT23 (TO-236AB)**. Tensão de standoff reversa 27 V, clamping ~33 V @1A, proteção ESD até 20 kV (IEC 61000-4-2), capacitância baixa ~6 pF, operação até 175 °C, qualificado **AEC-Q101**. [F]/[I] Fonte: datasheet Nexperia — https://assets.nexperia.com/documents/data-sheet/PESD2CANFD27V-T.pdf (acesso 2026-10-23, via busca; PDF não aberto diretamente nesta sessão, apenas citado).
- **Pinagem reportada: Pino 1 = K1 (cátodo diodo 1), Pino 2 = K2 (cátodo diodo 2), Pino 3 = CC (cátodo comum / deve ser ligado a GND).** [I]/NÃO VERIFICADO em detalhe — mesma ressalva do item 6.1: não confirmado por leitura direta do diagrama do datasheet nesta sessão. **Confirmar manualmente antes de finalizar o footprint — note que aqui o pino de GND (CC) está reportado como PINO 3, enquanto no ESDCAN24-2BLY o GND estaria reportado como PINO 2 (posição diferente!). Esta diferença de posição do pino de GND entre os dois candidatos É CRÍTICA para o layout e deve ser verificada com máxima prioridade nos datasheets originais antes de desenhar qualquer footprint compartilhado.**
- LCSC: part reportado **C552488** (variante -TR, fita e rolo) — https://www.lcsc.com/product-detail/C552488.html (acesso 2026-10-23, via busca). Estoque reportado "esgotado" em 2026-10-23, preço de referência ~US$0,08–0,12/un conforme quantidade. **NÃO VERIFICADO por fetch direto.**
- DigiKey: part PESD2CANFD27V-TR, estoque reportado "0, previsão de chegada 11-jan-2027" — https://www.digikey.com/en/products/detail/nexperia-usa-inc/PESD2CANFD27V-TR/6015087 (acesso 2026-10-23, via busca). **NÃO VERIFICADO por fetch direto.**

### 6.3 Tabela resumo — ESD CAN

| MPN | Fabricante | Pacote | Pino GND/comum (conforme busca, NÃO VERIFICADO por leitura direta) | AEC-Q | LCSC |
|---|---|---|---|---|---|
| ESDCAN24-2BLY | ST | SOT-23-3L | Pino 2 (central) — **confirmar manualmente** | AEC-Q101 [I] | NÃO VERIFICADO (LCSC part exato ambíguo nesta sessão) |
| PESD2CANFD27V-T(R) | Nexperia | SOT23 | Pino 3 (CC) — **confirmar manualmente** | AEC-Q101 [I] | C552488 [I] |

⚠ **Atenção crítica:** a posição do pino de GND/comum reportada difere entre os dois candidatos (pino 2 vs. pino 3). Isso **não foi confirmado por leitura direta de nenhum dos dois PDFs nesta sessão** (ambos falharam no fetch direto). **Não finalizar o footprint sem abrir manualmente os dois datasheets e confirmar visualmente o diagrama de pinagem.**

---

## 7. Conector SWD

### 7.1 Samtec FTSH-105-01-L-DV-K (2×5, 1.27 mm, SMD, com capa/shroud)

- 10 pinos (2×5), passo 1.27 mm, montagem SMD vertical, contatos banhados a ouro, faixa de temperatura operacional **−55 °C a +125 °C**, corrente por contato **3.4 A**, altura de isolamento 2.92 mm, comprimento do pino de acoplamento 3.05 mm. [F] Fonte: LCSC — https://lcsc.com/product-detail/Pin-Header-Female-Header_Samtec-FTSH-105-01-L-DV-K_C5155080.html (acesso 2026-10-23, via busca; fetch direto ao lcsc.com falhou). LCSC part **C5155080**.
- Datasheet: https://datasheet.lcsc.com/lcsc/1912111439_Samtec-FTSH-105-01-L-DV-K_C5155080.pdf (não aberto diretamente nesta sessão).
- Alternativas de outros fabricantes (CNC Tech, Amphenol) para o mesmo footprint 2×5 1.27 mm com shroud **não foram pesquisadas em detalhe nesta sessão — NÃO VERIFICADO**; recomenda-se busca adicional caso o Samtec FTSH-105 esteja indisponível.

### 7.2 Alternativa THT 1×4, passo 2.54 mm

- Header macho THT, 1×4, passo 2.54 mm — opção genérica amplamente disponível. [F] Fonte: LCSC — https://lcsc.com/product-detail/Header-Male-2-54_1x4_C124378.html (acesso 2026-10-23, via busca). LCSC part reportado **C124378** (genérico "Header-Male-2.54_1x4"); alternativa adicional **C5116483** (ZHOURI 2.54-1*4) — https://jlcpcb.com/partdetail/ZHOURI-2_54_14/C5116483.
- **Nota:** um conector 1×4 de 2.54mm cobre tipicamente apenas 4 sinais (ex. VCC/SWDIO/SWCLK/GND) — **não é um substituto funcional completo de um SWD 2×5 de 10 pinos (que inclui adicionalmente RESET, SWO/TDI, 3V3, e GNDs extras)**. Confirmar quais sinais são realmente necessários no projeto antes de adotar o header 1×4 como alternativa funcional, não apenas mecânica. [I]

### 7.3 Tabela resumo — conector SWD

| MPN | Fabricante | Config. | Passo | Tipo | LCSC |
|---|---|---|---|---|---|
| FTSH-105-01-L-DV-K | Samtec | 2×5 (10 pinos) | 1.27 mm | SMD, shroud | C5155080 [F] |
| Header-Male-2.54_1x4 (genérico) | diversos (ex. ZHOURI) | 1×4 (4 pinos) | 2.54 mm | THT | C124378 / C5116483 [F] |

---

## 8. Itens de valor fixo

### 8.1 Jumpers 0 Ω 0402/0603

- 0402: **UNI-ROYAL 0402WGF0000TCE**, LCSC Basic part **C17168**. [F]/[I] (via busca agregada a partir de listas de peças comuns JLCPCB — https://kaspercalc.com/JLCPCBResistors.html, acesso 2026-10-23; **não confirmado por fetch direto à página LCSC do part**, tratar como indicativo forte mas reconfirmar antes do BOM final).
- 0603: MPN específico **NÃO VERIFICADO** nesta sessão — recomenda-se buscar o equivalente 0603WGF0000TCE (ou similar) diretamente no LCSC antes de fechar o BOM.

### 8.2 Resistor 10 kΩ 0402 1%

- **UNI-ROYAL 0402WGF1002TCE**, LCSC Basic part **C25804**. [F]/[I] mesma ressalva de fonte acima (via busca/agregador, não confirmado por fetch direto).

### 8.3 BAT54S (dual schottky série, SOT-23) para grampeamento de linhas SBU

- Fabricantes alternativos: **Nexperia BAT54S** e **onsemi BAT54S**.
- Pinagem (SOT-23, reportada via busca sobre datasheets Nexperia e onsemi, **não confirmada por fetch direto do PDF** nesta sessão): **Pino 1 = Ânodo do diodo 1 (A1), Pino 2 = Cátodo do diodo 2 (K2), Pino 3 = nó comum Cátodo1/Ânodo2 (K1/A2)** — ou seja, os dois diodos Schottky estão em **série** entre os pinos 1 e 2, com o nó médio acessível no pino 3. [I]/NÃO VERIFICADO em detalhe fino — **esta topologia "em série" (não "série dupla com catodo comum") deve ser confirmada no diagrama do datasheet antes de usar para grampeamento de linhas SBU, pois a topologia de conexão (série vs. catodo-comum vs. anodo-comum) determina completamente a função de proteção.** Fontes: https://assets.nexperia.com/documents/data-sheet/BAT54S.pdf e https://www.onsemi.com/pdf/datasheet/bat54s-d.pdf (acesso 2026-10-23, via busca; nenhum dos dois PDFs foi aberto diretamente nesta sessão).
- Características elétricas gerais reportadas: tensão reversa máx. 30 V, corrente direta máx. 200 mA, Vf típica 0.24–0.8 V (conforme corrente). [I]/NÃO VERIFICADO em detalhe.
- LCSC: **BAT54S,235** (Nexperia) part **C503463**, estoque reportado ~19.130 un., preço a partir de ~US$0,059 (10+un) — https://www.lcsc.com/product-detail/C503463.html (acesso 2026-10-23, via busca). Alternativa **BAT54S-QR** part **C7507573**. **Preço/estoque NÃO VERIFICADO por fetch direto.**

### 8.4 Tabela resumo — itens de valor fixo

| Item | MPN | Fabricante | LCSC |
|---|---|---|---|
| 0 Ω 0402 | 0402WGF0000TCE | Uni-Royal | C17168 [I] |
| 0 Ω 0603 | NÃO VERIFICADO | — | NÃO VERIFICADO |
| 10 kΩ 0402 1% | 0402WGF1002TCE | Uni-Royal | C25804 [I] |
| BAT54S (SOT-23) | BAT54S,235 | Nexperia | C503463 [I] |
| BAT54S (alt.) | BAT54S-QR | Nexperia | C7507573 [I] |

---

## Resumo: escolha primária / alternativa / justificativa

| # | Item | Escolha primária | Alternativa | Justificativa |
|---|---|---|---|---|
| 1 | MCU | STM32H725ZGT6 (LCSC C730156) | STM32H735ZGT6 (pinout a confirmar) | 1 MB Flash + SMPS confirmados [F]; H735 adiciona cripto, mesma família/pacote mas pinout não confirmado pino-a-pino nesta sessão |
| 1b | MCU alternativas rejeitadas | — | STM32H725ZET6 (512KB, Flash insuficiente); STM32H723ZGT6 (SMPS em LQFP144 **conflito de fontes, NÃO VERIFICADO**) | H725ZET6 não atende requisito de 1MB; H723ZGT6 requer verificação manual da tabela de pacotes DS13310 antes de decidir |
| 2 | Indutor SMPS 2.2µH | Murata DFE201610E-2R2M=P2 (LCSC C337891) | TDK TFM201610ALMA2R2MTAA (LCSC C404810, AEC-Q200, mas DCR máx. 152mΩ ligeiramente acima do limite de 150mΩ) | Murata atende DCR≤150mΩ com folga (140mΩ); TDK é qualificado automotivo mas no limite da especificação de DCR |
| 3 | Transceptor CAN | **Manter TJA1042TK/3** (NXP, HVSON8) — pinagem e suporte a CAN FD 5Mbit/s **confirmados diretamente no datasheet** [F] | TCAN1042HGV-Q1 (TI) — pinagem aparentemente idêntica, mas **não confirmada por leitura direta do PDF**; TCAN1044VDRBRQ1 **não é pino-compatível** (ordem de pinos diferente) | TJA1042TK/3 é a única opção com compatibilidade de footprint 100% confirmada nesta pesquisa; trocar de fabricante exigiria reconfirmação manual do datasheet TI |
| 4 | Cristal 25MHz 3225 | YXC X322525MOB4SI (LCSC C9006, CL=12pF) | ECS-250-8-33-JGN-TR (LCSC C312378, CL=8pF) | YXC cobre faixa industrial completa −40/+85°C; ECS tem CL menor (pode simplificar capacitores de carga) |
| 5 | Cap. VCAP 2.2µF 0603 | **NÃO VERIFICADO — MPN exato a reconfirmar** | — | Ambiguidade entre códigos "225"(2.2µF) e "226"(22µF) na família Murata GRM188 encontrada na pesquisa |
| 5b | Cap. 4.7µF 0603 | Murata GRM188R61A475KAAJD (LCSC C668355) | — | Dados confirmados via LCSC |
| 5c | Cap. 10µF 0805 VFBSMPS | Samsung CL21A106KOQNNNE (LCSC C1713, "Basic") | — | ESR numérico não confirmado — reconfirmar antes de aprovar para VFBSMPS |
| 5d | Cap. 220pF NP0 0402 | Murata GRM1555C1H221JA01D (LCSC C71693) | — | Dados confirmados via LCSC |
| 6 | ESD CAN | **Confirmar pinagem antes de decidir** entre ESDCAN24-2BLY (ST) e PESD2CANFD27V-T (Nexperia) | — | Posição do pino de GND/comum reportada diferente entre os dois (pino 2 vs. pino 3) — **não confirmada por leitura direta de nenhum datasheet nesta sessão**; risco alto de erro de footprint se não revalidado manualmente |
| 7 | Header SWD | Samtec FTSH-105-01-L-DV-K (LCSC C5155080), 2×5 1.27mm SMD shroud | Header THT 1×4 2.54mm genérico (LCSC C124378) — cobertura funcional parcial, a confirmar sinais necessários | Samtec confirmado via LCSC; alternativa THT é mecanicamente simples mas pode não cobrir todos os sinais SWD necessários |
| 8 | Jumpers/resistores/BAT54S | 0R 0402 (C17168), 10k 0402 1% (C17168→C25804), BAT54S Nexperia (C503463) | — | Partes "Basic" comuns de JLCPCB; MPNs obtidos via agregador de listas comuns, não confirmados por fetch direto individual |

---

## Lista consolidada de itens marcados "NÃO VERIFICADO"

1. Conteúdo literal do datasheet DS13311 (STM32H725/735) — seções de HSE, VCAP, VFBSMPS, VLXSMPS com valores numéricos exatos — **PDF não pôde ser aberto diretamente nesta sessão** (timeout repetido em st.com).
2. Conteúdo literal do AN5419 (tabela de indutores SMPS recomendados pela ST) — mesmo motivo acima.
3. Compatibilidade de pinagem **pino-a-pino exata** entre STM32H725ZGT6 e STM32H735ZGT6 no pacote LQFP144 (apenas inferido como "mesma família/pacote", não confirmado tabela a tabela).
4. Disponibilidade do SMPS no pacote LQFP144 do **STM32H723ZGT6** — fontes contraditórias encontradas; necessário checar DS13310 diretamente (Tabela 5 / pin description).
5. Pinagem exata da TCAN1044VDRBRQ1 e TCAN1042HGV-Q1 (TI) e MCP2562FD (Microchip) — reportada apenas via síntese de busca, PDFs originais não abertos diretamente (bloqueios técnicos: binário ilegível ou Cloudflare).
6. Posição exata do pino de GND/comum no ESDCAN24-2BLY (ST) e no PESD2CANFD27V-T (Nexperia) — reportadas em posições diferentes (pino 2 vs. pino 3) por fontes de busca, **sem confirmação por leitura direta de nenhum dos dois datasheets**.
7. MPN exato do capacitor VCAP 2.2 µF X5R 0603 ≥6.3 V — ambiguidade entre códigos de parte "225" vs "226" na família Murata GRM188 encontrada na pesquisa.
8. Valor de ESR numérico específico do capacitor Samsung CL21A106KOQNNNE (10 µF 0805) — datasheet completo não aberto.
9. MPN exato do jumper 0 Ω em pacote 0603 (apenas 0402 foi confirmado via agregador).
10. Topologia interna exata (série vs. catodo comum) do BAT54S — reportada como "série" via busca, mas não confirmada por leitura direta do diagrama do datasheet.
11. Existência e especificações do cristal "TXC 7V25000" — não localizado um datasheet específico e verificável.
12. Alternativas de fabricante (CNC Tech, Amphenol) para o header SWD 2×5 1.27 mm com shroud — não pesquisadas nesta sessão.
13. **Todos os dados de preço e estoque de DigiKey, Mouser, LCSC e JLCPCB citados neste relatório** — nenhuma dessas páginas pôde ser aberta via fetch direto nesta sessão (bloqueios HTTP 403, timeout, ou falha de handshake TLS); os valores reportados vêm de resultados de mecanismo de busca com citação de URL e devem ser **reconfirmados manualmente pelo engenheiro antes de fechar qualquer pedido de compra**, pois preço e estoque são altamente voláteis e o método de coleta usado aqui não constitui confirmação direta da página.

---

*Fim do relatório. Compilado em 2026-10-23. Todas as URLs citadas devem ser reabertas manualmente para confirmação final antes de decisões de compra ou de layout de PCB, especialmente para os itens listados na seção "NÃO VERIFICADO" acima.*
