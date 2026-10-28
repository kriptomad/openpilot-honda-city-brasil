"""Gera footprint-audit.md e footprint_audit.json a partir de board_dump.json
(medidas reais da placa) + tabela de veredictos/datasheets abaixo.
Somente leitura da placa (usa o dump). Nao modifica nada fora de hardware/reports/footprint-audit.
Uso: python build_report.py
"""
import json
import os
from collections import defaultdict, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.normpath(os.path.join(HERE, "..", "..", "..", "hardware", "hybrid-panda"))
KICAD3D = r"C:\Users\costabr\AppData\Local\Programs\KiCad\10.0\share\kicad\3dmodels"

dump = json.load(open(os.path.join(HERE, "board_dump.json"), encoding="utf-8"))
fps = dump["footprints"] if isinstance(dump, dict) else dump
by_ref = {f["ref"]: f for f in fps}

# ---------------------------------------------------------------------------
# Veredictos por grupo. key = (lib, name) ou ref especifico.
# verdict: OK | NOTE | MISMATCH | UNVERIFIABLE
# ---------------------------------------------------------------------------
V = OrderedDict()


def add(key, verdict, mpn, ds_url, ds_land, board, fix="", notes="", pin1="", bom=""):
    V[key] = dict(verdict=verdict, mpn=mpn, datasheet_url=ds_url, datasheet_land_pattern=ds_land,
                  board_measured=board, fix=fix, notes=notes, pin1_check=pin1, bom_constraint=bom)


IPC = "Nao foi possivel baixar o datasheet (proxy corporativo / 403 / timeout). Comparado com a biblioteca KiCad 10 (IPC-7351 nominal)."

add(("Capacitor_SMD", "C_0402_1005Metric"), "NOTE", "generico 0402 (1005 metrico)", "-",
    "IPC-7351 0402: 2 pads ~0.56-0.62 x 0.62, centros +-0.48 a 0.51",
    "2 pads 0.56 x 0.62 mm roundrect, centros +-0.48 mm (= KiCad C_0402_1005Metric)",
    notes="C8 = 10uF em 0402 no rail +5V: 10uF 0402 so existe em 4 V / 6.3 V (X5R) -> a 5 V fica sem derating e perde >50% da capacitancia; mover para 0603 (10 V) ou aceitar. C43 1uF (VDDA) e C63 1uF (+3V3) 0402: OK.",
    bom="Capacitores 0402; C8 10uF: usar 0603 10 V ou reduzir para 4.7uF 6.3 V se o circuito permitir.")
add(("Capacitor_SMD", "C_0603_1608Metric"), "NOTE", "generico 0603 (1608 metrico)", "-",
    "IPC-7351 0603: pads 0.9 x 0.95, centros +-0.775",
    "2 pads 0.90 x 0.95 mm, centros +-0.775 mm (= KiCad C_0603_1608Metric)",
    notes="R6 '3.16K (1%)' usa footprint de CAPACITOR C_0603 (R_0603 teria pads 0.80 x 0.95 em +-0.825). Geometricamente solda um resistor 0603, mas BOM/footprint inconsistentes e modelo 3D de capacitor. Trocar por Resistor_SMD:R_0603_1608Metric.",
    fix="R6: trocar footprint para Resistor_SMD:R_0603_1608Metric (pads 0.80x0.95 em +-0.825).",
    bom="C39/C40 2.2uF, C60-C62 4.7uF em 0603: exigir >= 10 V (X5R/X7R) para rails 3V3/5V.")
add(("Capacitor_SMD", "C_0805_2012Metric"), "NOTE", "generico 0805 (2012 metrico)", "-",
    "IPC-7351 0805: pads 1.0 x 1.45, centros +-0.95",
    "2 pads 1.00 x 1.45 mm, centros +-0.95 mm (= KiCad C_0805_2012Metric)",
    notes="47uF em 0805 (C3,C10,C18-C21 em +5V; C17 em USB_PWR; C16 em +3V3) so existe em 4 V / 6.3 V (X5R) e a 5 V de polarizacao a capacitancia efetiva cai para ~15-25 uF. Nenhum 47uF esta em 12 V (bom), mas em 5 V exigir 10 V (derating 50%) -> 47uF/10V nao existe em 0805: BOM deve ir para 1206 (10 V) ou 1210 (16-25 V), e o footprint tera de mudar para C_1206/C_1210. 2.2uF 0805 em 12V_Protected (C4,C6,C7,C12): exigir >= 25 V (existe em 0805, OK). C42 10uF 0805 em VFBSMPS (interno STM32, ~1.2 V): OK.",
    bom="47uF em +5V/USB_PWR: 1206 10 V ou 1210 16-25 V X5R/X7R (footprint muda). 2.2uF em 12V_Protected: 0805 >= 25 V X7R.")
add(("Resistor_SMD", "R_0402_1005Metric"), "OK", "generico 0402", "-",
    "IPC-7351 0402: pads 0.54 x 0.64, centros +-0.51",
    "2 pads 0.54 x 0.64 mm, centros +-0.51 mm (= KiCad R_0402_1005Metric)")
add(("Inductor_SMD", "L_0603_1608Metric"), "OK", "ferrite bead 600R@100MHz, 0603 generico", "-",
    "IPC-7351 0603 indutor: pads 0.875 x 0.95, centros +-0.7875",
    "2 pads 0.875 x 0.95 mm, centros +-0.7875 mm (= KiCad L_0603_1608Metric)",
    bom="FB1: ferrite 0603 (1608), corrente >= corrente do rail filtrado.")
add(("Fiducial", "Fiducial_1mm_Mask2mm"), "OK", "fiducial", "-", "IPC: cobre 1 mm, abertura de mascara 2 mm",
    "pad circular 1.0 mm F.Cu, mascara 2.0 mm; sem modelo 3D (normal)",
    notes="DRC lib_footprint_mismatch apenas por atributos/clearance adicionados pelo pipeline.")
add(("BlackPanda", "DIOM4325X250N"), "NOTE", "SMAJ16CA-13-F (Diodes, SMA / DO-214AC, bidirecional)",
    "https://www.diodes.com/assets/Datasheets/ds18006.pdf (nao baixado - 403/timeout)",
    "Diodes SMA 'Suggested Pad Layout' (tipico): 2 pads ~2.0-2.5 x 1.5-1.8, gap ~1.6-2.1. " + IPC + " KiCad D_SMA: 2.5 x 1.8 em +-2.0.",
    "2 pads 2.12 x 1.50 mm, centros +-2.115 mm (span externo 6.35, gap 2.11). Atributo do footprint = THT com pads SMD (DRC footprint_type_mismatch). Silk simetrico (TVS bidirecional, sem polaridade).",
    fix="Alterar atributo para SMD (FOOTPRINT_ATTR_SMD). Opcional: adotar geometria KiCad D_SMA (2.5 x 1.8 em +-2.0) para mais filete; nao obrigatorio.",
    notes="Geometria herdada da comma (IPC 'least'). Pad 1 = GND, pad 2 = +12V; CA = bidirecional, orientacao irrelevante.")
add(("Diode_SMD", "D_SOD-123F"), "UNVERIFIABLE", "BAS70H,115 (Nexperia SOD123F)",
    "https://assets.nexperia.com/documents/data-sheet/BAS70H.pdf (403)",
    "Nexperia SOD123F recomendado: 2 pads ~1.1 x 1.2, span externo ~3.9 (valor de referencia; datasheet nao obtido). " + IPC,
    "2 pads 1.10 x 1.10 mm, centros +-1.40 mm (span externo 3.9) = KiCad D_SOD-123F. Marca de catodo (silk fechado) no lado do pad 1 = +5V (K); pad 2 = USB_PWR (A).",
    pin1="Catodo em +5V, anodo em USB_PWR: coerente (USB alimenta o rail 5V).")
add(("Diode_SMD", "D_SMA"), "UNVERIFIABLE", "B320AE-13 (Diodes, SMA/DO-214AC)",
    "https://www.diodes.com/assets/Datasheets/ds13006.pdf (nao baixado)",
    "Diodes SMA suggested pad (tipico): pads ~2.0-2.5 x 1.5-1.8, span externo ~6.5. " + IPC,
    "2 pads 2.50 x 1.80 mm, centros +-2.00 mm = KiCad D_SMA. Silk fechado no lado do pad 1 = Net-(D11-K) (catodo).",
    pin1="Pad 1 = K (rede *-K), pad 2 = GND (A): catodo no no de chaveamento, correto para buck.")
add(("Diode_SMD", "D_SMC"), "UNVERIFIABLE", "SM540C (SMC / DO-214AB)", "mccsemi (404); alternativa Diodes B540C ds13003",
    "SMC suggested pad (tipico Diodes/Vishay): pads ~3.3-3.6 x 2.4-2.6, span externo ~10. " + IPC,
    "2 pads 3.30 x 2.50 mm, centros +-3.40 mm (span externo 10.1) = KiCad D_SMC. Silk fechado no lado do pad 1 = L4 (K).",
    pin1="Pad 1 = K (no L4/switch), pad 2 = GND (A): correto para buck TPS5450.")
add(("Package_TO_SOT_SMD", "SOT-23"), "UNVERIFIABLE", "BAT54S (SOT-23, serie)",
    "https://assets.nexperia.com/documents/data-sheet/BAT54_SER.pdf (403)",
    "Nexperia SOT23 recomendado (tipico): pads ~1.0-1.4 x 0.6, pitch 0.95, span ~2.3-2.9. " + IPC,
    "3 pads 1.475 x 0.60 mm em x=+-0.9375, y=+-0.95 (= KiCad SOT-23). B.Cu.",
    pin1="BAT54S: 1=A1, 2=K2, 3=K1/A2 (center tap). Placa: 1=GND, 2=+3V3, 3=SBU1_ADC/SBU2 -> clamp GND..3V3 no sinal: coerente.")
add(("Diode_SMD", "D_SOD-323"), "UNVERIFIABLE", "BAS40WS,43 (Nexperia SOD323)",
    "https://assets.nexperia.com/documents/data-sheet/BAS40WS.pdf (403)",
    "Nexperia SOD323 recomendado (tipico): pads ~0.6 x 0.7, span externo ~2.7. " + IPC,
    "2 pads 0.60 x 0.45 mm, centros +-1.05 mm (= KiCad D_SOD-323). Silk fechado no lado do pad 1 = 12V_Protected (K); pad 2 = Net-(D2-A).",
    pin1="K em 12V_Protected, A em Net-(D2-A): nomes de rede coerentes com o simbolo.")
add(("BlackPanda", "SOT95P230X110-3N"), "NOTE", "PESD2CAN,215 (Nexperia SOT23)",
    "https://assets.nexperia.com/documents/data-sheet/PESD2CAN.pdf (403)",
    "Nexperia SOT23 (tipico): pads ~1.0 x 0.6, pitch 0.95, span externo ~2.9-3.3. " + IPC + " KiCad SOT-23: 1.475 x 0.6 em +-0.9375.",
    "3 pads 1.00 x 0.60 mm em x=+-1.15, y=+-0.95 (span externo 3.3, interno 1.3). Atributo THT com pads SMD (DRC). D8/D9 sem modelo 3D; D5-D7 com modelo.",
    fix="Atributo -> SMD. Atribuir modelo 3D ${KICAD10_3DMODEL_DIR}/Package_TO_SOT_SMD.3dshapes/SOT-23.step a D8/D9. Pads curtos (1.0): opcional alongar para 1.2 mantendo span externo.",
    pin1="PESD2CAN: 1=I/O1, 2=I/O2, 3=GND. Placa D5: 1=SBU1, 2=SBU2, 3=GND -> OK; D6-D9 nos pares CANH/CANL.")
add(("Connector_PinHeader_1.27mm", "PinHeader_2x05_P1.27mm_Vertical_SMD"), "OK", "header SWD 2x5 1.27 mm SMD (generico)", "-",
    "Header 1.27 mm SMD generico (ex. Samtec FTSH-105-01-L-DV): pads ~0.74 x 2.4, pitch 1.27, linhas +-1.95 (span 3.9).",
    "10 pads 2.40 x 0.74 mm, pitch 1.27, linhas em y=+-1.95 (= KiCad lib).",
    bom="Escolher header 2x05 1.27 mm SMD vertical compativel com FTSH-105 (pads em 2 linhas 3.9 mm).")
add(("BlackPanda", "IND-SMD_L7.3-W6.8"), "UNVERIFIABLE", "SMMS0650-470M (47uH 2A, 6.0x6.0x5.0?)",
    "nao baixado (fabricante chines; LCSC)",
    "Datasheet nao obtido. Indutor blindado 6050/0650 tipico: 2 pads ~2.0-2.4 x 3.0-3.5, gap ~3.0-3.8 (span externo ~7.5-8.4).",
    "2 pads 2.35 x 3.50 mm, centros +-3.00 mm (span externo 8.35, gap 3.65). Sem courtyard. Atributo THT com pads SMD (DRC). Body 7.3 x 6.8 no nome do footprint vs 'SMMS0650' (6.0 x 5.0?) -> conferir.",
    fix="Atributo -> SMD; adicionar courtyard (ret. ~8.9 x 7.6). Confirmar land pattern quando o MPN for fixado.",
    bom="L3: indutor SMD 2 pads, pads 2.35x3.5 em +-3.0; corpo <= 7.3 x 6.8 mm.")
add(("BlackPanda", "L_10.5x11.5_H4.0"), "UNVERIFIABLE", "15uH generico (corpo 10.5 x 11.5 x 4.0) - MPN a definir", "-",
    "Sem MPN. Indutores 1050/1054 tipicos (ex. Bourns SRR1050, Wurth 7447709xxx): pads ~3.6-4.0 x 4.0-4.6, span externo ~13 (centros ~+-4.5-4.9).",
    "2 pads 3.50 x 4.00 mm, centros +-4.75 mm (span externo 13.0). Modelo 3D .wrl do projeto.",
    bom="L4: corpo <= 10.5 x 11.5 x 4.0; pads 3.5x4.0 em +-4.75; Isat >= 2x corrente do buck (TPS5450 5 A tipico ~ 3-4 A).")
add(("Inductor_SMD", "L_Murata_DFE201610P"), "UNVERIFIABLE", "DFE201610E-2R2M (Murata 2.0 x 1.6 x 1.0)",
    "https://www.murata.com/products/productdata/8807029342238/DFE201610E.pdf (falha SSL via proxy)",
    "Murata DFE201610E recomendado (catalogo): pads 0.60 x 1.70, gap 0.80 (centros +-0.70) - valor de catalogo nao reconfirmado online.",
    "2 pads 0.55 x 1.60 mm, centros +-0.725 mm (= KiCad L_Murata_DFE201610P). Serie 'P' vs 'E' tem mesmo corpo 2016.",
    notes="Diferenca esperada <= 0.05 mm por pad; aceitavel.")
add(("BlackPanda", "USB-C-SMD_TYPE-C-USB-20"), "NOTE", "HRO TYPE-C-31-M-04 (USB-C 16P, hibrido SMD+THT)",
    "https://atta.szlcsc.com/upload/public/pdf/source/20190321/C129018_ECAF745BBC5FC08427E0CBD0F9A58A2A.pdf",
    "Pads SMD 12x 0.30 x 0.90 pitch 0.50; furos THT 12x diam 0.40, anel diam 0.65, 2 linhas a 0.70 (x +-0.4/+-1.2/+-2.8 e +-0.8/+-1.6/+-2.4); 4 slots blindagem 0.50 x 1.10 (+-0.05), linha superior span 8.97, inferior 8.24, distancia entre linhas 4.40; 2 NPTH posicionamento diam 0.65 x 0.025 (datasheet) em 5.64?",
    "A1-A12 SMD 0.30 x 0.90 pitch 0.50 (OK). B1-B12 PTH furo 0.40, pad 0.60 (anel 0.10 - fino; datasheet 0.65), posicoes e numeracao OK. 4 slots ovais pad 1.0 x 1.6 furo 0.6 x 1.2 em (+-4.49, 3.105) e (+-4.13, -1.305): spans 8.98/8.26, distancia 4.41 -> OK (+0.1 em furo/pad). 2 NPTH 0.80 em (+-3.675, -2.545). 12 circulos F.Paste 0.6 soltos sobre os pinos PTH (pasta inutil). DRC hole_clearance 0.144 mm entre slot PTH e NPTH (< 0.25).",
    fix="B1-B12: pad 0.60 -> 0.70 (anel 0.15). Remover 12 circulos F.Paste sobre PTH. Avaliar NPTH 0.80 -> 0.65 (datasheet) ou aceitar DRC hole_clearance com justificativa.",
    pin1="A1 lado do pad SMD extremo; pinos B em 2 linhas conforme desenho (12,9,7,6,4,1 / 11,10,8,5,3,2): confere.")
add(("BlackPanda", "SOT23-3"), "MISMATCH", "DDTA143ECA-7-F (Diodes SOT-23 pre-biased PNP)",
    "https://www.diodes.com/assets/Datasheets/ds30390.pdf (nao baixado)",
    "SOT-23 (Diodes 'Suggested pad layout' tipico / IPC): pitch 0.95 entre pinos 1-2 (dist. 1.90), pads ~1.0-1.5 x 0.6, centros em y +-0.95 a 1.0. KiCad SOT-23: 1.475 x 0.60 em x=+-0.9375, y=+-0.95.",
    "3 pads quadrados 0.914 x 0.914 mm em (+-0.889, -1.016) e (0, +1.001): distancia pinos 1-2 = 1.778 (datasheet 1.90, erro 0.12); pads curtos no eixo do terminal (0.91 vs 1.0-1.5). Sem courtyard. Modelo 3D OK.",
    fix="Substituir pads por geometria KiCad SOT-23: pads 1 e 2 em (+-0.95, +1.0) 0.6 x 1.475 (eixo do terminal em y), pad 3 em (0, -1.0); adicionar courtyard 3.3 x 3.0.",
    pin1="DDTA143ECA: 1=B(in), 2=E, 3=C. Placa Q1: 1=relay_SBU2 (base), 2=+5V (emissor, PNP), 3=SBU2 (coletor) -> coerente.")
add(("Package_TO_SOT_SMD", "SOT-323_SC-70"), "MISMATCH", "PDTC114EU (Nexperia SOT323 / SC-70)",
    "https://assets.nexperia.com/documents/data-sheet/PDTC114EU.pdf (403)",
    "Nexperia SOT323 recomendado (tipico): pads ~0.7-0.9 x 0.45-0.5 (eixo do terminal), pitch 0.65, span externo ~2.5-2.7. KiCad SOT-323_SC-70: pads 0.925 x 0.45 em x=+-0.8875, y=+-0.65 / 0.",
    "3 pads 0.45 x 0.70 mm (0.45 no eixo do terminal!) em x=+-1.00, y=+-0.65 e (+1.00, 0): span externo 2.45 (lib 2.35), pad transposto/curto no eixo do terminal (0.45 vs 0.925) e largo no eixo do pitch (0.70 com pitch 0.65 -> gap 0 entre pads 1 e 2 = risco de curto).",
    fix="Pads: tamanho 0.925 x 0.45 (x por y, footprint nao rotacionado), posicoes (-0.8875, -0.65), (-0.8875, +0.65), (+0.8875, 0). Unico desvio real detectado pelo lib_compare.",
    pin1="PDTC114EU: 1=B, 2=E, 3=C. Conferir redes apos correcao.")
add(("Package_SO", "PowerPAK_SO-8_Single"), "UNVERIFIABLE", "HY12P03C2 (HY Electronic, P-MOSFET; pacote PDFN 5x6 presumido)",
    "nao baixado (hy-electronic / LCSC)",
    "Vishay PowerPAK SO-8 single (referencia da lib KiCad): 4 pads 1.27 x 0.61 pitch 1.27 em x=-2.67; dreno 3.81 x 3.91 + 4 pads 1.02 x 0.61. Confirmar que HY12P03C2 e PDFN5x6 (DFN8 5x6 compativel).",
    "= KiCad lib: 4 pads 1.27 x 0.61 em x=-2.67 (y +-0.635/+-1.905), dreno 3.81 x 3.91 em (0.69, 0) + 4 pads 1.02 x 0.61 em x=2.795. Modelo 3D aponta para ${KICAD6_3DMODEL_DIR} (.wrl) - caminho obsoleto.",
    fix="Modelo 3D -> ${KICAD10_3DMODEL_DIR}/Package_SO.3dshapes/PowerPAK_SO-8_Single.step. Confirmar pacote do MPN.",
    pin1="PowerPAK: 1-3 S, 4 G, 5-8 D. Conferir redes (gate = EN do P-MOS).")
add(("Button_Switch_SMD", "SW_SPST_SKQG_WithStem"), "UNVERIFIABLE", "SW_Push generico (Alps SKQG ABE010 presumido)",
    "https://tech.alpsalpine.com/e/products/detail/SKQGABE010/ (land pattern so em GIF, nao lido)",
    "Alps SKQG: corpo 5.2 x 5.2 x 1.5. Land pattern Alps (catalogo): 4 pads ~1.8 x 1.1, centros x +-3.1, y +-1.85.",
    "4 pads 1.80 x 1.10 mm em (+-3.10, +-1.85) (= KiCad lib).",
    bom="SW1: tactile 5.2x5.2 SMD, 4 terminais em J (pads +-3.1 / +-1.85). Ex.: Alps SKQGABE010 ou C&K PTS810.")
add(("Package_TO_SOT_SMD", "SOT-23-6"), "UNVERIFIABLE", "AP22615AWU-7 (Diodes SOT-26)",
    "https://www.diodes.com/assets/Datasheets/AP22615.pdf (404) / LCSC (reset)",
    "Diodes SOT-26 suggested pad (tipico): pads ~1.0-1.3 x 0.6, pitch 0.95, span externo ~3.2-3.6. KiCad SOT-23-6: 1.325 x 0.60 em x=+-1.1375, y=0/+-0.95.",
    "6 pads 1.325 x 0.60 mm em x=+-1.1375, y=0/+-0.95 (= KiCad lib).",
    pin1="AP22615 SOT-26: 1=OUT, 2=GND, 3=FLG, 4=EN, 5=ILIM, 6=IN. Placa: 1=USB_PWR, 2=GND, 3=FLG, 4=EN (Q3), 5=ISET, 6=+5V -> coerente.")
add(("Package_DFN_QFN", "DFN-8-1EP_3x3mm_P0.65mm_EP1.55x2.4mm"), "NOTE", "TJA1042TK/3 (NXP HVSON8, SOT782-1)",
    "https://www.nxp.com/docs/en/package-information/SOT782-1.pdf",
    "SOT782-1 footprint: Ay 3.25 (span externo), By 2.20 (interno), pad 0.30 x 0.525, P 0.65; EP land 2.45 x 1.65 (SLx x SLy); pasta EP 1.10 x 0.65 (1x1); ocupado 3.25 x 3.50.",
    "8 pads 0.65 x 0.35 mm em x=+-1.55 (span externo 3.75, interno 2.45), pitch 0.65; EP 1.55 x 2.40 (F.Cu+F.Mask) + 4 ret. de pasta 0.6 x 1.0 (= KiCad lib).",
    fix="Opcional: encurtar pads para 0.525 e span externo 3.25-3.4 para aderir ao SOT782-1; pasta do EP (4 x 0.6) e maior que a NXP (1x 1.1x0.65) - reduzir se houver tombamento.",
    pin1="TJA1042: 1=TXD, 2=GND, 3=VCC, 4=RXD, 5=VIO, 6=CANL, 7=CANH, 8=STB. Placa U8: 1 TXD, 2 GND, 3 +5V, 4 RXD, 5 +3V3, 6 CANL, 7 CANH, 8 STB -> OK.",
    notes="Pads mais longos (0.65 vs 0.525) e span 0.5 mm maior que o NXP: aceitavel, mais filete externo.")
add(("Package_SO", "Diodes_PSOP-8"), "MISMATCH", "XL1509-3.3 (XLSEMI, SOP-8 padrao, sem pad exposto)",
    "http://www.xlsemi.com/datasheet/XL1509%20datasheet.pdf (connection reset)",
    "XL1509: pacote SOP-8L (3.9 x 4.9, pitch 1.27, sem EP) - datasheet nao baixado, conhecido do catalogo XLSEMI. SOIC-8 IPC: pads ~1.55 x 0.6, span externo 5.4-6.0.",
    "8 pads 1.50 x 0.65 mm em x=+-2.70, pitch 1.27 (OK para SOP-8) + 4 pads de EP 1.35 x 1.80 (total 2.70 x 3.60) COM pasta sob o corpo. Modelo 3D PowerIntegrations_SO-8.step (incorreto).",
    fix="Se XL1509 for SOP-8 sem EP: remover os 4 pads de EP (ou tirar F.Paste/F.Mask deles) - pasta sob corpo plastico gera bolas de solda/tombamento. Trocar footprint por Package_SO:SOIC-8_3.9x4.9mm_P1.27mm e modelo ${KICAD10_3DMODEL_DIR}/Package_SO.3dshapes/SOIC-8_3.9x4.9mm_P1.27mm.step. Se o MPN final for PSOP-8 com EP, manter.",
    pin1="XL1509 SOP-8: 1 (NC/ SS?), 2 VIN, 3 OUT, 4 GND, 5 FB, 6 ON/OFF... conferir no datasheet final.")
add(("BlackPanda", "USB-A-TH_10.0QHHTZB6.3"), "UNVERIFIABLE", "SHOU HAN 10.0 QHHTZB6.3 (USB-A femea, LCSC C668591)",
    "https://atta.szlcsc.com/upload/public/pdf/source/20200618/C668591_4974797655F912CB13E5351AD3DDB1B7.pdf (nao baixado)",
    "USB-A SMD 4 pinos pitch 2.5/2.0 + 2 abas THT; valores exatos nao obtidos.",
    "4 pads SMD 1.12 x 2.88 em x=+-1.0/+-3.5 (pitch 2.0-2.5, padrao USB-A), y=-4.395; 2 PTH ovais 1.2 x 3.1 furo 0.7 x 2.5 em (+-6.45, 4.395). Modelo 3D do projeto.",
    fix="Confirmar com o PDF LCSC quando acessivel (slots das abas e profundidade).")
add(("BlackPanda", "LED-ARRAY-SMD_4P-L2.2-W2.1-BR"), "NOTE", "FM-B1921RGBA-SH (Foshan Nationstar? RGB 2.1x2.0, 4P)",
    "https://atta.szlcsc.com/upload/public/pdf/source/20200110/C... FMB1921 (baixado; pagina 4/11)",
    "Reference soldering pad: 4 pads 0.66 x 0.70; gap X 1.00 (centros x +-0.83); gap Y 0.50 (centros y +-0.60). Corpo 2.15 x 2.05; nick mark no pino 1 (+). Pinos: 1 +, 2 R-, 3 G-, 4 B- (vista superior: 3 G- esq-sup, 2 R- dir-sup, 4 B- esq-inf, 1 + dir-inf).",
    "4 pads 0.66 x 0.70 em (+-0.83, +-0.50): X igual ao datasheet; Y 0.1 mm por pad mais para dentro (gap 0.30 vs 0.50). Pad 1 (+3V3) em (+0.83,+0.50) dir-inf com chanfro de silk e circulo no mesmo canto -> coincide com o nick mark.",
    fix="Mover pads para y=+-0.60 (gap 0.50) conforme datasheet. Polaridade OK.",
    pin1="1=+3V3 (anodo comum), 2=RED-, 3=GREEN-, 4=BLUE-: posicoes conferem com o desenho.")
add(("BlackPanda", "CONV_TPS5450DDAR"), "NOTE", "TPS5450DDAR (TI HSOP-8 PowerPAD, DDA0008J)",
    "https://www.ti.com/lit/ds/symlink/tps5450.pdf",
    "DDA: 8 pads 1.55 x 0.60, pitch 1.27, span externo 5.4 (pads +-2.7 centro... TI: 1.55 x 0.6 em x=+-2.7); thermal pad 2.95 x 4.90 (exposto), abertura mascara 2.60 x 3.10, stencil 2.60 x 3.10 (0.125 mm), vias diam 0.20 (furo) em grade 1.3 mm.",
    "8 pads 1.55 x 0.60 em x=+-2.70 (OK); EP 2.95 x 4.90 em F.Cu (sem F.Mask/F.Paste nas camadas do pad) + 8 vias pad 0.6 / furo 0.3 em (+-0.65, +-0.65/+-1.95); mascara e pasta do EP e dos pinos desenhadas como POLIGONOS graficos (F.Mask 2.61 x 3.11 + 8 x 1.7 x 0.75; F.Paste 2.61 x 3.11). Pinos 1-8 em F.Cu+F.Paste sem F.Mask no pad (abertura vem do grafico). Construcao herdada da comma (gerbers originais confirmam).",
    fix="Robustecer: pads 1-8 -> camadas F.Cu/F.Mask/F.Paste; EP -> F.Cu+F.Mask e pasta via pad com janela 2.6 x 3.1 (ou 4 retangulos); remover poligonos graficos de mascara/pasta. Vias 0.3 mm (TI 0.2) OK.",
    pin1="TPS5450: 1 BOOT, 2 NC, 3 NC, 4 VSENSE, 5 ENA, 6 GND, 7 VIN, 8 PH, 9 PowerPAD. Conferir redes no esquema.")
add(("Package_QFP", "LQFP-144_20x20mm_P0.5mm"), "NOTE", "STM32H725ZGT6 (ST LQFP144 20x20, pitch 0.5)",
    "https://www.st.com/resource/en/datasheet/stm32h725zg.pdf (timeout)",
    "ST 'LQFP144 recommended footprint' (tipico ST): pads 0.30 x 1.35, pitch 0.50, span externo 22.6, interno 19.9 (valores de referencia ST; PDF nao baixado).",
    "144 pads 1.475 x 0.30, pitch 0.50, centros +-10.6625 (span externo 22.8, interno 19.85) = KiCad lib. B.Cu. Pino 1 no canto com marca; pad 36 = VDDA, 144 = +3V3, 37 = PA0 coerentes com o pinout LQFP144 do H725.",
    notes="Pads 0.1 mm mais longos que ST e span externo +0.2: dentro da pratica IPC. Montado no lado B (espelhado no dump).",
    pin1="Pino 1 = PE2 (LED_BLUE no esquema) no canto do indice; 36 VDDA e 144 VDD coerentes com LQFP144 STM32H7.")
add(("Crystal", "Crystal_SMD_3225-4Pin_3.2x2.5mm"), "UNVERIFIABLE", "X322525MOB4SI 25 MHz (Yangxing 3225 4 pads)",
    "https://atta.szlcsc.com/... X322525MOB4SI (connection reset)",
    "Land pattern 3225 tipico (Yangxing/Abracon): pads 1.4 x 1.2, centros (+-1.1, +-0.85) (pitch 2.2 x 1.7). Datasheet nao baixado.",
    "4 pads 1.40 x 1.20 em (+-1.10, +-0.85) retangulares (lib KiCad: roundrect rr 0.25). Diferenca apenas de forma (cosmetica).",
    pin1="3225: 1 e 3 = cristal, 2 e 4 = GND. Conferir redes.")

# ---------------------------------------------------------------------------
groups = defaultdict(list)
for f in fps:
    groups[(f["lib"], f["name"])].append(f)

refs_sorted = lambda lst: sorted(lst, key=lambda f: (f["ref"].rstrip("0123456789"), int("".join(ch for ch in f["ref"] if ch.isdigit()) or 0)))


def pad_summary(f):
    out = []
    for p in f["pads"]:
        d = dict(num=p["num"], net=p["net"], local_x=p["lx"], local_y=p["ly"], size_x=p["sx"], size_y=p["sy"],
                 shape=p["shape"], attr=p["attr"], layers=p["layers"])
        if p.get("drill"):
            d["drill"] = p["drill"]
        out.append(d)
    return out


def model_status(f):
    st = []
    for m in f.get("models") or []:
        path = m.replace("${KIPRJMOD}", PRJ).replace("${KICAD10_3DMODEL_DIR}", KICAD3D)
        if "${KICAD6_3DMODEL_DIR}" in m or "${KICAD7_3DMODEL_DIR}" in m or "${KICAD8_3DMODEL_DIR}" in m:
            st.append((m, "OBSOLETO (variavel KiCad antiga)"))
        else:
            st.append((m, "ok" if os.path.exists(path) else "ARQUIVO NAO ENCONTRADO"))
    if not st:
        st.append(("", "SEM MODELO 3D"))
    return st


report = OrderedDict(method="pcbnew dump (footprint_dump.py) + lib_compare.py + kicad-cli DRC + datasheets (ds_bulk/ds_fetch/ds_render)",
                     units="mm", footprints=OrderedDict())
counts = defaultdict(int)
rows = []
for key, lst in groups.items():
    v = V.get(key)
    if v is None:
        raise SystemExit("sem veredicto para %s" % (key,))
    lst = refs_sorted(lst)
    refs = [f["ref"] for f in lst]
    for f in lst:
        vv = dict(v)
        if f["ref"] == "R6":
            vv["verdict"] = "NOTE"
        rails = sorted({p["net"] for p in f["pads"]})
        report["footprints"][f["ref"]] = OrderedDict(
            lib_id="%s:%s" % key, value=f["value"], layer=f["layer"], rotation=f["rot"], attrs=f["attrs"],
            models=[dict(path=m, status=s) for m, s in model_status(f)], nets=rails,
            pads=pad_summary(f), courtyard_mm=f.get("courtyard_mm"), bbox_mm=f.get("bbox_mm"), **vv)
    counts[v["verdict"]] += len(refs)
    rows.append((refs, key, lst[0]["value"], v))

counts_groups = defaultdict(int)
for refs, key, val, v in rows:
    counts_groups[v["verdict"]] += 1
report["summary_refs"] = dict(counts)
report["summary_groups"] = dict(counts_groups)
report["drc"] = dict(lib_footprint_mismatch=64, footprint_type_mismatch=["D1", "D5", "D6", "D7", "D8", "D9", "Q1", "Q2", "U5", "L3"],
                     hole_clearance_P1=8, note="64 lib_footprint_mismatch: pads identicos a lib exceto Q3, U6, Y1 (ver lib_compare.txt); demais sao courtyard explodido em linhas / marcas de pino 1 / atributos.")
json.dump(report, open(os.path.join(HERE, "footprint_audit.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=True)

# ---------------------------------------------------------------------------
L = []
w = L.append
w("# Auditoria de footprints - Hybrid Panda (KiCad 10)")
w("")
w("Placa: hardware/hybrid-panda/HybridPanda.kicad_pcb (somente leitura). %d footprints, %d grupos lib:footprint." % (len(fps), len(groups)))
w("Data da auditoria: gerado por build_report.py. Nenhum arquivo rastreado foi alterado; proposed_fixes.py so foi executado em --dry-run (e em --apply apenas sobre uma COPIA temporaria, depois apagada).")
w("")
w("**STATUS: PARCIAL.** Geometria de todos os 120 footprints medida e comparada com biblioteca/IPC; datasheets online obtidos apenas para U8-U11 (NXP SOT782-1), U6 (TI TPS5450), P1 (HRO TYPE-C-31-M-04) e U5 (FM-B1921RGBA-SH). Pendente ('a verificar' quando a rede permitir): PDFs de ST (U7), Diodes (D1, D11, Q1/Q2, U1), Nexperia (D2, D5-D9, D10, D13/D14, Q3), XLSEMI (U12), HY (Q4), Murata (L5), Alps (SW1), Yangxing (Y1), SHOU HAN (U3), SMMS0650 (L3). Para esses, os valores 'tipicos' citados vem de catalogo/memoria e NAO foram reconfirmados online.")
w("")
w("## Metodo")
w("")
w("1. footprint_dump.py (pcbnew): referencia, lib id, camada, rotacao, atributo, modelos 3D, cada pad (numero, rede, posicao local sem rotacao, tamanho, forma, PTH/SMD/NPTH, furo, camadas) -> board_dump.json.")
w("2. lib_compare.py: diff pad a pad contra a copia de biblioteca (KiCad 10 share/footprints e archive/baseline-original/.../BlackPanda.pretty, HybridPanda.pretty) -> lib_compare.txt/json. Resultado: so Q3, U6 e Y1 tem pads diferentes da lib; os 64 'lib_footprint_mismatch' do DRC restantes sao graficos (courtyard convertido em 4 linhas, marcas de pino 1 em silk, atributos de fiducial).")
w("3. kicad-cli pcb drc --severity-all: 64 lib_footprint_mismatch, 10 footprint_type_mismatch (D1, D5-D9, Q1, Q2, U5, L3: atributo THT com pads SMD), 8 hole_clearance em P1 (slot PTH x NPTH 0.144 mm), 1 drill_out_of_range (via 0.25 mm, nao e footprint).")
w("4. Datasheets: download via Python urllib com retries (ds_bulk.py), texto via pypdf (ds_fetch.py), desenhos renderizados com pymupdf (ds_render.py) e lidos visualmente. O proxy corporativo bloqueou/zerou a maioria dos downloads (Nexperia/Diodes 403, ST timeout, XLSEMI/LCSC reset, Murata SSL). Obtidos: NXP SOT782-1, TI TPS5450, HRO TYPE-C-31-M-04, FM-B1921RGBA-SH. Para os demais o veredito e UNVERIFIABLE ou NOTE comparando com a biblioteca KiCad 10 (IPC-7351 nominal) e valores tipicos de catalogo - indicados como tal.")
w("5. Polaridade/pino 1: polarity_dump.py lista pads + graficos de silk/fab por footprint; verificado D1, D2, D10, D11, D12, D5, Q1, U5 e os mapeamentos de rede de U1, U6, U7, U8-U11, Q4, D13.")
w("")
w("## Resumo")
w("")
w("| Veredito | Referencias | Grupos |")
w("|---|---|---|")
for k in ("OK", "NOTE", "MISMATCH", "UNVERIFIABLE"):
    w("| %s | %d | %d |" % ({"OK": "OK", "NOTE": "OK-com-nota", "MISMATCH": "MISMATCH", "UNVERIFIABLE": "UNVERIFIABLE"}[k], counts[k], counts_groups[k]))
w("")
w("MISMATCH: Q3 (SOT-323, pads transpostos/curtos), Q1/Q2 (SOT23-3 comma: distancia 1-2 = 1.778 vs 1.90, pads 0.91 quadrados, sem courtyard), U12 (pasta/EP sob SOP-8 sem pad exposto, modelo 3D errado).")
w("Observacoes principais: P1 anel 0.10 mm nos pinos THT + pasta solta sobre PTH; U5 pads 0.1 mm para dentro em Y; U6 mascara/pasta por grafico; 10 footprints com atributo THT em pecas SMD; 47uF 0805 em +5V (so existe em 6.3 V) e 10uF 0402 em +5V; R6 em footprint de capacitor; modelos 3D ausentes (D8, D9) ou obsoletos (Q4, U12).")
w("")
w("## Tabela por grupo")
w("")
w("| Referencias | Footprint | Valor | Veredito | Placa (medido) | Datasheet / referencia | Acao |")
w("|---|---|---|---|---|---|---|")
for refs, key, val, v in sorted(rows, key=lambda r: r[0][0]):
    rr = ",".join(refs) if len(refs) <= 6 else "%s ... (%d)" % (",".join(refs[:4]), len(refs))
    w("| %s | %s:%s | %s | %s | %s | %s | %s |" % (rr, key[0], key[1], val, v["verdict"],
      v["board_measured"].replace("|", "/"), v["datasheet_land_pattern"].replace("|", "/"), (v["fix"] or "-").replace("|", "/")))
w("")
w("## Capacitores 47uF 0805 - redes")
w("")
for ref in ("C3", "C10", "C16", "C17", "C18", "C19", "C20", "C21"):
    f = by_ref[ref]
    w("- %s: %s" % (ref, " / ".join(sorted({p["net"] for p in f["pads"]}))))
w("")
w("## Detalhe por footprint nao trivial")
w("")
for refs, key, val, v in sorted(rows, key=lambda r: r[0][0]):
    if key[0] in ("Capacitor_SMD", "Resistor_SMD") and "R6" not in refs:
        continue
    w("### %s - %s:%s (%s)" % (", ".join(refs), key[0], key[1], val))
    w("")
    w("- Veredito: **%s**" % v["verdict"])
    w("- MPN / pacote: %s" % v["mpn"])
    w("- Datasheet: %s" % v["datasheet_url"])
    w("- Land pattern do datasheet/referencia: %s" % v["datasheet_land_pattern"])
    w("- Medido na placa: %s" % v["board_measured"])
    if v["pin1_check"]:
        w("- Pino 1 / polaridade: %s" % v["pin1_check"])
    if v["notes"]:
        w("- Notas: %s" % v["notes"])
    if v["fix"]:
        w("- Correcao proposta: %s" % v["fix"])
    if v["bom_constraint"]:
        w("- Restricao para a BOM: %s" % v["bom_constraint"])
    ms = model_status(refs_sorted(groups[key])[0])
    w("- Modelo 3D: %s" % "; ".join("%s [%s]" % (m or "-", s) for m, s in ms))
    w("")
w("## Modelos 3D (STEP export rc 2)")
w("")
w("| Ref | Modelo atual | Situacao | Sugestao |")
w("|---|---|---|---|")
sugg = {"D8": "${KICAD10_3DMODEL_DIR}/Package_TO_SOT_SMD.3dshapes/SOT-23.step", "D9": "${KICAD10_3DMODEL_DIR}/Package_TO_SOT_SMD.3dshapes/SOT-23.step",
        "Q4": "${KICAD10_3DMODEL_DIR}/Package_SO.3dshapes/PowerPAK_SO-8_Single.step",
        "U12": "${KICAD10_3DMODEL_DIR}/Package_SO.3dshapes/SOIC-8_3.9x4.9mm_P1.27mm.step (se SOP-8 sem EP)",
        "FID1": "nenhum (fiducial)", "FID2": "nenhum", "FID3": "nenhum", "FID4": "nenhum", "FID5": "nenhum", "FID6": "nenhum"}
for f in refs_sorted(fps):
    for m, s in model_status(f):
        if s != "ok" or f["ref"] == "U12":
            w("| %s | %s | %s | %s |" % (f["ref"], m or "-", s if f["ref"] != "U12" else "modelo de outro pacote (PowerIntegrations SO-8)", sugg.get(f["ref"], "verificar")))
w("")
w("Modelos .wrl do projeto (L3, L4, U3, U5) existem mas sao VRML: a exportacao STEP os ignora (rc 2). Substituir por STEP equivalentes quando os MPN forem fixados.")
w("")
w("## Restricoes de footprint para a escolha da BOM (pecas genericas)")
w("")
for refs, key, val, v in sorted(rows, key=lambda r: r[0][0]):
    if v["bom_constraint"]:
        w("- %s: %s" % (",".join(refs) if len(refs) <= 8 else refs[0] + "...", v["bom_constraint"]))
w("")
w("## Arquivos")
w("")
w("- footprint_audit.json: por referencia - lib id, pads medidos, valores de datasheet, veredito, correcao, status dos modelos 3D.")
w("- footprint_dump.py, lib_compare.py, polarity_dump.py: scripts pcbnew somente leitura usados.")
w("- ds_bulk.py / ds_fetch.py / ds_render.py: ferramentas de datasheet; datasheets/: PDFs obtidos e PNGs renderizados.")
w("- proposed_fixes.py: aplica as correcoes por referencia (Q3, Q1/Q2, U5, P1, U6, U12, atributos SMD, modelos 3D). Padrao --dry-run; com --apply faz backup antes. NAO foi executado contra a placa real (apenas dry-run).")
w("")
w("Observacao: esta auditoria compara geometria; nao substitui a revisao do fabricante de montagem nem o DFM da fab.")
open(os.path.join(HERE, "footprint-audit.md"), "w", encoding="ascii", errors="replace").write("\n".join(L))
print("refs", dict(counts), "groups", dict(counts_groups))
