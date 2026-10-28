# Hybrid Panda - BOM com MPN reais (v1) - RELATORIO PARCIAL

Data: 2026-10-27. Projeto: 04_PROJECT\HybridPanda\HybridPanda.kicad_sch (STM32H725ZGT6, 4x TJA1042TK/3).
Arquivos gerados (apenas novos, nada rastreado foi alterado):

- BOM_HYBRIDPANDA_v1.csv - BOM completa (48 linhas, 114 componentes - bate com 06_REPORTS\hybrid_BOM.csv).
- BOM_JLCPCB.csv - formato JLCPCB (Comment, Designator, Footprint, LCSC Part #).
- BOM_REPORT.md - este relatorio.

**STATUS: PARCIAL.** Toda a parte LCSC/JLCPCB (numero LCSC, estoque, Basic/Extended, preco @10, datasheet)
foi obtida de base de dados real. A coluna Mouser/Digi-Key tem SKU e preco verificados apenas para
AP22615AWU-7, TPS5450DDAR e STM32H725ZGT6; para as demais linhas esta registrado "by MPN (SKU nao verificado)".
Ver secao 8 (pendencias).

## 1. Metodo

1. Netlist exportada com kicad-cli (formato kicadxml) e cruzada com hybrid_BOM.csv -> cada passivo recebeu
   rede e classe de tensao (12V_Protected / +5V / USB_PWR / +3V3 / VDDA / internos do MCU).
2. Para cada linha: escolha do MPN com pacote igual ao footprint da placa, margem de tensao (>=2x para MLCC
   em 12V), classe X7R/X5R, tolerancia conforme valor; preferencia por itens JLC "Basic" ou "Extended preferred".
3. Pecas herdadas do BlackPanda: os LCSC originais foram lidos diretamente do projeto KiCad original
   (C:\Users\costabr\Downloads\BlackPandaH7\OpenpilotHardware\BlackPanda\kicad_project\BlackPanda.kicad_sch,
   campos LCSC/JLCPCB): U3=C668591, U5=C727904, L3=C149588, P1=C129018; L4 identificado pelo modelo 3D
   (Sunlord MWSA1004 -> MWSA1004S-150MT).
4. Nenhum MPN foi inventado: todos existem na base JLC (abaixo) ou foram confirmados via Octopart / web search.

## 2. Fontes

- Base JLCPCB/LCSC: yaqwsx.github.io/jlcparts (dump oficial do catalogo JLCPCB, data 2026-10-27, tabela
  jlc_components: estoque, Basic/Extended/preferred, precos por faixa, URL do datasheet). Estoques e precos
  na BOM sao dessa data.
- Octopart (octopart.com/search) para Mouser/Digi-Key/Arrow/Newark/TME: funcionou para AP22615AWU-7 e
  TPS5450DDAR; depois o acesso foi bloqueado pelo proxy corporativo (HTTP 407/403).
- Web search (Bing) para STM32H725ZGT6 (Mouser 511-STM32H725ZGT6 / DK 497-STM32H725ZGT6-ND) e para as
  dimensoes do pacote NXP SOT782-1 (EP 2.40 x 1.60 mm nominal).
- Acesso direto a lcsc.com, jlcpcb.com, mouser.com, digikey.com, ti.com, diodes.com: bloqueado no ambiente
  (TLS reset / proxy). Por isso as URLs de datasheet das pecas LCSC apontam para o espelho JLCPCB
  (jlcpcb.com/api/file/downloadByFileSystemAccessId/...), que e o mesmo PDF mostrado na pagina do produto.

## 3. Resumo

- Linhas da BOM: 48. Resolvidas com LCSC em estoque: 47. Nao resolvidas na JLC: 1 (U1 AP22615AWU-7).
- Linhas Basic (sem taxa de extended): 22 (todas as MLCC exceto 47uF/2.2uF-12V/10uF-0402, resistores 1K/10K/
  22R/100R, FB1, Y1). Extended: 25. Extended "preferred" (sem taxa): R27.
- Substituicoes por indisponibilidade (drop-in, mesmo footprint): D11 B320AE-13 -> B340A-13-F;
  D12 SM540C -> B540C-13-F.
- Custo JLC estimado por placa (precos @10, 47 linhas, sem U1): USD 26.93. Para 5 placas: ~USD 135 em
  componentes + U1 (Mouser USD 0.45 x5) + taxas JLC de extended (~USD 3/linha x 25 = ~USD 75, estimativa
  da tabela publica da JLC, nao cotada) + PCB + montagem. MCU responde por USD 15.74/placa.

## 4. Racional por linha (itens nao triviais)

| Ref | Escolha | Por que |
|---|---|---|
| U7 STM32H725ZGT6 | C730156, 132 pcs, USD 15.74 | Unico com estoque. Sufixo 6 = -40..85C; o grau "3" (-40..105C) nao foi encontrado em estoque em nenhuma fonte. Alternativas pin-compativeis: H723ZGT6 (C730146, 73 pcs, sem crypto - panda nao usa), H735ZGT6 (2 pcs), H725ZET6 (0 pcs, 512 kB -> layout de flash do firmware muda). Mouser 511-STM32H725ZGT6 sem estoque (USD 9.75@10, backorder); DK 497-STM32H725ZGT6-ND sem estoque (web search, nao confirmado ao vivo). |
| U8-U11 TJA1042TK/3/1J | C131480, 14645 pcs, USD 0.73, AEC-Q100 | Versao /3 (VIO) obrigatoria para MCU 3V3. Footprint da placa DFN-8 3x3 P0.65 EP 1.55x2.4; HVSON8 SOT782-1 tem EP nominal 1.60x2.40 -> compativel. Alternativa TJA1051TK/3 (C124020) mesmo pacote/pinagem (pino 8 = S em vez de STB, funcionalmente igual para o firmware panda). MCP2562FDT-E/MF (C623222, USD 5.67) pinagem NAO verificada -> nao listar como drop-in. |
| U6 TPS5450DDAR | C114425, 32560 pcs, USD 1.86 | Original. Vin max 36V cobre o clamp da TVS (26V). AEC: TPS5450QDDARQ1 C181270 (753 pcs, USD 3.26). Mouser 595-TPS5450DDAR (26 pcs, USD 7.28@10), DK 296-26997-1-ND (10255 pcs, USD 7.71@10). |
| U12 XL1509-3.3E1 | C74193, 34166 pcs, USD 0.30 | Original. Footprint da placa e PSOP-8 com pad exposto; XL1509 e SOP-8 simples -> pad central fica sem uso (herdado do BlackPanda, funciona). Nao ha fonte Mouser/DK para XLSEMI; nao ha substituto pin-compativel ocidental verificado. |
| U1 AP22615AWU-7 | NAO disponivel na JLC (C2680357 removido) | Mouser 621-AP22615AWU-7: 209 pcs, USD 0.446@10 (Octopart 2026-10-27); Arrow 51000; Newark 5849. Substituto JLC: TPS2553DBVR C55266 (54233 pcs, USD 0.45), SOT-23-6 com pinagem identica (1 OUT, 2 GND, 3 FAULT, 4 EN, 5 ILIM, 6 IN), EN ativo alto como o AP22615AWU. POREM a resistencia de ILIM muda: TPS2553 usa 15k..232k; o R27=2.4k do AP22615 nao serve. Formula do AP22615 nao verificada (datasheet inacessivel). Decisao a tomar: consignar AP22615 ou trocar U1+R27. |
| Q4 HY12P03C2 | C358006, 2741 pcs, USD 0.24 | -30V, 16 mOhm @4.5V, 50A, -55..150C, PowerPAK SO-8 (PPAK 5x6). Alternativa mesmo footprint: AON6407 C13899 (-30V, 8171 pcs). Si7141DP (sugerido no datasheet da BOM original) e -20V -> NAO atende Vds >= -30V. AO4407A e SOIC-8 sem pad -> NAO compativel. |
| D1 SMAJ16CA | Littelfuse C148217 (9805 pcs) | Footprint DIOM4325X250N = SMA. 16V standoff, 400W. Alternativa barata MDD C173493 (48970 pcs, USD 0.046). Para load dump ISO 7637 pulso 5 real, 400W e marginal (igual ao BlackPanda). |
| D5-D9 PESD2CAN,215 | C75176, 34023 pcs | Original. Para CAN-FD >2 Mbit/s considerar PESD2CANFD24V-TR (C552486), mesmo SOT-23. |
| D11 B340A-13-F | C85098 (subst. B320AE-13) | Mesmo SMA, 40V 3A. B320AE nao esta na JLC. |
| D12 B540C-13-F | C72264 (subst. SM540C) | Mesmo SMC, 40V 5A; e o diodo recomendado pela TI para o TPS5450. |
| L4 MWSA1004S-150MT | C151872, 6391 pcs | 15uH 6.5A 45 mOhm blindado 11x10x4 - identificado pelo modelo 3D do projeto original (footprint L_10.5x11.5_H4.0). |
| L3 SMMS0650-470M | C149588 | Mesmo LCSC do original; 47uH 2A. |
| L5 DFE201610E-2R2M=P2 | C337891, 1351 pcs | Valor recomendado pela ST para o SMPS interno do H7. |
| Y1 X322525MOB4SI | C9006, Basic | CL=12pF, ESR 50 Ohm, +-10/20 ppm, -40..85C. Com C23/C24 = 15pF: CL_eff 9.5-11.5 pF (ligeiro pull para cima, aceitavel). |
| SW1 SKQGAFE010 | C202424 | Footprint KiCad cita explicitamente SKQGAFE010. |
| FB1 GZ1608D601TF | C1002, Basic | 600R@100MHz, 200 mA; VDDA consome < 20 mA. |
| 47uF 0805 (x8) | Fenghua 0805X476M100NT 10V X5R, C178332 | Nenhum 47uF esta em 12V (6 em +5V, 1 em +3V3, 1 em USB_PWR). Em 5V um 10V X5R 0805 derata para ~20-25uF; aceitavel para o filtro de saida do TPS5450 (6 em paralelo). Basic 6.3V (C16780) derata mais. Capacitancia nominal exige 1206 (C96123, Basic, 10V) -> impacto de footprint. |
| 2.2uF 0805 (x4) | Yageo CC0805KKX7R9BB225 50V X7R, C125847 | Unicos capacitores em 12V_Protected. 50V >= 2x o clamp de 26V. Alternativa Basic 50V X5R C377773. |
| 10uF 0402 C8 | CL05A106MP5NUNC 10V, C315248 | Em +5V; so existe em 6.3/10V, derating forte (~3-5uF). Funcao local de decoupling, redundante com 6x47uF. |
| 100nF 0402 (x31) | CL05B104KB54PNC 50V X7R, Basic, C307331 | Item unico para 3V3/5V/VDDA/NRST/USB_PWR. |
| R6 3.16k 1% | 0603WAF3161T5E C22993 | Esta em footprint de capacitor 0603 - solda fisicamente; JLC pode acusar mismatch. Com R5=10k da Vout = 1.221*(1+10/3.16) = 5.08 V. |
| R18 110R | Panasonic ERJ2RKF1100X C413064 (AEC-Q200) | Nao ha 110R Basic em 0402. |
| J1 SWD | Amphenol 20021121-00010C4LF C150517 (809 pcs) | Generico BOOMELE C59981 (5433 pcs, USD 0.14) e opcao; pode ser DNP. |

## 5. Tabela de impacto de footprint (NADA foi alterado na placa)

| Item | Situacao atual | Impacto / acao sugerida |
|---|---|---|
| C3,C10,C16-C21 47uF 0805 | Pecas 0805 10V so entregam ~50% em 5V | Opcional: mudar para 1206 (CL31A476MPHNNNE, Basic) para capacitancia nominal. Sem mudanca: funciona com derating. |
| C8 10uF 0402 | So 6.3/10V existem | Opcional: 0603 ou 0805 para capacitancia real. |
| R6 3.16k em Capacitor_SMD:C_0603 | Resistor 0603 em pad de capacitor 0603 | Compativel fisicamente; corrigir footprint para R_0603 na proxima revisao para evitar aviso DFM da JLC. |
| U1 AP22615AWU-7 -> TPS2553DBVR | Mesmo SOT-23-6 e pinagem | Sem impacto de footprint, mas R27 (2.4k) precisa ser recalculado para TPS2553 (faixa 15k..232k). |
| U12 XL1509 em Diodes_PSOP-8 | Footprint com pad exposto, peca sem pad | Sem impacto (herdado); pad central sem uso. |
| U8-U11 HVSON8 em DFN-8 EP 1.55x2.4 | EP real 1.60x2.40 nominal | Compativel (diferenca 0.05 mm). Dimensao obtida por web search, nao lida do PDF NXP diretamente. |
| Q4 alternativas | Si7141DP (-20V) / AO4407A (SOIC-8) | NAO usar; manter HY12P03C2 ou AON6407 (DFN 5x6). |

## 6. Disponibilidade fraca (estoque JLC em 2026-10-27)

1. U7 STM32H725ZGT6 - 132 pcs na JLC; Mouser/DK sem estoque. RISCO MAIOR. Alternativa H723ZGT6 (73 pcs).
2. U1 AP22615AWU-7 - 0 na JLC; Mouser 209 pcs. Precisa consignacao ou troca por TPS2553DBVR (+R27).
3. Q1,Q2 DDTA143ECA-7-F - 187 pcs (alternativa DDTA143ECA-TP C52205286, 2552 pcs).
4. J1 20021121-00010C4LF - 809 pcs (alternativa generica C59981).
5. D2 BAS40WS - 984 pcs (alternativa BORN C7461123, 4284 pcs).
6. L5 DFE201610E-2R2M=P2 - 1351 pcs.
7. P1 TYPE-C-31-M-04 - 1956 pcs (alternativa -04A, 458 pcs).
8. Q4 HY12P03C2 - 2741 pcs (alternativa AON6407, 8171 pcs).

Para 2-5 prototipos (max. 5 pcs de cada, 20 pcs de TJA1042) todos os estoques acima sao suficientes hoje.

## 7. Temperatura

- -40..85C: MCU (grau 6), TJA1042 (-40..150), TPS5450, XL1509, YXC cristal, SKQGAFE010 (-40..90), MLCC X7R/X5R.
- -30..85C (abaixo do desejado): P1 TYPE-C-31-M-04, U5 FM-B1921RGBA-SH, U3 USB-A SHOU HAN (nao informado).
- -40..105C sob painel: nao atendido pelo MCU em estoque (grau 3 indisponivel). Nenhuma peca AEC-Q100
  completa foi escolhida como primaria por custo; marcadas na coluna AEC as que sao (TJA1042, PESD2CAN,
  BAS70H, BAT54S, PDTC114EU, ERJ2RKF1100X) e a alternativa TPS5450QDDARQ1.

## 8. O que NAO foi verificado / pendencias (estado parcial)

1. SKUs e estoque Mouser/Digi-Key de todas as linhas exceto AP22615AWU-7, TPS5450DDAR e STM32H725ZGT6
   (Octopart foi bloqueado pelo proxy a meio da coleta). Na BOM esta "by MPN (SKU nao verificado)" -
   os MPN listados sao de fabricantes vendidos por Mouser/DK (Samsung, Yageo, Murata, Nexperia, Diodes, TI,
   Panasonic, Alps, Amphenol); XLSEMI, HUAYI, Hroparts, NationStar, SHOU HAN, Sunlord, SXN, Fenghua, Uniroyal,
   YXC nao sao vendidos por Mouser/DK - para estes a alternativa ocidental e apenas funcional/footprint a conferir.
2. Formula de ILIM do AP22615 e valor equivalente de R27 para TPS2553 (datasheets Diodes/TI inacessiveis).
3. Pinagem do MCP2562FD-E/MF vs TJA1042TK/3 (nao listado como drop-in).
4. Dimensao do EP do SOT782-1 lida via web search (NXP SOT782-1.pdf nao pode ser aberto no ambiente).
5. Estoque/preco Mouser/DK do STM32H725ZGT6 vem de web search (nao confirmado na pagina ao vivo).
6. Taxa de extended da JLC e custo de montagem: nao cotados.
7. Precos "@10" sao da base jlcparts (faixa que inclui 10 pcs); para extended a JLC cobra multiplo de reel/attrition.
8. Classificacao AEC marcada apenas quando constava na base JLC/datasheet; nao auditada peca a peca.
9. Rede exata de R5 (10k 1%) assumida como divisor superior do TPS5450 (par com R6 3.16k) - conferir no esquematico.

## 9. Resumo de retorno

- Linhas resolvidas com LCSC em estoque: 47/48. Nao resolvida na JLC: 1 (U1 AP22615AWU-7, disponivel Mouser).
- Itens com impacto de footprint: 47uF 0805 (opcional 1206), C8 10uF 0402 (opcional), R6 em pad de capacitor,
  U1 substituto exige novo R27. Nenhuma alteracao na placa foi feita.
- Top riscos de disponibilidade: STM32H725ZGT6 (132 pcs JLC, 0 Mouser/DK), AP22615AWU-7 (0 JLC),
  DDTA143ECA-7-F (187 pcs), J1 Amphenol (809 pcs), BAS40WS (984 pcs).


## 10. Passo 4 da campanha de correcoes (2026-10-28) - delta da BOM apos passos 1-3

Script: 05_SCRIPTS\corr_step4_bom.py (edita BOM_HYBRIDPANDA_v1.csv, regenera BOM_JLCPCB.csv, grava MPN/Manufacturer/LCSC
como propriedades ocultas nos simbolos do esquema e regenera 06_REPORTS\hybrid_BOM.csv com kicad-cli, agrupado por
Value,Footprint,MPN). Resultado: 53 linhas / 119 referencias; 118 com MPN (JP1 e jumper de solda, sem peca).

| Ref | Antes | Depois | LCSC | Status |
|-----|-------|--------|------|--------|
| R6 | 3.16k em footprint C_0603 | 3.16k em R_0603_1608Metric (passo 1) | C22993 | OK |
| C64 (novo) | - | 2.2uF 10V X5R 0402 CL05A225MP5NSNC (passo 2, VCAP U7.103) | C23733 | TO-VERIFY (numero por busca web) |
| C65 (novo) | - | 4.7uF 16V X5R 0603 CL10A475KO8NNNC (passo 2, VDDSMPS U7.16) | C19666 | OK (mesma linha de C60-C62) |
| JP1 (novo) | - | solder jumper HW_ID (passo 2) | - | NO-PART |
| R1 | 1k 0402 (linha R1,R2) | 10k R_0603 0603WAF1002T5E (passo 3 item 4) | C25804 | OK (Basic classico; confirmar estoque) |
| C4, C12 | 2.2uF 50V X7R 0805 (linha C4,C6,C7,C12) | 10uF 50V X5R 0805 CL21A106KBYQNNE (passo 3 item 6) | C2932476 | TO-VERIFY (numero por busca web) |
| D15 (novo) | - | BZT52C12 SOD-123 (passo 3 item 5) | C571379 | TO-VERIFY (numero por busca web) |
| U13 (novo) | - | USBLC6-2SC6 SOT-23-6 ST (passo 3 item 8) | C7519 | OK (confirmado lcsc.com) |
| D10 | datasheet onsemi MBR1020 (errado) | datasheet Nexperia BAS70H | C426766 | OK; funcao (item 9) deferida |

Nao alterados nesta rodada (decisao documentada em 06_REPORTS\CORRECOES_APLICADAS.md): 47uF 0805 mantidos com a peca 10V
(0805X476M100NT); C8 10uF 0402 mantido (troca para 0603 exige espaco no PCB); U1 AP22615AWU-7 mantido, TPS2553DBVR
(C55266) apenas como alternativa documentada (exige recalcular R27); C21 polimero 100uF (item 36) nao aplicado.
Os numeros LCSC marcados TO-VERIFY vieram de busca web (nao da base jlcparts) e devem ser confirmados antes de encomendar.
