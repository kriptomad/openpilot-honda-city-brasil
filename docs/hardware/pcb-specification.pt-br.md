# Hybrid Panda: especificacao de fabricacao da PCB

Estado: apenas projeto. **NAO FABRICAR.** Nenhuma placa foi encomendada, construida ou
testada. Este documento descreve o que os arquivos KiCad e o pacote de fabricacao gerado
especificam, nao o que um fabricante confirmou. Versao em ingles:
[pcb-specification.md](pcb-specification.md).

Fontes principais: `hardware/hybrid-panda/HybridPanda.kicad_pcb`, `HybridPanda.kicad_pro`,
`hardware/fabrication/readme.md`, `hardware/fabrication/drill_table.md`,
`hardware/fabrication/gerbers/HybridPanda-job.gbrjob`, `hardware/reports/hybrid_DRC_final.json`.
Os numeros marcados "extraido" foram obtidos por parsing dos arquivos S-expression do KiCad
para este documento.

## 1. Resumo da placa

| Item | Valor | Fonte |
|---|---|---|
| Projeto | `HybridPanda` (KiCad 10.0.7) | `.kicad_pro`, cabecalho do `.kicad_pcb` |
| Formato | Contorno da OpenBlackPanda v2 (black panda), inalterado exceto pelo degrau no conector USB-A | D-02, D-33 (`docs/decisions.md`) |
| Dimensao nominal | 50,625 mm x 46,75 mm | D-33; bounding box do Edge.Cuts extraido |
| Bounding box do Edge.Cuts (borda externa, traco 0,1 mm) | X 91,91 a 142,535 mm (142,935 mm para Y < 48,6 mm), Y 32,01 a 78,76 mm | extraido |
| Detalhe do contorno | Cantos arredondados; a borda leste tem um degrau de 0,4 mm para o receptaculo USB-A (`U3`) | extraido; D-33 |
| Camadas de cobre | 4 (F.Cu, In1.Cu, In2.Cu, B.Cu) | `(layers ...)` do `.kicad_pcb` |
| Espessura final | 1,59 mm (soma do stackup; `BoardThickness: 1.59` no job file) | stackup do `.kicad_pcb`; `HybridPanda-job.gbrjob` |
| Footprints | 125 (80 em F.Cu, 45 em B.Cu); 119 referencias do esquema + 6 fiduciais | extraido |
| Pads | 526 | extraido |
| Redes | 142 nomeadas no arquivo da PCB (62 redes reais, 80 redes `unconnected-*` de nao conexao) | extraido |
| Segmentos de trilha | 1218 (F.Cu 628, B.Cu 352, In1.Cu 152, In2.Cu 86) | extraido |
| Vias | 242 (203 x 0,6/0,3 mm, 39 x 0,7/0,3 mm), todas passantes, sem cegas/enterradas, sem via-in-pad | extraido; `fabrication/readme.md` item 9 |
| Componentes com furo passante | `P1` (receptaculo OBD-C, 12 PTH 0,4 mm + 4 rasgos + 2 NPTH 0,8 mm), `U3` (USB-A, 2 PTH 2,5 mm), vias termicas de `U6` (8 x PTH 0,3 mm) | `drill_table.md` |
| Zonas de cobre | 17: GND nas quatro camadas; +3V3 em In1.Cu; +5V em F/B/In1 (x2)/In2; +12V e 12V_Protected em B.Cu; USB_PWR em F.Cu; L4 (no de comutacao) em F.Cu; 6 areas keep-out | extraido |
| Fiduciais | 6 (`FID1`-`FID3` topo, `FID4`-`FID6` fundo), apenas na PCB, sem simbolo no esquema | extraido; `correcoes-aplicadas.md` |
| Painelizacao | Nenhuma (placa unica) | `fabrication/readme.md` |

A placa baseline OpenBlackPanda v2 (`archive/baseline-original/`) tem 2 camadas, 86
footprints, 838 segmentos e 156 vias (extraido); a Hybrid Panda e um novo layout do mesmo
contorno em 4 camadas (D-05).

## 2. Stackup

Definido na secao `(stackup ...)` do `HybridPanda.kicad_pcb` e repetido no
`HybridPanda-job.gbrjob`. Os valores foram escolhidos pelo projeto e **nao foram confirmados
com nenhum fabricante** (`fabrication/readme.md` item 1).

| # | Camada | Tipo | Espessura | Material / notas |
|---|---|---|---|---|
| 1 | F.SilkS | serigrafia | - | cor nao definida no arquivo |
| 2 | F.Paste | pasta | - | |
| 3 | F.Mask | mascara | 0,01 mm | cor nao definida no arquivo |
| 4 | F.Cu | cobre | 0,035 mm (1 oz) | sinais, componentes |
| 5 | dieletrico 1 | prepreg | 0,2 mm | FR4, er 4,5, tangente de perdas 0,02 |
| 6 | In1.Cu | cobre | 0,0175 mm (0,5 oz) | plano GND, plano +3V3 sob `U7`, par USB acoplado, alguma potencia |
| 7 | dieletrico 2 | core | 1,065 mm | FR4, er 4,5, tangente de perdas 0,02 |
| 8 | In2.Cu | cobre | 0,0175 mm (0,5 oz) | plano GND, +5V, poucos sinais |
| 9 | dieletrico 3 | prepreg | 0,2 mm | FR4, er 4,5, tangente de perdas 0,02 |
| 10 | B.Cu | cobre | 0,035 mm (1 oz) | componentes, potencia |
| 11 | B.Mask | mascara | 0,01 mm | |
| 12 | B.Paste | pasta | - | |
| 13 | B.SilkS | serigrafia | - | |

Total: 1,59 mm. `copper_finish` e `"None"` no arquivo e `"Finish": "None"` no job file;
`dielectric_constraints` e `no` (o arquivo nao solicita stackup com impedancia controlada).
A intencao e um stackup padrao de 4 camadas classe 1,6 mm em FR-4 com cobre "1 oz externo /
0,5 oz interno" (`fabrication/readme.md`, "Intended specification").

## 3. Acabamento, mascara e serigrafia

| Item | Valor nos arquivos | Recomendacao no repositorio |
|---|---|---|
| Acabamento de superficie | nao definido (`copper_finish "None"`) | ENIG recomendado por causa do LQFP-144 com passo 0,5 mm e dos encapsulamentos DFN/HVSON; HASL nao recomendado (`fabrication/readme.md`) |
| Cor da mascara | nao definida | verde sugerido (`fabrication/readme.md`) |
| Cor da serigrafia | nao definida | nao determinado (branco implicito pela convencao de mascara verde; nao consta no repositorio) |
| Cobertura da serigrafia | 52 referencias sem texto de serigrafia (herdado do baseline, cosmetico) | `docs/final-audit.md` |
| Bordas metalizadas / castelacoes | nenhuma | - |

## 4. Regras de projeto

Do `HybridPanda.kicad_pro` (`board.design_settings.rules`), mais as classes de rede. Sao os
valores contra os quais o DRC verificou; os valores mais apertados realmente usados na placa
estao na secao 5.

| Regra | Valor | Nota |
|---|---|---|
| Afastamento minimo (cobre a cobre) | 0,1 mm | |
| Largura minima de trilha | 0,127 mm | 5 mil |
| Diametro minimo de via | 0,4 mm | |
| Anel minimo de via | 0,125 mm | |
| Furo passante minimo | 0,3 mm | |
| Afastamento de furo | 0,25 mm | |
| Furo a furo | 0,25 mm | |
| Cobre a borda da placa | 0,2 mm | |
| Altura / espessura minima de texto | 0,8 mm / 0,08 mm | 45 avisos `text_height` herdados abaixo disso |
| Largura minima de conexao | nao definida (padrao do KiCad) | |

Classes de rede:

| Classe | Redes | Trilha | Via (diam./furo) | Par diferencial largura / gap |
|---|---|---|---|---|
| Default | todas as demais | 0,2 mm | 0,7 / 0,3 mm | 0,2 / 0,25 mm |
| CAN_DIFF | BUSx_H / BUSx_L | 0,25 mm | 0,7 / 0,3 mm | 0,25 / 0,2 mm |
| USB | USB_D+/-, USB_R_D+/- | 0,2 mm | 0,7 / 0,3 mm | 0,2 / 0,25 mm |

## 5. Valores usados na placa

| Parametro | Valor | Fonte |
|---|---|---|
| Menor largura de trilha presente | 0,14 mm | extraido (em segmentos de estreitamento; a maioria das trilhas de sinal tem 0,2 a 0,25 mm) |
| Menor afastamento de cobre presente | DRC passa a 0,1 mm; 0 violacoes `clearance` | `hybrid_DRC_final.json` |
| Menor furo | 0,300 mm (vias e vias termicas de `U6`) | `drill_table.md` |
| Tamanhos de via usados | 0,6/0,3 mm (203), 0,7/0,3 mm (39) | extraido |
| Anel minimo | PTH 0,125 mm, via 0,150 mm | `drill_table.md` |
| Quantidade de furos | 270 (PTH 26, NPTH 2, via 242) | `drill_table.md`, `gerber_check.json` (Excellon vs PCB 270 vs 270) |
| Rasgos | 4 (1,199 a 1,2 mm de largura, carcaca de `P1`) | `drill_table.md` |
| Maiores furos | PTH 2,5 mm x2 (`U3`), NPTH 0,8 mm x2 (`P1`) | `drill_table.md` |
| Menor passo SMD | 0,5 mm (`U7` LQFP-144, `U8`-`U11` HVSON-8) | footprints |
| Menores passivos | 0402 (39 capacitores, 22 resistores) | contagem de footprints extraida |

## 6. Requisitos de impedancia

O projeto define alvos, mas **nenhuma impedancia foi simulada ou confirmada**; o DRC do KiCad
nao verifica impedancia (`fabrication/readme.md` item 1).

| Par | Alvo | Camada / geometria na placa | Estimativa analitica no repositorio | Estado |
|---|---|---|---|---|
| CAN BUSx_H/L (4 pares) | 120 ohm diferencial (nominal do barramento) | microstrip em F.Cu / B.Cu, largura 0,25 mm, gap 0,2 mm sobre prepreg de 0,2 mm para GND | faixa de 108 a 143 ohm reportada por `step6_reports.py` | nao confirmado; trilhas curtas entre transceptor e `P1`, a terminacao fica no chicote do veiculo, nao na placa |
| USB_R_D+/D- (full speed) | 90 ohm diferencial | par acoplado em In1.Cu, largura 0,2 mm, gap 0,3 mm, uma camada ate `U13` (`correcoes-aplicadas.md` item 19) | nao recalculada apos o reroteamento | nao confirmado; USB FS a 12 Mbit/s e tolerante, mas nada foi medido |

Nota: o item 2 de `fabrication/readme.md` ainda afirma que USB_D+/- foi roteado pelo
Freerouting com vias e nao como par acoplado. Esse texto e anterior ao item 19 da auditoria
SI/PI, que reroteou `USB_R_D+/D-` como par acoplado em In1.Cu. Os trechos do lado do MCU
`USB_D+/-` (entre `U7` e os resistores serie de 22 ohm `R20`/`R21`) permanecem como foram
roteados. Nao foi possivel determinar pelo repositorio se os gerbers em
`hardware/fabrication/` refletem a placa posterior ao item 19 (ambos foram importados no
mesmo commit); regenerar o pacote antes de qualquer pedido.

## 7. Resumo do resultado do DRC

Ferramenta: kicad-cli 10.0.7, todas as severidades, `hardware/reports/hybrid_DRC_final.json`
(2026-10-28T10:16:47).

| Categoria | Quantidade | Natureza |
|---|---|---|
| Itens nao conectados | 0 | |
| Paridade com o esquema | 0 | |
| `clearance`, `shorting_items`, `courtyards_overlap`, `copper_edge_clearance`, `starved_thermal`, `drill_out_of_range`, `footprint_type_mismatch`, `track_width`, `via_dangling` | 0 | as quatro ultimas categorias existiam no baseline/placas intermediarias e foram eliminadas pelos scripts de correcao |
| `lib_footprint_mismatch` | 73 | footprints na placa diferem das copias da biblioteca (edicoes locais, versoes de biblioteca do KiCad 10); informativo |
| `text_height` | 45 | texto de serigrafia abaixo de 0,8 mm, herdado do baseline (baseline tinha 82) |
| `hole_clearance` | 8 | herdado do baseline (8/8); em torno dos furos de fixacao de `P1` / `U3` |
| `silk_edge_clearance` | 4 | herdado (4/4) |
| `silk_overlap` | 4 | baseline 3 |
| `silk_over_copper` | 1 | baseline 0; cosmetico |
| **Total** | **135** | reduzido de 182 antes das correcoes SI/PI (`correcoes-aplicadas.md`) |

Todos os 135 itens restantes sao cosmeticos ou de controle de biblioteca; nenhum e violacao
eletrica. Foram deliberadamente deixados (D-37, "deferidos"). Recomenda-se nova execucao do
DRC com a placa final e serigrafia atualizada antes de qualquer pedido.

## 8. Arquivos de fabricacao

Diretorio `hardware/fabrication/`, gerado em 2026-10-28 10:19:21 por
`hardware/scripts/step8_fabricate.py` com `kicad-cli` do KiCad 10.0.7.

### 8.1 Gerbers (`gerbers/`, RS-274X, extensoes Protel, sem atributos X2)

| Arquivo | Camada |
|---|---|
| `HybridPanda-F_Cu.gtl` | cobre superior |
| `HybridPanda-In1_Cu.g1` | interna 1 |
| `HybridPanda-In2_Cu.g2` | interna 2 |
| `HybridPanda-B_Cu.gbl` | cobre inferior |
| `HybridPanda-F_Mask.gts` / `HybridPanda-B_Mask.gbs` | mascara de solda |
| `HybridPanda-F_Paste.gtp` / `HybridPanda-B_Paste.gbp` | estencil |
| `HybridPanda-F_Silkscreen.gto` / `HybridPanda-B_Silkscreen.gbo` | legenda |
| `HybridPanda-Edge_Cuts.gm1` | contorno |
| `HybridPanda-job.gbrjob` | job file (stackup, espessura 1,59, acabamento None) |

### 8.2 Furacao (`drill/`)

Excellon, mm, 3:3, supressao de zeros a esquerda: `HybridPanda-PTH.drl`,
`HybridPanda-NPTH.drl`, mapa de furacao em Gerber X2 (`.gbr`) e PDF para cada um.

### 8.3 Montagem (`assembly/`)

| Arquivo | Conteudo |
|---|---|
| `BOM_JLC.csv` | BOM no formato JLCPCB (Comment, Designator, Footprint, LCSC) |
| `CPL_JLC.csv` | posicionamento no formato JLCPCB (Designator, Mid X/Y, Layer, Rotation); origem = origem de furacao/auxiliar 0,00, 0,00 mm; **rotacoes nao normalizadas para a convencao JLC** |
| `pos_kicad_both.csv` | arquivo de posicao nativo do KiCad, ambos os lados |

### 8.4 Outros

| Arquivo | Conteudo |
|---|---|
| `pdf/` | esquema, cobre por camada (F, In1, In2, B), desenho de fabricacao topo/fundo, desenho de montagem topo/fundo |
| `3d/HybridPanda.step` | exportacao STEP (28,2 MB; modelos apenas VRML omitidos, portanto alguns corpos 3D faltam) |
| `drill_table.md`, `drill_table.json` | tabela de furos |
| `gerber_check.json` | apenas verificacao sintatica de gerber/Excellon; nenhuma verificacao em visualizador foi feita |
| `HybridPanda_gerbers_JLC.zip` | 16 entradas: os 11 gerbers, o job file, os arquivos de furacao PTH e NPTH e os 2 PDFs de mapa de furacao; preparado para upload mas **nao deve ser enviado** ate que os bloqueios abaixo sejam resolvidos |

## 9. Notas de montagem

- SMD nos dois lados: 80 footprints no topo (inclui `U7`, os quatro transceptores, `U6`,
  `U12`, `U1`, `P1`, `U3`, `J1`, `SW1`, `U5`), 45 no fundo (principalmente desacoplamento
  0402 sob `U7`, `JP1`, fiduciais `FID4`-`FID6`). O lado exato por referencia esta em
  `docs/hardware/bom.csv` (coluna `side`).
- Furo passante / misto: `P1` (receptaculo OBD-C, pads de sinal SMD mais carcaca THT), `U3`
  (USB-A, carcaca THT), ambos no topo. `U6` tem 8 vias termicas sob o pad exposto.
- Fiduciais: 3 por lado (cobre de 1 mm, abertura de mascara de 2 mm, footprints de fiducial
  padrao do KiCad).
- Camadas de pasta exportadas para os dois lados; a espessura do estencil nao esta
  especificada no repositorio (nao determinado).
- Painelizacao: nao feita; sem trilhos, furos de ferramenta ou V-cut.
- O espacamento minimo de courtyard dentro do bloco dos transceptores CAN e inferior a 1 mm
  (D-37, deferido); aceitavel para montagem automatica, apertado para retrabalho.
- `U1` (AP22615AWU-7) nao e estocado pela JLCPCB; a alternativa TPS2553DBVR (C55266) exige
  outro valor de `R27` (`hardware/reports/bom-real/bom-report.md`).
- Varios codigos LCSC estao marcados "a verificar"; ver [bom.pt-br.md](bom.pt-br.md).
  Nenhum codigo LCSC foi confirmado no catalogo.

## 10. Estado e itens deferidos

**NAO FABRICAR.** O pacote existe para arquivo e revisao. Os motivos de bloqueio, conforme
`hardware/fabrication/readme.md` e `docs/decisions.md` D-37:

1. Impedancia (CAN 120 ohm, USB 90 ohm) apenas estimada analiticamente; stackup nao
   acordado com um fabricante.
2. Zero validacao fisica: nenhuma placa construida, montada ou medida; o firmware da red
   panda nunca rodou neste hardware.
3. BOM: 1 referencia sem MPN (`JP1`), 2 sem LCSC (`JP1`, `U1`); codigos LCSC "a verificar"
   nao confirmados; `U1` indisponivel na JLC.
4. 135 itens de DRC herdados (cosmeticos) nao resolvidos; serigrafia incompleta (52 refs).
5. Gerbers nao revisados em visualizador (apenas verificacao sintatica).
6. Rotacoes do CPL nao normalizadas.
7. Possivel divergencia entre a exportacao de fabricacao e a placa final (ver nota da
   secao 6); nova exportacao necessaria.
8. Itens SI/PI deferidos (`correcoes-aplicadas.md`: 9, 10, 16, 21/22/23, 25, 27, 29, 34,
   36), troca de encapsulamento de `C8`, alternativa para `U1`, espacamento de courtyard e
   um novo gabinete (o degrau na borda do USB-A e os componentes mais altos nao foram
   verificados contra a caixa original da black panda).

Nada neste documento deve ser lido como afirmacao de que a placa e fabricavel como esta.

## 11. Referencias

- `hardware/hybrid-panda/HybridPanda.kicad_pcb`, `HybridPanda.kicad_pro`.
- `hardware/fabrication/readme.md`, `drill_table.md`, `gerber_check.json`,
  `gerbers/HybridPanda-job.gbrjob`.
- `hardware/reports/hybrid_DRC_final.json`, `hardware/reports/final_audit.json`,
  `hardware/reports/correcoes-aplicadas.md`, `hardware/reports/si-pi-audit/si-pi-audit.md`.
- `hardware/research/step5-layout-h725.md` (layout e Freerouting),
  `step6-roteamento-impedancia.md` (estimativa de impedancia), `step7-validacao.md`,
  `step9-bringup-e-teste-veiculo.md` (bring-up planejado, nao executado).
- `docs/decisions.md` D-02, D-05, D-33, D-37.
- `docs/final-audit.md`.
