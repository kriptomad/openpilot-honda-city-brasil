# Relatório de Pesquisa de Componentes — Interface CAN-FD Automotiva (STM32H7, 4× CAN-FD, USB-FS)

**Data de acesso de todas as fontes (salvo indicação contrária): 22/10/2026**

**Nota metodológica (aplicável a todo o relatório):** A pesquisa foi conduzida por agentes paralelos que tentaram buscar e ler diretamente datasheets de fabricantes e páginas de distribuidores (DigiKey, Mouser, LCSC, JLCPCB). Em diversos casos `mouser.com`, `lcsc.com`, `jlcpcb.com`, `nexperia.com` (PDF) e `st.com` (PDF) bloquearam o acesso direto (HTTP 403 / falha de DNS-TLS) no ambiente de pesquisa. Nesses casos, usou-se: (a) espelhos de texto verbatim do datasheet (alldatasheet.com, datasheet4u.com), (b) o espelho `item.szlcsc.com` da própria base LCSC, ou (c) páginas DigiKey regionais (.cn/.mx/.in) que carregaram quando o domínio `.com` não carregou. Todo dado obtido **apenas** de resumo de busca por IA (não de uma página de fato aberta e lida) está marcado explicitamente **NÃO VERIFICADO**. Nenhum MPN, pinagem, preço ou estoque foi inventado — onde não há confirmação primária, isso é dito de forma explícita.

---

## 1. MCU — STM32H723VGT6 (LQFP100) e alternativas

### 1.1 Correção crítica de nomenclatura de documento

O datasheet correto do **STM32H723VGT6/STM32H723ZGT6** é o **DS13313** ("STM32H723VE/VG/ZE/ZG — Datasheet — production data"), não o DS13311 citado no pedido original. **DS13311** é, na verdade, o datasheet da família **STM32H725/735** (logo, é o documento correto para o STM32H725VGT6, mas não para o H723VGT6). Ambos remetem à mesma nota de aplicação **AN5419** ("Getting started with STM32H723/733, STM32H725/735 and STM32H730 Value Line hardware development"), provável origem da confusão.
Fonte: `https://www.st.com/resource/en/datasheet/stm32h723vg.pdf` (DS13313); `https://www.st.com/resource/en/datasheet/stm32h725vg.pdf` (DS13311).
RM0468 está correto como indicado no pedido: `https://www.st.com/resource/en/reference_manual/rm0468-...-stmicroelectronics.pdf`.

### 1.2 STM32H723VGT6 — parâmetros confirmados diretamente no PDF (DS13313 Rev.4)

| Parâmetro | Valor | Confiança | Fonte |
|---|---|---|---|
| FDCAN | **3** (2× FDCAN + 1× TT-FDCAN) | ✅ Alta — Tabela 1, p.17–18/257 | DS13313 |
| Flash | **1024 KB** (variante "G") | ✅ Alta — Tabela 1, p.17/257 | DS13313 |
| RAM total | **564 KB com ECC** (128KB DTCM + 320KB AXI SRAM + 32KB SRAM1/2 + 16KB SRAM4 + 64KB ITCM + 4KB backup SRAM — breakdown reconciliado matematicamente, não lido como tabela única) | ✅ Alta (soma) / 🟡 breakdown por bloco | DS13313, Features bullets |
| Freq. máx. CPU | **550 MHz** | ✅ Alta — Tabela 1, p.18/257 | DS13313 + DigiKey |
| SMPS | **NÃO possui — somente LDO** (confirmado: nenhum bloco SMPS na Figura 10 "Power supply scheme", §6.1.6, p.110/257; Tabela 1 nem tem linha "SMPS") | ✅ Alta | DS13313 |
| VCAP (nº de pinos / capacitância) | 2 pinos (VCAP1/VCAP2), ~2,2 µF cerâmico X7R recomendado | 🟡 Moderada — corroborado por múltiplas fontes/comunidade ST, mas tabela exata do PDF não citada literalmente | ST Community (ver abaixo) + prática padrão família H7 |
| Decoupling VDD/VDDA/VREF+/VBAT | ~100 nF por pino VDD/VDDA + bulk 1–4,7 µF; VBAT ~100nF–1µF | 🔴 **NÃO VERIFICADO** — não citado literalmente da tabela/figura "Power supply scheme" do DS13313 | Prática genérica STM32H7, não confirmada no PDF |
| HSE (cristal) | **4–50 MHz** | ✅ Conteúdo confirmado — tabela "HSE oscillator characteristics" | 🔴 Nº exato de página NÃO VERIFICADO |
| SYSCFG_PKGR código p/ LQFP100 | **NÃO VERIFICADO** — seção correta localizada (RM0468 §13.4.2, campo PKG[3:0]), mas valor numérico do código não confirmado com citação confiável | 🔴 | RM0468 |
| PC2/PC3 em LQFP100 | **Confirmado em conteúdo**: disponíveis somente como PC2_C/PC3_C (função analógica via chave resistiva; uso digital não recomendado) | 🟡 — corroborado por fórum oficial ST, texto literal da nota de rodapé da tabela não citado | `community.st.com/stm32-mcus-products-25/stm32h723-ulpi-and-pc2-c-pc3-c-161159` |
| ADC: PC0/PC4/PC5/PB1 | PC0=ADC1/2/3_INP10; PC4=ADC1/2_INP4; PC5=ADC1/2_INP8; PB1=ADC1/2_INP5 | 🟡 Moderada — fonte secundária (fórum ST), não lido na tabela primária | `community.st.com/.../pin-out-of-stm32h723-vs-stm32h7-nucleo-144-boards-150456` |

### 1.3 Mapeamento de Alternate Function (AF) — ✅ Verificado diretamente na Tabela 8 "STM32H723 pin alternate functions" (DS13313 Rev.4, p.72–85/257)

| Pino | Sinal | AF | Observação |
|---|---|---|---|
| PB8 | FDCAN1_RX | **AF9** | p.74/257 |
| PB9 | FDCAN1_TX | **AF9** | p.74/257 |
| PB12 | FDCAN2_RX | **AF9** | p.75/257 |
| PB13 | FDCAN2_TX | **AF9** | p.75/257 |
| PB5 | FDCAN2_RX (remap) | **AF9** | p.74/257 |
| PB6 | FDCAN2_TX (remap) | **AF9** | p.74/257 |
| PD12 | FDCAN3_RX | **AF5** | p.79/257 |
| PD13 | FDCAN3_TX | **AF5** | p.79/257 |
| PA13 | SWDIO | **AF0** (JTMS-SWDIO) | p.73/257 |
| PA14 | SWCLK | **AF0** (JTCK-SWCLK) | p.73/257 |
| PA11 | USB_FS DM (OTG_HS c/ PHY interno) | **Sem número de AF** — não é uma Alternate Function, é "Additional function" fixa, fora do mux AF0-AF15 | Tabela 7, p.66/257. Linha completa de AF para PA11 não inclui nenhum sinal USB; FDCAN1_RX também aparece como AF9 em PA11, mas há alternativa em PB8 |
| PA12 | USB_FS DP | **Sem número de AF** (mesma observação) | Tabela 7, p.66/257 |

### 1.4 Alternativas (≥3 FDCAN)

| MCU | Pacote | Datasheet | FDCAN | Flash | Freq. máx | SMPS | Lifecycle |
|---|---|---|---|---|---|---|---|
| **STM32H723ZGT6** | LQFP144 | DS13313 (mesmo doc) — `stm32h723zg.pdf` | 3 | 1024 KB | 550 MHz | Não — LDO somente (mesma Fig.10) | **Active**, disponibilidade garantida até 01/2035 |
| **STM32H725VGT6** | LQFP100 | DS13311 Rev.5 — `stm32h725vg.pdf` | 3 | 1024 KB | 550 MHz | **Sim** — "Embedded DCDC and LDO regulator"; Fig.14 + Tabela 2 p.20/283 mostram SMPS disponível mesmo no LQFP100 (diferença de silício vs. H723) | **Active**, disponibilidade até 01/2035 |

### 1.5 Distribuidores / JLCPCB — MCU

| Peça | LCSC P/N | Preço LCSC (qty1) | Estoque LCSC | DigiKey/Mouser | JLCPCB Basic/Extended |
|---|---|---|---|---|---|
| STM32H723VGT6 | **C730142** ✅ (szlcsc.com, JSON-LD real) | ¥84,04 CNY | 100 un. | NÃO VERIFICADO (bloqueado) | NÃO VERIFICADO |
| STM32H725VGT6 | **C730154** ✅ | ¥76,84 CNY | 0 un. (OutOfStock) | NÃO VERIFICADO | NÃO VERIFICADO |
| STM32H723ZGT6 | **C730146** (pacote confirmado) | NÃO VERIFICADO | NÃO VERIFICADO | NÃO VERIFICADO | NÃO VERIFICADO |

URLs DigiKey (página existe, preço/estoque não renderizado no fetch): `digikey.com/en/products/detail/stmicroelectronics/STM32H723VGT6/13171212`; `.../STM32H725VGT6/13171209`; `.../STM32H723ZGT6/13171205`.

---

## 2. Transceptor CAN-FD, SOIC-8 com pino VIO

### Tabela de pinagem comparativa (verificada em datasheets primários TI/NXP/Microchip)

| Peça | Pacote | Pino1 | Pino2 | Pino3 | Pino4 | Pino5 | Pino6 | Pino7 | Pino8 |
|---|---|---|---|---|---|---|---|---|---|
| **TCAN1044VDRQ1** (TI) | SOIC-8 | TXD | GND | VCC | RXD | **VIO** | CANL | CANH | **STB** |
| **TJA1042T/3** (NXP) | SOIC-8 | TXD | GND | VCC | RXD | **VIO** | CANL | CANH | **STB** |
| **TJA1042TK/3** (NXP) | **HVSON8/DFN8** (⚠️ NÃO é SOIC-8) | TXD | GND | VCC | RXD | VIO | CANL | CANH | STB |
| **TJA1051T/3** (NXP) | SOIC-8 | TXD | GND | VCC | RXD | **VIO** | CANL | CANH | **"S" (somente Silent, sem wake)** ⚠️ incompatível funcionalmente |
| **TCAN1042VDRQ1** (TI) | SOIC-8 | TXD | GND | VCC | RXD | **VIO** | CANL | CANH | **STB** |
| **MCP2562FDT-x/SN** (Microchip) | SOIC-8 | TXD | VSS | VDD | RXD | **VIO** | CANL | CANH | **STBY** |
| **TJA1463AT** (NXP) | **SOIC-14** ⚠️ incompatível (contagem de pinos) | TXD | GND | VCC | RXD | VIO | EN | INH | ERR_N (+ WAKE, VBAT, CANL, CANH, STB_N) |

### Parâmetros elétricos e qualificação

| Peça | Max. CAN-FD | ISO 11898-2 | Proteção de barramento | AEC-Q100 | Temp. | Lifecycle | Datasheet |
|---|---|---|---|---|---|---|---|
| **TCAN1044VDRQ1** | **8 Mbps** | 2016, confirmado | ±58 V | Grade 1 (–40 a 125°C) | –40 a 125°C | **Active** | TI SLLSF17D — `ti.com/lit/ds/symlink/tcan1044-q1.pdf` |
| **TJA1042T/3** | 5 Mbit/s (fase rápida) | 2016 + SAE J2284-1/5 | ±58 V | Qualificado | Tj –40 a 150°C | **Active** (Rev.11, jan/2023) | NXP — `nxp.com/docs/en/data-sheet/TJA1042.pdf` |
| **TJA1042TK/3** | 5 Mbit/s (mesmo die) | idem | ±58 V | Qualificado | idem | Active | mesmo doc |
| **TJA1051T/3** | 5 Mbit/s (fase rápida) — corrige hipótese do pedido de que seria "CAN clássico apenas" | 2016 + SAE J2284 | ±58 V | Qualificado | Tj –40 a 150°C | **Active** (Rev.9, nov/2017) | NXP — `nxp.com/docs/en/data-sheet/TJA1051.pdf` |
| **TCAN1042VDRQ1** | ⚠️ **2 Mbps apenas** (não é sufixo "G"; só TCAN1042G-Q1/HG-Q1 atingem 5 Mbps) | 2016 + ISO 11898-5:2007 | ±58 V | Grade 1 | –55 a 125°C | Active | TI SLLSES9D — `ti.com/lit/ds/symlink/tcan1042-q1.pdf` |
| **MCP2562FDT-x/SN** | 8 Mbps (anunciado) / 5 Mbps (simetria garantida no texto — inconsistência interna no próprio datasheet) | 2016 + ISO 11898-5 | ESD ±14kV (IEC 61000-4-2) | "Automotive Qualified" genérico, **grade exato NÃO VERIFICADO** — variante automotiva tem sufixo "VAO" no P/N | E:–40 a 125°C / H:–40 a 150°C | **Active** | Microchip DS20005284B |
| **TJA1463AT** | 8 Mbit/s com SIC | **2024** (edição mais nova que as demais) | –36V a +40V (arquitetura diferente, pino VBAT) | Grade 1 | Tj –40 a 150°C | Active (Rev.3.0, fev/2025) | NXP — `nxp.com/docs/en/data-sheet/TJA1463.pdf` |

### Distribuidores / JLCPCB

| Peça | LCSC | DigiKey | JLCPCB |
|---|---|---|---|
| TCAN1044VDRQ1 | C1852061 ⚠️NÃO VERIFICADO (só busca) | NÃO VERIFICADO | "Extended" ⚠️NÃO VERIFICADO (só busca) |
| TJA1042T/3 | C140827 ⚠️NÃO VERIFICADO | NÃO VERIFICADO | NÃO VERIFICADO |
| TJA1051T/3 | C5342108 ⚠️NÃO VERIFICADO | NÃO VERIFICADO | NÃO VERIFICADO |
| TJA1042TK/3 | C20234932 ⚠️NÃO VERIFICADO | NÃO VERIFICADO | NÃO VERIFICADO |
| MCP2562FDT-H/SN | C623224 ⚠️NÃO VERIFICADO | ✅ **Verificado direto**: US$1,38 (qty1), estoque 5.539, Active — `digikey.com/.../MCP2562FDT-H-SN/...` | NÃO VERIFICADO |
| TJA1463 | — | NÃO VERIFICADO | NÃO VERIFICADO |

**Conclusão:** TCAN1044VDRQ1, TJA1042T/3, TJA1042TK/3 (pacote diferente), TCAN1042VDRQ1 e MCP2562FD compartilham o mesmo padrão de pinagem 1-8 (compatibilidade cruzada entre fabricantes em footprint SOIC-8). **TJA1051T/3 quebra compatibilidade funcional** no pino 8 (somente Silent, sem wake-up por barramento). **TJA1463 é incompatível em contagem de pinos** (14, não 8).

---

## 3. Proteção ESD/TVS do barramento CAN-FD

| Peça | Fabricante | Pacote | Rating CAN-FD explícito | VRWM | VBR | VCL | AEC-Q101 | Lifecycle | Datasheet |
|---|---|---|---|---|---|---|---|---|---|
| **PESD2CAN** | Nexperia | SOT-23 | ❌ **NÃO** — nenhuma menção a CAN-FD no documento; só "CAN bus protection" genérico | 24 V | 26,2 V (mín.) | 41 V @ 5A (8/20µs) | Sim | **NRND** | `assets.nexperia.com/documents/data-sheet/PESD2CAN.pdf` (confirmado via espelho verbatim) |
| **PESD2CANFD27V-T/-TR** | Nexperia | SOT-23 | ✅ **Sim**, no próprio nome comercial do produto | 27 V | 28 V (mín.) | 44 V @ 2,5A (8/20µs) | Citado como Q101 no texto, mas DigiKey classifica como "AEC-Q100" (conflito não resolvido) | **Active** | `assets.nexperia.com/documents/data-sheet/PESD2CANFD27V-T.pdf` |
| **ESDCAN24-2BLY** | STMicroelectronics | SOT-23-3L | ✅ **Sim, citação explícita e direta**: *"compliant with CAN-FD and high speed buses like FlexRay, USB, and even the future CAN XL"* | 24 V | 26,2–27 V (conflito mín./típ. não resolvido) | 40 V @ 5,5A (8/20µs) | Sim | **Active/Production** | `st.com/resource/en/datasheet/esdcan24-2bly.pdf` (confirmado via espelho verbatim) |

**Conformidade a normas (ESDCAN24-2BLY, texto literal do datasheet):** UL94 V0; J-STD-020 MSL1; ISO 16750-2; IEC 61000-4-4 (EFT) 4kV; ISO 10605 (±30kV contato/ar); **ISO 7637-3 Pulso 3a −150V, Pulso 3b +150V, Pulso 2a ±85V**.

**Pinout CANH/CANL/GND exato:** NÃO VERIFICADO para os três (diagramas de pinagem originais não puderam ser abertos com confiabilidade; resumos de IA deram respostas mutuamente inconsistentes).

| Peça | DigiKey (22/10/2026) | LCSC | JLCPCB |
|---|---|---|---|
| PESD2CAN | ✅ Verificado direto: estoque 25.144 un. (NRND); qty1 US$0,66 / qty10 US$0,406 / qty100 US$0,2587 / qty9000 US$0,12857 — `digikey.com/.../PESD2CAN-215/1589994` | C75176 ⚠️NÃO VERIFICADO | NÃO VERIFICADO |
| PESD2CANFD27V-T | ✅ Verificado direto: estoque **0** (3000 un. esperadas 22/dez/2026); qty1 US$0,47 / qty100 US$0,1814 / qty9000 US$0,08727 — `digikey.com.mx/.../PESD2CANFD27V-TR/11686246` | C552488 ⚠️NÃO VERIFICADO | NÃO VERIFICADO |
| ESDCAN24-2BLY | Página confirmada Active/AEC-Q101, mas tabela de preço/estoque não renderizou | NÃO VERIFICADO (só genuíno ST; achados são de 2ªs fontes "UMW"/"TECH PUBLIC") | NÃO VERIFICADO |

**Conclusão:** ESDCAN24-2BLY é a única peça com afirmação explícita de compatibilidade CAN-FD pelo fabricante **e** status Active/Production. PESD2CANFD27V-T é a escolha correta por nomenclatura Nexperia, mas estoque zero no momento. PESD2CAN é só para CAN clássico e está em NRND.

---

## 4. Proteção de entrada 12V e polaridade reversa

### 4.1 TVS de alimentação (dados idênticos confirmados em Vishay e Littelfuse)

| Parte | Pacote | VWM | VBR mín/máx | VC @ IPP | IPP máx | Potência pico |
|---|---|---|---|---|---|---|
| **SMAJ16CA** | SMA/DO-214AC | 16,0 V | 17,8/19,7 V | 26,0 V | 15,4 A | 400 W (10/1000µs) |
| **SMBJ18CA** | SMB/DO-214AA | 18,0 V | 20,0/22,1 V | 29,2 V | 20,5 A | 600 W |
| **SMBJ24CA** | SMB/DO-214AA | 24,0 V | 26,7/29,5 V | 38,9 V | 15,4 A | 600 W |

Fontes: Vishay Doc.88390/88392 (`vishay.com/docs/88390/smaj50a.pdf`, `.../88392/smbj.pdf`); Littelfuse SMAJ/SMBJ series datasheets (acessados via web.archive.org devido a bloqueio 403 do domínio principal).

**Normas (verificado via app notes primários, não inventado):**
- TI SNOAAA1 (nov/2023, `ti.com/lit/an/snoaaa1/snoaaa1.pdf`): *load dump* = desconexão da bateria com alternador ainda carregando; ISO 16750-2 Testes A/B "anteriormente designados 5A e 5B na ISO 7637-2"; para sistemas 12V, Us de pico varia **79–101V**; para 24V, **151–202V**.
- Vishay AN87003 (`vishay.com/docs/87003/vishayloaddumptvsseriesfor24vpowertrains.pdf`): ISO 16750-2 (2010) exige 10 pulsos em 10 minutos; ISO 7637-2 (2004) antiga exigia só 1 pulso único.
- **Escopo exato dos pulsos 2a/3a/3b da ISO 7637-2: NÃO VERIFICADO** — nenhuma fonte primária aberta com confiabilidade definiu o escopo físico genérico desses pulsos (bloqueios de acesso consistentes a Littelfuse AN e onsemi TND6424). Os números 2a/3a/3b citados no datasheet ESDCAN24-2BLY referem-se à robustez do próprio componente, não ao escopo da norma.

Distribuidores (SMAJ16CA/SMBJ18CA/SMBJ24CA): **NÃO VERIFICADO** em todos os distribuidores — bloqueio de acesso total nesta sessão.

### 4.2 Proteção de polaridade reversa

| Peça | O que é / achado | AEC-Q10x | Lifecycle | Fonte |
|---|---|---|---|---|
| **"HY12P03C2"** | 🔴 **NÃO VERIFICADO.** Alegado MOSFET canal-P "HUAYI Microelectronics" (Vds −30V, Id −50A, PPAK5x6-8L) só aparece em agregadores não-oficiais (alldatasheet, datasheet4u); nenhum fabricante tier-1 o lista; site do fabricante alegado inacessível. **Não usar sem datasheet original confirmado manualmente.** | — | — | — |
| **"BAS40WS"** | ⚠️ **Não é zener — é diodo Schottky duplo.** Além disso, "BAS40WS" (com "S") **não é produto Nexperia/Diodes/onsemi** — esses fabricantes só produzem **BAS40W** (sem S), que está **EOL** (PCN-2623, EOL 15/nov/2023, `diodes.com/assets/PCN-Files/Diodes_PCN_2623_Rev1_EOL.pdf`). "BAS40WS" aparece só em fabricantes secundários (JSCJ, Panjit, GMW), pacote SOT-323/SC-70, especificações assumidas equivalentes ao BAS40W mas não confirmadas pino-a-pino. | NÃO VERIFICADO | BAS40W = **EOL**; "BAS40WS" sem rótulo claro | `diodes.com/part/view/BAS40W`; `panjit.com.tw/upload/datasheet/BAS40WS.pdf` |
| **DMP4065S-7 (Diodes Inc.)** | MOSFET canal-P, 40V, SOT-23, modo enriquecimento. Id contínuo: **conflito não resolvido entre fontes** (−2,4A vs −3,4A); Rds(on) ~80-100mΩ não confirmado com certeza total | NÃO VERIFICADO | Sem PCN de EOL encontrada (indício de Active, não confirmado) | `diodes.com/part/view/DMP4065S`; `diodes.com/assets/Datasheets/DMP4065S.pdf` (acessível) |
| **LM74700-Q1 (TI)** | ✅ **Melhor opção, totalmente verificada.** Controlador de diodo ideal p/ MOSFET canal-N externo. *"AEC-Q100 qualified... Device temperature grade 1: –40°C to +125°C... HBM level 2... CDM level C4B"*. Faixa operação 3,2–65V; reversa suportada −65V; SOT-23-6/SOT-23-THN; *"Meets automotive ISO7637 transient requirements with a suitable TVS Diode"* | **Grade 1, confirmado** | **Active** | `ti.com/product/LM74700-Q1`; `ti.com/lit/ds/symlink/lm74700-q1.pdf` |

Distribuidores: NÃO VERIFICADO diretamente para todas as 4 peças (bloqueio de acesso consistente).

---

## 5. Reguladores de tensão e diodos retificadores

### 5.1 Buck 5V

| Peça | Pacote | VIN operação | Iout | AEC-Q100 | Lifecycle | Datasheet |
|---|---|---|---|---|---|---|
| **TPS5450DDAR** | SOIC-8 PowerPAD | **5,5–36V** (abs. máx até 40V) | ⚠️ **5A contínuo / 6A pico** (NÃO 3A — 3A é do TPS5430) | Não qualificado | Família Active, mas **TPS5450DDAR especificamente NRND** (addendum do datasheet + Octopart) | TI SLVS757E — `ti.com/lit/ds/symlink/tps5450.pdf` |
| **TPS54540-Q1** | HSOIC-8 PowerPAD | 4,5–42V (conflito interno: tabela diz 4,5-60V) | 5A | **Sim, Grade 1** | ⚠️ **NRND** (TI recomenda substituto TPS54540B-Q1, Active) | TI SLVSC56B — `ti.com/lit/ds/symlink/tps54540-q1.pdf` |
| **LMR33630-Q1** | VQFN-HR 12-pin | 3,8–36V (abs. máx 38V) | 3A | **Sim, Grade 1**, HBM L2, CDM C5 | **Active** | TI SNVSB26C — `ti.com/lit/ds/symlink/lmr33630-q1.pdf` |
| **TPS5430-Q1** | SOIC-8 PowerPAD | 5,5–36V | 3A contínuo/4A pico | ⚠️ **NÃO VERIFICADO formalmente** — datasheet não contém "AEC-Q100 Qualified" com grade explícito, só menções a normas de teste ESD; dúvida pública no fórum TI E2E sobre isso | **Active** | TI SLVS751F — `ti.com/lit/ds/symlink/tps5430-q1.pdf` |

**Recomendação:** usar **TPS54540-Q1/B** ou **LMR33630-Q1** quando Grade AEC-Q100 explícito for requisito.

### 5.2 Buck 3,3V

| Peça | VIN operação | Iout | Pacote | AEC-Q100 | Lifecycle | Datasheet |
|---|---|---|---|---|---|---|
| **XL1509-3.3E1** (XLSEMI) | 4,5–40V | 2A (⚠️ não 3A) | **Somente SOP-8** | NÃO VERIFICADO | NÃO VERIFICADO (não rotulado) | `xlsemi.com/datasheet/XL1509-EN.pdf` |
| **TPS562201** | **4,5–17V** | 2A (ILIM 3,2-4A) | **Somente SOT-23-6** | ❌ **Confirmado negativo** — `TPS562201-Q1` retorna HTTP 404, variante -Q1 não existe | **Active** | TI SLVSD91D — `ti.com/lit/ds/symlink/tps562201.pdf` |
| **AP63203 / AP63203Q** | 3,8–32V | 2A | TSOT26 | AP63203 comercial = Não; **AP63203Q = Sim, Grade 1** | NÃO VERIFICADO (página bloqueada) | DS41326 (comercial) / DS43698 (automotivo) — `diodes.com/datasheet/download/...` |
| **TLV62569** | ⚠️ **apenas 2,5–5,5V** — **NÃO serve para 12V→3,3V direto** | 0-2A | SOT-23-5/6/SOT-563 (3 variantes) | ❌ Confirmado negativo (TLV62569-Q1 → HTTP 404) | **Active** | TI SLVSDG1C — `ti.com/lit/ds/symlink/tlv62569.pdf` |

**Recomendação (2 melhores alternativas de 3 solicitadas):** **TPS562201** (melhor documentado, VIN 4,5-17V adequado, dados DigiKey verificados) e **AP63203Q** (única com AEC-Q100 formal). **TLV62569 descartado** para 12V direto (VIN incompatível).

### 5.3 Diodos Schottky diversos

| Peça | Fabricante | Tipo/Pacote | VRRM | IF(AV) | Status | Fonte |
|---|---|---|---|---|---|---|
| **SM540C** | 🔴 **NÃO VERIFICADO quase tudo** — provável LRC (China), ausente de DigiKey/Mouser | — | — | — | — | — |
| **B320AE** | ✅ Diodes Inc., Schottky single, **SMA/DO-214AC** | 20V | 3A | Lifecycle não rotulado; AEC-Q101 NÃO VERIFICADO (confundido com P/N distinto "B320A-13-F") | `diodes.com/datasheet/download/B320AE.pdf` |
| **BAS70H** | ⚠️ Nexperia, Schottky **single** (NÃO dual), pacote **SOD-123F** (NÃO SOT23) | 70V | 70mA | DigiKey: estoque 0 (lead 30 sem.) | alldatasheet mirror (PDF Nexperia bloqueado) — equivalente dual real é **BAS70-04/-05/-06** |
| **"MBR" genérico → MBRS340T3G** | onsemi, Schottky single, **SMC/DO-214AB** (não SMB) | 40V | 3A | Estoque 156.680 un. DigiKey | `onsemi.com/pdf/datasheet/mbrs340t3-d.pdf` |

Distribuidores verificados diretamente: **B320AE** (DigiKey: estoque 14.921 un., qty1 US$0,60/qty100 US$0,2333); **BAS70H** (DigiKey: estoque 0, qty1 US$0,24/qty100 US$0,0911); **MBRS340T3G** (DigiKey: estoque 156.680 un., qty1 US$1,02/qty100 US$0,4127). SM540C: NÃO VERIFICADO.

---

## 6. Chave de distribuição de energia USB

| Peça | Pacote | Pinout | Corrente limite | AEC-Q100 | Lifecycle | Datasheet |
|---|---|---|---|---|---|---|
| **AP22615AWU-7** | ⚠️ **TSOT26 (6 pinos)** — NÃO SOT23-5 | P1 OUT, P2 GND, P3 FLG (OD, ativo-baixo), P4 EN, P5 **ISET**, P6 IN | Ajustável via RLIM: 0,4–4,0A | "Contact us" para variante automotiva — sem SKU automotivo público | NÃO VERIFICADO | Diodes DS41022 Rev.7-2 — `diodes.com/datasheet/download/AP22815_615.pdf` |
| **TPS2051** (original) | Só SOIC-8/PDIP-8 (sem SOT23-5) | — | 0,9A típ | Não | **Active** | TI SLVS172A |
| **TPS2051B** | SOIC/SOT-23-5/HVSSOP/SON | P1 OUT, P2 GND, P3 OC, P4 EN, P5 IN | 1A típ | **TPS2051B-Q1 existe**, Grade 1 | **Active** | TI SLVS514P |
| **TPS2051C** | MSOP-PowerPAD/VSSOP/SOT-23-5 | P1 OUT, P2 GND, P3 FLT, P4 EN, P5 IN | 0,5/1/1,5/2A fixo | sugerido -Q1, NÃO VERIFICADO | **Active** | TI SLVSAU6I |

**⚠️ Incompatibilidade confirmada:** AP22615AWU-7 (6 pinos) e TPS2051B/C (5 pinos) **não são pino-a-pino compatíveis** — divergem a partir do pino 5 (ISET vs IN). Equivalente de 5 pinos da Diodes seria o AP22815AWT-7 (pinout inferido, não confirmado em tabela separada).

Distribuidores: NÃO VERIFICADO para as três peças (bloqueio de acesso).

---

## 7. Conectores

### 7.1 USB-C

| Peça | Fabricante | Nº pinos | Pacote | Datasheet | JLCPCB |
|---|---|---|---|---|---|
| **"TYPE-C-31-M-04"** | ⚠️ Korean Hroparts Elec | **24 pinos** (achado crítico: NÃO é 16 pinos como premissa do pedido) | SMD lateral | `atta.szlcsc.com/.../C129018_...WJ26275.PDF` (LCSC C129018) | "Extended" (verificação indireta) |
| **GCT USB4105** | Global Connector Technology | **16 pinos** ✅ (confirmado — correto para USB 2.0+alimentação) | SMD | `gct.co/files/drawings/usb4105.pdf` (confirmado acessível) | — |
| **TYPE-C-31-M-12** (Hroparts) | Korean Hroparts Elec | **16 pinos** ✅ — este é o P/N correto para 16 pinos, não o M-04 | SMD | `atta.szlcsc.com/.../C165948_...WJ310728.PDF` (LCSC C165948) | Estoque >330.000 un. (verificação indireta) |

### 7.2 USB-A

| Peça | Achado | Fonte |
|---|---|---|
| **"10.0QHHTZB6.3"** | ⚠️ Fabricante **SHOU HAN**, confirmado como **SMD** (montagem lateral), **NÃO through-hole** como premissa do pedido. LCSC C668591. | `atta.szlcsc.com/.../C668591_...WJ323165.PDF` |
| **Molex 67643-2910** (alternativa THT real) | USB-A fêmea, 4 pinos, right-angle, THT, 1,5A/30V | `molex.com/pdm_docs/sd/676432910_sd.pdf` (não confirmado por fetch direto, mas URL localizada) |
| **Amphenol 87520-0010BLF** (alternativa THT) | USB-A fêmea, THT, 3A, −55 a 85°C | Verificação indireta apenas — página exata não confirmada |

### 7.3 SWD Header

| Peça | Especificação | Confiança |
|---|---|---|
| **Samtec FTSH-105-01-L-DV-K** | 1,27mm, 2×5, SMT, shrouded, −55 a 125°C | 🔴 Verificação indireta (fetch bloqueado em Mouser/DigiKey/PDF) |
| **Samtec TSW-105 (série, 2,54mm 1×5 THT)** | Pitch 2,54mm, contato quadrado 0,635mm, −55 a 125°C | 🔴 Série confirmada; P/N exato de 5 posições (ex. TSW-105-07-G-S) não confirmado |

---

## 8. Cristal 25 MHz / 3225 SMD

| Peça | Carga | Tolerância | Temp. | Pacote | JLCPCB | Fonte |
|---|---|---|---|---|---|---|
| **Yangxing X322525MOB4SI** | ⚠️ **12 pF** (não 10 pF como premissa) | ±10 ppm | −40 a 85°C | SMD3225-4P | "Basic Part" (indireto) | LCSC C9006 — `atta.szlcsc.com/.../C9006_...YSX321SL.PDF`. Nota: fabricante indica substituição p/ XL2EL89COI-111YLC-25M |
| **"ECS-250-10-33-TR"** | ⚠️ **Part number exato não existe** como SKU comercial | — | — | — | — | NÃO VERIFICADO |
| **ECS-250-10-33-JGN-TR** (SKU real da mesma família, 10pF) | **10 pF** ✅ | ±20 ppm | **−40 a 85°C** | 4-SMD No Lead 3225 | — | ✅ DigiKey verificado direto: estoque 777 un., qty1 US$0,50/qty100 US$0,3812 — `digikey.com/.../ECS-250-10-33-JGN-TR/15777834`; datasheet `ecsxtal.com/store/pdf/ecx-32.pdf` |

---

## 9. LED RGB ânodo comum, SMD 4 pinos

| Peça | Fabricante | Config. | Pacote | Vf (R/G/B) | Fonte |
|---|---|---|---|---|---|
| **FM-B1921RGBA-SH** | Foshan NationStar (国星光电) | **Ânodo comum** ✅ | SMD-4P, 2,15×2,05×1,9mm | R: 2,1V@15mA; G: 2,8V@8mA; B: 2,8V@5mA | LCSC C727904 — `item.szlcsc.com/775227.html` (fetch direto) |
| **Everlight HNB1921W-OS01** | Everlight | Ânodo comum | SMD 4-J-Lead, mesmas dimensões | R: 2,1V@15mA; G/B: 2,9V | ⚠️ Verificação indireta — PDF retornou 404; confirmar manualmente |

---

## 10. Capacidades de fabricação JLCPCB (4 camadas) e montagem SMT

🔴 **NÃO VERIFICADO.** A tentativa de `web_fetch` em `https://jlcpcb.com/capabilities/pcb-capabilities` falhou com erro de transporte (DNS/TLS) nesta sessão, assim como todas as demais tentativas de acessar `jlcpcb.com` ao longo da pesquisa (comum a todos os agentes paralelos). **Nenhum valor de trilha/espaço mínimos, drill mínimo, anel mínimo, espessura de placa, controle de impedância ou peso de cobre é reportado aqui** — recomenda-se consulta manual direta a `jlcpcb.com/capabilities/pcb-capabilities` e `jlcpcb.com/smt-assembly` antes de fechar as regras de projeto (design rules) do PCB.

---

## Tabela consolidada de fontes (mínimo cobertas — acesso em 22/10/2026)

| # | Título do documento/página | URL | Data de acesso |
|---|---|---|---|
| 1 | STM32H723VE/VG/ZE/ZG Datasheet (DS13313 Rev.4) | st.com/resource/en/datasheet/stm32h723vg.pdf | 22/10/2026 |
| 2 | STM32H725xE/G Datasheet (DS13311 Rev.5) | st.com/resource/en/datasheet/stm32h725vg.pdf | 22/10/2026 |
| 3 | RM0468 Reference Manual | st.com/resource/en/reference_manual/rm0468-... | 22/10/2026 |
| 4 | STM32H723ZGT6 product page | st.com/en/microcontrollers-microprocessors/stm32h723zg.html | 22/10/2026 |
| 5 | STM32H725VGT6 product page | st.com/en/microcontrollers-microprocessors/stm32h725vg.html | 22/10/2026 |
| 6 | ST Community — PC2_C/PC3_C | community.st.com/.../stm32h723-ulpi-and-pc2-c-pc3-c-161159 | 22/10/2026 |
| 7 | ST Community — pinout H723 vs Nucleo-144 | community.st.com/.../pin-out-of-stm32h723-vs-stm32h7-nucleo-144-boards-150456 | 22/10/2026 |
| 8 | STM32_open_pin_data (GitHub oficial ST) | github.com/STMicroelectronics/STM32_open_pin_data | 22/10/2026 |
| 9 | TCAN1044-Q1 Datasheet (SLLSF17D) | ti.com/lit/ds/symlink/tcan1044-q1.pdf | 22/10/2026 |
| 10 | TCAN1042-Q1 Datasheet (SLLSES9D) | ti.com/lit/ds/symlink/tcan1042-q1.pdf | 22/10/2026 |
| 11 | TJA1042 Datasheet (Rev.11) | nxp.com/docs/en/data-sheet/TJA1042.pdf | 22/10/2026 |
| 12 | TJA1051 Datasheet (Rev.9) | nxp.com/docs/en/data-sheet/TJA1051.pdf | 22/10/2026 |
| 13 | TJA1463 Datasheet (Rev.3.0) | nxp.com/docs/en/data-sheet/TJA1463.pdf | 22/10/2026 |
| 14 | MCP2561/2FD Datasheet (DS20005284B) | ww1.microchip.com/.../MCP2561-2FD-...-20005284.pdf | 22/10/2026 |
| 15 | PESD2CAN Datasheet | assets.nexperia.com/documents/data-sheet/PESD2CAN.pdf (via espelho datasheet4u.com) | 22/10/2026 |
| 16 | PESD2CANFD27V-T Datasheet | assets.nexperia.com/documents/data-sheet/PESD2CANFD27V-T.pdf (via espelho datasheet4u.com) | 22/10/2026 |
| 17 | ESDCAN24-2BLY Datasheet | st.com/resource/en/datasheet/esdcan24-2bly.pdf (via espelho datasheet4u.com) | 22/10/2026 |
| 18 | Vishay SMAJ series Datasheet (Doc.88390) | vishay.com/docs/88390/smaj50a.pdf | 22/10/2026 |
| 19 | Vishay SMBJ series Datasheet (Doc.88392) | vishay.com/docs/88392/smbj.pdf | 22/10/2026 |
| 20 | Littelfuse SMAJ/SMBJ Datasheets | littelfuse.com (via web.archive.org) | 22/10/2026 |
| 21 | TI App Brief SNOAAA1 — Load Dump Protection | ti.com/lit/an/snoaaa1/snoaaa1.pdf | 22/10/2026 |
| 22 | Vishay AN87003 — Load Dump TVS for 24V Powertrains | vishay.com/docs/87003/vishayloaddumptvsseriesfor24vpowertrains.pdf | 22/10/2026 |
| 23 | LM74700-Q1 Datasheet/página produto | ti.com/product/LM74700-Q1 ; ti.com/lit/ds/symlink/lm74700-q1.pdf | 22/10/2026 |
| 24 | DMP4065S Datasheet | diodes.com/assets/Datasheets/DMP4065S.pdf | 22/10/2026 |
| 25 | BAS40W Datasheet + PCN EOL | diodes.com/part/view/BAS40W ; diodes.com/assets/PCN-Files/Diodes_PCN_2623_Rev1_EOL.pdf | 22/10/2026 |
| 26 | TPS5450 Datasheet (SLVS757E) | ti.com/lit/ds/symlink/tps5450.pdf | 22/10/2026 |
| 27 | TPS54540-Q1 Datasheet (SLVSC56B) | ti.com/lit/ds/symlink/tps54540-q1.pdf | 22/10/2026 |
| 28 | LMR33630-Q1 Datasheet (SNVSB26C) | ti.com/lit/ds/symlink/lmr33630-q1.pdf | 22/10/2026 |
| 29 | TPS5430-Q1 Datasheet (SLVS751F) | ti.com/lit/ds/symlink/tps5430-q1.pdf | 22/10/2026 |
| 30 | XL1509 Datasheet (Rev 2.6) | xlsemi.com/datasheet/XL1509-EN.pdf | 22/10/2026 |
| 31 | TPS562201 Datasheet (SLVSD91D) | ti.com/lit/ds/symlink/tps562201.pdf | 22/10/2026 |
| 32 | AP63203/AP63203Q Datasheets | diodes.com/datasheet/download/AP63200-AP63201-AP63203-AP63205.pdf ; .../AP63200Q+.../pdf | 22/10/2026 |
| 33 | TLV62569 Datasheet (SLVSDG1C) | ti.com/lit/ds/symlink/tlv62569.pdf | 22/10/2026 |
| 34 | B320AE Datasheet | diodes.com/datasheet/download/B320AE.pdf | 22/10/2026 |
| 35 | MBRS340T3 Datasheet | onsemi.com/pdf/datasheet/mbrs340t3-d.pdf | 22/10/2026 |
| 36 | AP22815/AP22615 Datasheet (DS41022) | diodes.com/datasheet/download/AP22815_615.pdf | 22/10/2026 |
| 37 | TPS2051/TPS2051B/TPS2051C Datasheets | ti.com/lit/ds/symlink/tps2051.pdf ; tps2051b.pdf ; tps2051c.pdf | 22/10/2026 |
| 38 | TYPE-C-31-M-04 Datasheet (LCSC C129018) | atta.szlcsc.com/upload/public/pdf/source/20210810/...WJ26275.PDF | 22/10/2026 |
| 39 | GCT USB4105 Datasheet | gct.co/files/drawings/usb4105.pdf | 22/10/2026 |
| 40 | TYPE-C-31-M-12 Datasheet (LCSC C165948) | atta.szlcsc.com/upload/public/pdf/source/20220525/...WJ310728.PDF | 22/10/2026 |
| 41 | 10.0QHHTZB6.3 Datasheet (LCSC C668591) | atta.szlcsc.com/upload/public/pdf/source/20200618/...WJ323165.PDF | 22/10/2026 |
| 42 | ECS-250-10-33-JGN-TR produto DigiKey + ECX-32 Datasheet | digikey.com/.../ECS-250-10-33-JGN-TR/15777834 ; ecsxtal.com/store/pdf/ecx-32.pdf | 22/10/2026 |
| 43 | X322525MOB4SI Datasheet (LCSC C9006) | atta.szlcsc.com/upload/public/pdf/source/20250928/...YSX321SL.PDF | 22/10/2026 |
| 44 | FM-B1921RGBA-SH Datasheet (LCSC C727904) | item.szlcsc.com/775227.html | 22/10/2026 |
| 45 | Páginas DigiKey diversas (preço/estoque verificado diretamente) | digikey.com — PESD2CAN, PESD2CANFD27V-TR, B320AE, BAS70H, MBRS340T3G, TPS562201, TLV62569, XL1509-3.3, MCP2562FDT-H/SN, ECS-250-10-33-JGN-TR | 22/10/2026 |
| 46 | LCSC/szlcsc páginas diversas (preço/estoque verificado diretamente) | item.szlcsc.com — STM32H723VGT6, STM32H725VGT6, FM-B1921RGBA-SH | 22/10/2026 |

---

## Resumo executivo de itens NÃO VERIFICADO (checklist para validação manual antes de congelar o BOM)

1. **Preço/estoque em Mouser** — não verificado para **nenhum** componente nesta pesquisa (bloqueio total de rede).
2. **Preço/estoque e Basic/Extended em JLCPCB** — não verificado diretamente para nenhum componente (jlcpcb.com inacessível em todas as tentativas, incluindo a página de capacidades de fabricação).
3. **SYSCFG_PKGR código PKG[3:0] para LQFP100** (RM0468).
4. **Decoupling exato VDD/VDDA/VREF+/VBAT** do STM32H723 (apenas estimativa de boas práticas).
5. **"HY12P03C2"** — não confirmado como componente real de fabricante rastreável.
6. **Pinout exato CANH/CANL/GND** dos três TVS de CAN (PESD2CAN, PESD2CANFD27V-T, ESDCAN24-2BLY).
7. **Escopo textual exato dos pulsos ISO 7637-2 2a/3a/3b** (não localizado em fonte primária aberta).
8. **AEC-Q101 da peça BAS40WS** e fabricante exato confirmado.
9. **Id contínuo exato do DMP4065S-7** (conflito 2,4A vs 3,4A entre fontes).
10. **Especificações do Samtec FTSH-105-01-L-DV-K** e TSW-105 (fetch bloqueado em todas as tentativas).
11. **Molex 67643-2910 e Amphenol 87520-0010BLF** — dados por verificação indireta apenas.
12. **Capacidades de fabricação JLCPCB** (trilha/espaço mínimos, drill, anel, impedância, espessura, cobre) — página inacessível, nenhum dado reportado.

**Achados críticos de correção de premissas do pedido original**, a destacar no projeto:
- DS13311 ≠ datasheet do STM32H723 (é do H725); o correto é **DS13313**.
- "TYPE-C-31-M-04" é de **24 pinos**, não 16 — usar **TYPE-C-31-M-12** ou **GCT USB4105** para 16 pinos.
- "10.0QHHTZB6.3" é **SMD**, não through-hole — usar Molex 67643-2910 para THT real.
- Yangxing X322525MOB4SI é **12 pF**, não 10 pF — usar ECS-250-10-33-JGN-TR para 10 pF confirmado.
- "ECS-250-10-33-TR" (sem sufixo) não existe como SKU comercial.
- TCAN1042VDRQ1 (sem sufixo "G") suporta só **2 Mbps** em CAN-FD, não 5/8 Mbps.
- BAS40WS não é um zener nem é produto tier-1 ativo (BAS40W está EOL).
- AP22615AWU-7 é **TSOT26 de 6 pinos**, não SOT23-5, e não é pino-compatível com TPS2051B/C.
