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

Atualizado em 2026-10-29 apos o passe de verificacao por software (`hardware/reports/verification-pcb/`): DRC com 73 itens
(todos `lib_footprint_mismatch`, intencionais), 0 nao conectados; netclass USB 0,35/0,15 mm; 240 vias, 268 furos;
largura minima de mascara 0,1 mm; revisao dos gerbers com comparacao de conectividade 0 curtos / 0 abertos; pacote de
fabricacao regenerado em 2026-10-29. A placa deve ser encomendada como PCB nua e montada a mao.

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
| Vias | 240 (0,6/0,3 mm e 0,7/0,3 mm), todas passantes, sem cegas/enterradas, sem via-in-pad; 4 vias termicas da mesma rede dentro dos pads expostos de `U8`-`U11` | `step6_reports.json`; `fabrication/readme.md` item 5 |
| Componentes com furo passante | `P1` (receptaculo OBD-C, 12 PTH 0,4 mm + 4 rasgos + 2 NPTH 0,65 mm), `U3` (USB-A, 2 PTH 2,5 mm), pads-via termicos de `U6` (8 x PTH 0,3 mm + 1 via) | `drill_table.md` |
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
| USB | USB_D+/-, USB_R_D+/- | 0,35 mm | 0,6 / 0,3 mm | 0,35 / 0,15 mm (par acoplado em B.Cu, `verification-pcb/usb-reroute.md`) |

## 5. Valores usados na placa

| Parametro | Valor | Fonte |
|---|---|---|
| Menor largura de trilha presente | 0,14 mm | extraido (em segmentos de estreitamento; a maioria das trilhas de sinal tem 0,2 a 0,25 mm) |
| Menor afastamento de cobre presente | DRC passa a 0,1 mm; 0 violacoes `clearance` | `verification-pcb/drc_a9_final.json` |
| Menor furo | 0,300 mm (vias e vias termicas de `U6`) | `drill_table.md` |
| Tamanhos de via usados | 0,6/0,3 mm e 0,7/0,3 mm (240 no total) | `step6_reports.json` |
| Anel minimo | PTH 0,125 mm, via 0,150 mm | `drill_table.md` |
| Quantidade de furos | 268 (PTH 26, NPTH 2, via 240) | `drill_table.md`, `gerber_check.json` (Excellon vs PCB 268 vs 268), `verification-pcb/gerber-review.md` |
| Rasgos | 4 (1,199 a 1,2 mm de largura, carcaca de `P1`) | `drill_table.md` |
| Maiores furos | PTH 2,5 mm x2 (`U3`), NPTH 0,65 mm x2 (`P1`) | `drill_table.md` |
| Menor passo SMD | 0,5 mm (`U7` LQFP-144, `U8`-`U11` HVSON-8) | footprints |
| Menores passivos | 0402 (39 capacitores, 22 resistores) | contagem de footprints extraida |

## 6. Requisitos de impedancia

O projeto define alvos, mas **nenhuma impedancia foi simulada ou confirmada**; o DRC do KiCad
nao verifica impedancia (`fabrication/readme.md` item 1).

| Par | Alvo | Camada / geometria na placa | Estimativa analitica no repositorio | Estado |
|---|---|---|---|---|
| CAN BUSx_H/L (4 pares) | 120 ohm diferencial (nominal do barramento) | microstrip em F.Cu / B.Cu, largura 0,25 mm, gap 0,2 mm sobre prepreg de 0,2 mm para GND | faixa de 108 a 143 ohm reportada por `step6_reports.py` | nao confirmado; trilhas curtas entre transceptor e `P1`, a terminacao fica no chicote do veiculo, nao na placa |
| USB_D+/- (full speed) | 90 ohm diferencial | par acoplado em B.Cu, largura 0,35 mm, gap 0,15 mm, um par de vias, skew < 0,3 mm (`verification-pcb/usb-reroute.md`, 2026-10-29) | `verification-pcb/impedance.md` (Hammerstad-Jensen / Kirschning-Jansen, stackup do arquivo e JLC7628) | nao confirmado; USB FS a 12 Mbit/s e tolerante, mas nada foi medido |

Nota: o pacote de fabricacao foi regenerado em 2026-10-29 a partir da placa atual, apos o reroteamento do USB
(o item 2 de `fabrication/readme.md` descreve agora o par acoplado em B.Cu).

## 7. Resumo do resultado do DRC

Ferramenta: kicad-cli 10.0.7, todas as severidades, `hardware/reports/verification-pcb/drc_a9_final.json`
(2026-10-29; historico em `verification-pcb/drc-cleanup.md`: 135 itens antes do passe, `drc_a8_before.json`).

| Categoria | Quantidade | Natureza |
|---|---|---|
| Itens nao conectados | 0 | |
| Paridade com o esquema | 0 | |
| `clearance`, `shorting_items`, `courtyards_overlap`, `copper_edge_clearance`, `starved_thermal`, `drill_out_of_range`, `footprint_type_mismatch`, `track_width`, `via_dangling` | 0 | as quatro ultimas categorias existiam no baseline/placas intermediarias e foram eliminadas pelos scripts de correcao |
| `lib_footprint_mismatch` | 73 | footprints na placa diferem das copias da biblioteca (edicoes locais: ~61 so grafica/caminho 3D, Q1/Q2/Q3/U5/Y1 corrigidos na placa, P1/U6/U12 documentados); informativo |
| `text_height`, `hole_clearance`, `silk_edge_clearance`, `silk_overlap`, `silk_over_copper`, `solder_mask_bridge` | 0 | 62 itens resolvidos em 2026-10-28/29 (`verification-pcb/drc-cleanup.md`) |
| **Total** | **73** | reduzido de 135 antes do passe de verificacao e de 182 antes das correcoes SI/PI |

Os 73 itens restantes sao apenas controle de biblioteca; nenhum e violacao eletrica.

## 8. Arquivos de fabricacao

Diretorio `hardware/fabrication/`, regenerado em 2026-10-29 por
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
| `gerber_check.json` | verificacao sintatica de gerber/Excellon; a comparacao de render, contorno, furos e conectividade do cobre esta em `hardware/reports/verification-pcb/gerber-review.md` |
| `HybridPanda_gerbers_JLC.zip` | 16 entradas: os 11 gerbers, o job file, os arquivos de furacao PTH e NPTH e os 2 PDFs de mapa de furacao; preparado para upload mas **nao deve ser enviado** ate que os bloqueios abaixo sejam resolvidos |

## 9. Notas de montagem

- SMD nos dois lados: 80 footprints no topo (inclui `U7`, os quatro transceptores, `U6`,
  `U12`, `U1`, `P1`, `U3`, `J1`, `SW1`, `U5`), 45 no fundo (principalmente desacoplamento
  0402 sob `U7`, `JP1`, fiduciais `FID4`-`FID6`). O lado exato por referencia esta em
  `docs/hardware/bom.csv` (coluna `side`).
- Furo passante / misto: `P1` (receptaculo OBD-C, pads de sinal SMD mais carcaca THT), `U3`
  (USB-A, carcaca THT), ambos no topo. `U6` tem 8 pads-via termicos + 1 via sob o pad exposto; `U8`-`U11` uma via GND cada (`verification-pcb/hand-assembly.md`).
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

1. Impedancia (CAN 120 ohm, USB 90 ohm) apenas estimada analiticamente (tratado por software em 2026-10-29:
   `verification-pcb/impedance.md`, stackup JLC7628); stackup nao acordado com um fabricante.
2. Zero validacao fisica: nenhuma placa construida, montada ou medida; o firmware da red
   panda nunca rodou neste hardware.
3. BOM: 1 referencia sem MPN (`JP1`), 2 sem LCSC (`JP1`, `U1`); codigos LCSC "a verificar"
   nao confirmados; `U1` indisponivel na JLC.
4. Itens de DRC herdados: resolvidos em 2026-10-28/29 (135 -> 73 `lib_footprint_mismatch`, intencionais); tratado por software, nao verificado fisicamente.
5. Gerbers: revisados por software em 2026-10-29 (renders, contorno, furos, conectividade do cobre vs netlist: 0 curtos / 0 abertos, `verification-pcb/gerber-review.md`); a inspecao humana no GerbView continua listada em `fabrication/readme.md`.
6. Rotacoes do CPL normalizadas com a tabela JLC (`verification-pcb/cpl-rotation.md`); so relevante se algum dia for pedida montagem na JLC (o plano e PCB nua + montagem manual).
7. Exportacao de fabricacao regenerada a partir da placa final em 2026-10-29 (`step8_fabricate.py`).
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
