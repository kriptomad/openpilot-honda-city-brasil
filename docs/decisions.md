# DECISIONS.md — registro de decisões (ADR curto)

Formato: ID | data | decisão | alternativas | evidência | status.

## D-01 — Raiz de execução = pasta v2 existente (sem subpasta `run_`)
- Data: 2026-10-22
- Decisão: usar `HybridPanda_v2_20261022_1616` como OUTPUT_ROOT efetivo do protocolo v3 em vez de criar `run_<timestamp>` novo.
- Motivo: STEP 1 já concluído nela (manifestos, baseline, clones, ERC/DRC baseline); recriar violaria "não duplicar trabalho" e quebraria referências. Estrutura de pastas é a mesma exigida pelo v3.
- Status: ATIVA.

## D-02 — MCU STM32H725ZGT6 (LQFP144), modo Direct SMPS
- Data: 2026-10-22
- Decisão do usuário (fixa): família/parte = STM32H725. Decisão técnica derivada: encapsulamento LQFP144, não TFBGA100 nem LQFP100.
- Alternativas rejeitadas:
  - TFBGA100 (H723/H725): firmware `stm32h7/clock.h:30-47` força **LDO** nesse pacote; a biblioteca KiCad e DS13311 Tab.8 mostram **ausência de GPIOF/GPIOG** → PF7–PF11, PG9–PG11 (HW_TYPE straps, FDCAN3, STB bus0, VOLT_S) inexistem → paridade 1:1 com `red.h` impossível.
  - LQFP100: idem (sem PF/PG) e PKGR não reconhecido pelo firmware → `while(true)`.
  - UFBGA169: tem SMPS e todos os pinos, mas BGA 0,5 mm é inviável para montagem/4 camadas no formato Black Panda.
- Evidência: `02_REFERENCE\panda\board\stm32h7\clock.h`, `03_RESEARCH\kicad_lib_STM32H723VGHx_pins.txt`, `03_RESEARCH\P3_tabela_pinos_LQFP144_vs_firmware.md` (39/39 pinos presentes, AF confirmadas, cruzamento com lib KiCad: 0 divergências).
- Consequências: alimentação do core via SMPS interno (indutor 2,2 µH + caps conforme DS Tab.16); VDDLDO ainda alimentado; `-DSTM32H725xx` já é o build padrão do red panda.
- Status: ATIVA.

## D-03 — Remoção do GPS NEO-M8M
- Decisão: não portar o bloco GPS do Black Panda (red panda não tem GPS; firmware não usa UART para GPS no H7). Área liberada para LQFP144 + SMPS.
- Status: ATIVA (ainda não executada no esquemático).

## D-04 — Terminação 120 Ω
- Decisão provisória: footprints de terminação selecionável **não populados** por padrão (ponto de conexão no City é em derivação do harness, barramento já terminado). Justificar por canal na Fase 4.
- 2026-10-23: **CONFIRMADA** por fonte oficial — hardware\harness\v3\Harness_Box.pdf mostra R6/R7/R8 120 Ω dentro da harness box (CAN0' e CAN2/CAN2'') → o lado panda não termina. Manter footprints DNP para bancada (sem harness box).
- Status: ATIVA.

## D-05 — Premissa P1 (CAN-FD no City 2023 BR) REFUTADA; prosseguir mesmo assim
- Evidência: opendbc `HONDA_CITY_7G = HondaBoschPlatformConfig(..., BOSCH_RADARLESS)`, CAN clássico 500 kbit/s. Usuário optou por continuar com H7 (FDCAN é retrocompatível; black panda FW descontinuado).
- Status: ATIVA.

## D-06 — Plataforma host do openpilot (smartphone vs. dispositivo dedicado tipo comma 4)
- Data: 2026-10-22
- Status: **PENDENTE — não decidir sem o usuário.** Opções: (a) smartphone/dispositivo externo; (b) hardware dedicado rodando openpilot localmente com tela, câmeras, IMU, GPS (modelo comma four). Ao retomar, levantar requisitos no clone do openpilot (system/hardware/*, pandad, camadas tici/comma four) e produzir comparativo para a decisão.

## D-07 — Termo "openflow" = openpilot
- Interpretação registrada conforme protocolo v3 (0x00 Constantes).
- Status: ATIVA.

## D-08 — Straps HW_TYPE para RED (id1 = 0)
- Data: 2026-10-23
- Decisão: PF7, PF8, PF9, PF10 ligados a GND (resistor 0 Ω/direto; firmware lê com pull-up interno, `stm32h7/board.h:25-29`). PD4, PD5, PD6 deixados NC (id2 ≠ 3 garantido, pois PD7 é saída STB e flutua alto na leitura). Alternativa rejeitada: resistores de pull-down "fracos" (valor real do red panda NV; 0 Ω elimina margem de erro).
- Evidência: HRS_red_panda.md §1.
- Status: ATIVA.

## D-09 — STB dos transceivers com pull-up externo (fail-safe silencioso)
- Data: 2026-10-23
- Decisão: cada linha STB (PG11, PB3, PD7, PB4) com pull-up 10 kΩ para 3,3 V, para que os transceivers fiquem em standby desde o reset até `board_init` (early_gpio_float deixa tudo flutuando, `stm32h7_config.h:95`). Valor do red panda NV; 10 kΩ é prática comum e não conflita com saída push-pull.
- Status: ATIVA.

## D-10 — Clone do openpilot sem objetos Git LFS
- Data: 2026-10-23
- Fato: checkout falhava (1255 arquivos) por LFS → `huggingface.co/commaai/openpilot-lfs.git` responde 403, não por long paths. Solução: `GIT_LFS_SKIP_SMUDGE=1`, `filter.lfs.smudge --skip`; 253 ponteiros LFS mantidos como texto. Clone limpo em ff47f484, submódulos iniciados (depth 1).
- Implicação: nenhuma análise de hardware/host depende de binários LFS. Registrado em LICENSES.md.
- Status: ATIVA.

## D-11 — Versão do firmware panda de referência
- Data: 2026-10-23
- Fato: openpilot ff47f484 pina o submódulo panda em **a5919516**, enquanto o clone `02_REFERENCE\panda` está em **408e14d4** (master). Decisão: HRS baseado em 408e14d4 (mais recente); antes do STEP 8 (bring-up) comparar `board/boards/red.h`, `stm32h7/*` entre os dois commits e registrar diff (esperado: nenhum impacto em pinos).
- Status: ATIVA (diff pendente).

## D-12 — Caminho SBU → ADC não pode ser direto em PC4
- Data: 2026-10-23
- Fato: DS13311 Tab. 8: PC4 é **TT_ha** (3,6 V máx.), PA1 é FT_ha; a linha SBU chega a 5 V quando o relé é acionado (Harness_Box.pdf / harness.h). Decisão: divisor resistivo ou resistor série + clamp em ambos SBU1/SBU2 (simetria), dimensionado para que 240 Ω → "baixo", 1 kΩ → "baixo", aberto → "alto" em relação a 1650 mV e ao VIL digital. Valores finais no STEP 4.
- Status: ATIVA (dimensionamento pendente).
## D-13 — Pinagem do conector P1 (TYPE-C-31-M-04) mantida igual ao baseline
- Data: 2026-10-23
- Fato: netlist do baseline: bus0 xcvr→B10/B11, bus1-normal→B2/B3, bus1-OBD→A2/A3, bus2→A10/A11, SBU1=A8, SBU2=B8. Pinout oficial do lado harness (OBD-C.sch.pdf): CAN0=A2/A3, CAN1=A10/A11, CAN2=B2/B3, CAN3=B10/B11. O cabo USB-C full-featured cruza TX1(A2/A3)↔RX1(B11/B10), RX2(A11/A10)↔TX2(B2/B3) e SBU1↔SBU2; harness.h:71-75 confirma o cruzamento SBU ("SBU1->SBU2 is the normal orientation connection per USB-C cable spec"). Resultado: panda bus0→CAN0 carro, bus1-normal→CAN1 radar, bus1-OBD→CAN3 comma power, bus2→CAN2 câmera — coerente com o firmware red (red.h:31-61, can_common.h:130-134).
- Decisão: não alterar a pinagem de P1; só trocar os pinos do MCU nos transceivers. Cruzamento do cabo é inferência da spec USB-C [I]; o comportamento flipped é tratado pelo firmware em qualquer caso.
- Evidência: STEP3_engenharia_reversa_tabela_hibrida.md §g-1.
- Status: ATIVA.

## D-14 — VDD33USB = 3V3 externo; VDD50USB ligado a VDD33USB
- Data: 2026-10-23
- Fato: firmware red habilita apenas `PWR_CR3_USB33DEN` (stm32h7/clock.h:121); `USBREGEN` só em tres.h:106. Regulador USB interno OFF ⇒ DS13311 l.1459-1460 e tabela de condições de operação (l.8453-8455): VDD33USB alimentado externamente com 3,3 V e VDD50USB = VDD33USB.
- Decisão: VDD33USB (91) e VDD50USB (90) ambos no trilho +3V3, com 100 nF cada.
- Status: ATIVA.

## D-15 — Correção de rótulo normal/OBD do FDCAN2 (errata interna)
- Data: 2026-10-23
- Fato: red.h:36-61 e black.h:33-57: `(mode==NORMAL) != flipped` → **PB5/PB6 = normal (xcvr 2, STB PB3/PC13)**; senão **PB12/PB13 = OBD (xcvr 4, STB PB4/PB10)**. firmware_pins.json e HRS §3/§5 tinham os rótulos invertidos; corrigidos nesta data (grupos trocados, pinos inalterados — parity_check black_f4 continua 35/35).
- Status: ATIVA.
## D-16 — Condicionamento SBU → ADC: 10 kΩ série + BAT54S (clamp) em PC4 e PA1
- Data: 2026-10-23
- Fato: PC4 é TT_ha (3,6 V abs. máx., DS13311 Tab. 8); SBU chega a 5 V com relé acionado. Divisor resistivo rejeitado: com o pull-up de 10 kΩ existente (R23/R24 → 3V3) o caso "aberto" cairia ≈ 1,65 V ≈ limiar do firmware (1650 mV) e o caso 5 V ainda excederia 3,6 V em PC4 sem clamp. Escolhido: 10 kΩ série (R28/R29) + BAT54S (D13/D14: COM no nó ADC, K → 3V3, A → GND) em ambos os canais (simetria).
- Riscos: clamp em 3,3 + Vf ≈ 3,55 V — marginal vs. 3,6 V (corrente limitada a ≈ (5−3,55)/10k = 145 µA → Vf baixo); impedância de fonte do ADC ≈ 20 kΩ (ADC do H7 tolera com tempo de amostragem longo — firmware usa `ADC_SMPR` padrão; **NV**, validar no bring-up: ler SBU com 240 Ω / 1 kΩ / aberto / 5 V).
- Status: ATIVA (validação no STEP 8).

## D-17 — Nets CAN renomeadas CANx_* → BUS0/BUS1N/BUS1O/BUS2_* (EN → STB)
- Data: 2026-10-23
- Fato: a numeração CANx do baseline não coincide com a numeração de bus do firmware (bus0 = CAN2_, bus1 normal = CAN3_, bus1 OBD = CAN1_, bus2 = CAN0_). Para o STEP 5–9 e para o verificador, os nomes de net seguem o firmware. P1 inalterado (D-13).
- Status: ATIVA.

## D-18 — Folha A1, U7 em (701,04; 266,70), blocos de suporte em x 787–813 e regiões liberadas
- Data: 2026-10-23
- Fato: o símbolo STM32H725ZGTx (±48,26 × ±93,98 mm) não cabe na região do F413 em A2. Folha ampliada para A1 (841 × 594); MCU e coluna de suporte à direita (x ≥ 600), pull-ups STB e banco de desacoplamento na região liberada do F413, PWR_FLAGs na região do GPS. Gerado por `step4_build_schematic.py` (determinístico, idempotente a partir de `HybridPanda.kicad_sch.baseline`).
- Status: ATIVA.

## D-19 — Três pinos VCAP interligados; ERC power_out↔power_out rebaixado para aviso
- Data: 2026-10-23
- Fato: DS13311 §6.3.2: VCAP ×3 ligados entre si com 2 × 2,2 µF (ESR < 100 mΩ). O símbolo KiCad declara VCAP como `power_out`; a matriz padrão do ERC marca power_out↔power_out como erro. Alterado `erc.pin_map[8][8] = 1` (aviso) no `HybridPanda.kicad_pro` — único efeito colateral: outros curtos entre power_out passariam a aviso; nenhum outro par existe no projeto (ERC: só os 2 pares VCAP).
- Status: ATIVA.

## D-20 — Transceivers TJA1042TK/3 reaproveitados (CAN FD 5 Mbit/s confirmado)
- Data: 2026-10-23
- Fato: datasheet NXP TJA1042 (R3v2 §3.1, [F]): "timing guaranteed for data rates up to 5 Mbit/s in the CAN FD fast phase"; pinagem HVSON8 TXD1/GND2/VCC3/RXD4/VIO5/CANL6/CANH7/STB8 igual ao footprint do baseline. Alternativas documentadas: TCAN1042HGV-Q1 (provável pino-compatível, NV), MCP2562FD (NV), TCAN1044V (NÃO pino-compatível). Substitui a hipótese "Substituído" da tabela híbrida (STEP 3 §f/§g). A linha "Transceivers" passa a **Reaproveitado**.
- Status: ATIVA.

## D-21 — MCU U7 (LQFP-144) montado em B.Cu
- Data: 2026-10-24
- Fato: a região do F413 em F.Cu (≈ 10 × 10 mm úteis) não comporta o LQFP-144 (22 × 22 mm c/ courtyard) sem deslocar os conectores OBD/USB e o GPS. B.Cu sob a região do F413 está livre de componentes no baseline; U7 colocado em (109,5; 56,6) rot 90 em B.Cu, com desacoplamento (C4x..C6x), VCAP (C45/C46) e cristal Y1/C23/C24 no mesmo lado. Gerado por `step5_update_pcb.py` (idempotente a partir de `.baseline`).
- Riscos: montagem dupla-face (custo SMT); as STLs de caixa do baseline assumiam B.Cu sem componentes altos (ver D-24).
- Status: ATIVA.

## D-22 — Interpretação das distâncias da regra 0x05 (VCAP/cristal/desacoplamento)
- Data: 2026-10-24
- Fato: as distâncias "< 2 mm VCAP", "< 4 mm cristal" são medidas **pad-a-pad** (borda da ilha do capacitor → borda do pad do U7), não centro-a-centro, pois é o comprimento de trilha que importa (indutância). Valores obtidos: VCAP 1,25/1,34 mm; cristal 1,64–3,28 mm; SMPS C41.1→L5 1,94 mm, C42.1→L5 2,68 mm (`06_REPORTS/step5_update_pcb.json` → `distances_cc`).
- Status: ATIVA.

## D-23 — Roteamento: trilhas críticas por script + Freerouting 2.5.0 (60 passes) + corretor orientado por DRC
- Data: 2026-10-24
- Fato: `step5b_route.py` roteia por script as trilhas críticas (VCAP, cristal, SMPS, desacoplamento, vias GND do U7 — inclusive sob o corpo do LQFP), trava todas as trilhas/vias do baseline e exporta DSN sem as zonas não-GND; Freerouting (headless, Java 25) fecha o restante; `step5c_fix_unrouted.py` fecha os `unconnected_items` restantes lendo o JSON do `kicad-cli pcb drc`. 200 passes (108 min) não melhoram vs. 60 (≈ 8 min). Restringir In1/In2 a `(type power)` **piorou** (29 vs. 17 não-roteadas) — o próprio baseline usa In1 (48) e In2 (34) para sinais; mantido como flag `--inner-power` (default OFF). Correção colateral: `seg_collides` agora respeita a camada das keepouts (áreas de regra só-F.Cu do SW1 bloqueavam B.Cu indevidamente).
- Status: ATIVA.

## D-24 — Placa ampliada +5 mm ao sul (Edge.Cuts y_max 73,76 → 78,76)
- Data: 2026-10-24
- Fato: a fileira sul do U7 (y = 67,26) ficava a 6,5 mm da borda, disputando espaço com Y1/C23/C24, L5/C41/C42, C45/C60/C63, SW1, Q1/Q2, D14. Autorização do usuário: "se precisar aumentar a area da pcb, nao tem problema" / "ja falei que se precisar aumentar a board, pode aumentar". Implementado na fase E de `step5_update_pcb.py`: todos os pontos do polígono Edge.Cuts com y > y_mid deslocados +5 mm (cantos arredondados preservados). Zonas GND/+3V3 estendidas até a nova borda.
- Consequência: as STLs de caixa em `01_BASELINE` **não servem mais** (desvio mecânico; nova caixa é tarefa fora do escopo STEP 1–9).
- Status: ATIVA.

## D-25 — Limpeza de "fragmentos" tem de respeitar o preenchimento das zonas
- Data: 2026-10-25
- Fato: a limpeza de trilhas soltas em `step5_update_pcb.py` (`cleanup_dangling`) e em `step5b_route.py` (`_touch`) considerava "ponta solta" qualquer extremo que não tocasse pad/trilha/via. Vários stubs do baseline terminam **dentro do preenchimento** de uma zona da mesma rede (GND/+3V3/+5V) — eram apagados indevidamente (5a: 67 → 50 itens removidos; 5b: 121 → 46). Corrigido: um extremo contido em `ZONE.GetFilledPolysList(layer)` da mesma rede conta como ligado. Única remoção legítima mantida: via GND do baseline em (120,41; 53,18), que colide com o pad U7.120 em B.Cu (origem do caso U1.2, ver D-26).
- Status: ATIVA.

## D-26 — Corretor pós-Freerouting: estratégias e dois casos encurralados
- Data: 2026-10-25
- Fato: `step5c_fix_unrouted.py` fecha os `unconnected_items` do DRC com, por ordem: via de costura em pad U7/8 direções, via-in-pad (0,6 → 0,5/0,3 — permitido pelas regras: via mín. 0,4, furo mín. 0,3), trilha curta até o pour da mesma rede, ligação de ilhas (via em qualquer ponto da ilha), trilha directa/em Z/por via (In1/In2), roteador A* local em grelha de 0,25 mm (8 vizinhos, obstáculos locais), e **rip-up** genérico: se o único bloqueio para uma via junto a um pad SMD for uma cadeia de trilhas destravadas de outra rede de sinal, remove-a, coloca via + stub + A* interno e re-roteia a outra rede por A* na mesma camada (tudo revertido se falhar). Também corrige `hole_to_hole`/`hole_clearance` entre vias destravadas (funde pares da mesma rede; remove via × trilha do FR), porque o Freerouting não respeita a folga furo-cobre de vias pré-existentes.
- Casos: (1) **U1.2 (GND, SOT-23-6 F.Cu)** só tem um ponto de via possível (via-in-pad 0,5 em 119,0; 53,42), bloqueado pela trilha +5V In1 em x = 119,11 → correção manual M1: desvia o troço vertical dessa trilha para x = 118,3 e encurta a diagonal. (2) **R19.1 (LED_RED, F.Cu)** fica sobre os pads U7.26–29 (B.Cu) e a trilha HSE_OUT (crítica, travada) — nenhuma via cabe ao norte de y = 68,4; resolvido pelo rip-up da RED- (via 0,5 em 105,38; 68,97 + A* In1).
- Nota: `id()` de proxies swig do pcbnew não é estável entre chamadas — usar `m_Uuid.AsString()` como chave.
- Status: ATIVA.

## D-27 — Fase P (potência antes do Freerouting) e folga de furo das vias no DSN
- Data: 2026-10-26
- Fato: (a) o Freerouting é não-determinista e, entre corridas, as suas trilhas passavam a bloquear os únicos pontos de via de pads de potência encurralados (U1.2, C14.2, C48.1). Por isso o `step5b_route.py` ganhou a **fase P**: executa o `step5c --pre` sobre a placa viva (só GND/+3V3/+5V, itens travados) *antes* do DSN — o Freerouting passa a desviar deles. (b) O DSN não exprime `hole_clearance` (0,25 mm): via 0,5/0,3 + clearance 0,10 = 0,35 mm do centro, mas o furo exige 0,15 + 0,25 = 0,40 → o DRC acusava `hole_clearance` em vias do FR e o 5c arrancava-as (até 14 itens de uma vez, desfazendo rotas inteiras — corrida de 26-10: 9 → 7 não ligados). Corrigido no DSN com `(clearance 160 (type via_wire|via_smd|via_pin))` (classes `wire/via/smd/pin/area` aceites por `Structure.setClearanceRule` do Freerouting). (c) `trilha->pour` só liga a um contorno vertido que contenha via/PTH da rede para o plano (senão era uma ilha e a correcção repetia-se a cada rodada).
- Incidente: a corrida iniciada em 23-10 16:35 ficou com o PC em suspensão; o Freerouting só fez 3 passes em 63 h de relógio (`freerouting_s` 229 404) → resultado descartado.
- Status: ATIVA.

## D-28 — Corredor U7.121–124 ↔ U9 (BUS2), via 0,5 para o Freerouting e clearance da zona GND
- Data: 2026-10-26
- Fato: BUS2_TX/BUS2_RX (U7.122/123, B.Cu) ficavam sem rota: os pads estão a 2,5 mm de U9.1/U9.4 (F.Cu) mas o corredor era fechado por (i) a via +3V3 própria do pino 119 (121,96; 53,85), (ii) a via de costura do C55.1 (122,49; 53,57), (iii) C31 (desacoplamento do U9) em F.Cu entre os dois CIs e (iv) as faixas BUS2_STB/BUS0_STB. Correcções em `step5b_route.py`: pino 119 deixa de ter via própria (é alimentado pela trilha crítica C55.1 + via do C55.1 — ver fase C/V); a via do C55.1 tem posição preferida a norte (`STITCH_PREF`, 122,28; 52,10); a classe `kicad_default` do DSN passa a `use_via 500:300` (a classe KiCad usa 0,7, que com a regra `via_*` = 0,16 dava raio efectivo 0,51 em vez dos 0,40 que o furo exige). Resultado: BUS2_TX/RX roteados pelo Freerouting (corrida 09:23).
- Zona GND: o baseline tinha clearance 0,508 mm e espessura mínima 0,25 — a via de costura do U7.128 (122,36; 57,10) ficou fora do preenchimento In2 por causa dos knock-outs de três vizinhos (via +5V, via BUS2_RX, trilha BUS1O_TX). Clearance da zona GND reduzida para 0,254 mm (10 mil; mínimo de fabrico 0,1). É uma alteração global ao baseline, documentada aqui.
- Status: ATIVA.

## D-29 — Ilhas de conectividade GND/+3V3, curto +5V×U1.2 e regras DSN finais
- Data: 2026-10-26
- Fato: com 0 `unrouted` o DRC ainda acusava 3 `unconnected_items` (2 zona GND↔zona GND, 1 via↔trilha +3V3). Causa: o Freerouting roteia muito em In1 (~110 segmentos) e In2 (~125) e cerca regiões do plano GND In2 (junto a U8/C57/D5 e R6.1/C3.2), criando agrupamentos de conectividade separados (379 / 24 / 5 itens); o baseline já usa In1/In2 para sinais e `--inner-power` piora o resultado (D-25/D-27), logo o roteamento interno é mantido. Correção genérica em `step5c_fix_unrouted.py` → `fix_clusters(net)`: para cada agrupamento que não seja o principal, procura pontos num anel (0,6–5,0 mm, 24 ângulos) dentro do preenchimento principal (`SHAPE_LINE_CHAIN.Distance(p, outlineOnly=True)` ≥ 0,4) onde caiba uma via 0,6/0,5 e liga por trilha directa, em Z ou A*. Aplicado a GND e +3V3.
- Ilha +3V3 {U7.119, trilha crítica, C55.1, via 122,49; 53,57}: a via ficava fora do preenchimento In1 (+3V3) por knock-out de uma trilha relay_SBU2 do FR em In1 + via BUS2_TX. Mitigações: clearance da zona +3V3 In1 0,508 → 0,254; `fix_clusters` liga a ilha ao plano.
- **Curto real** encontrado: a correção M1 do 5c (D-26) desviava a trilha +5V In1 (largura 1,0) para x = 118,3 → bordo em 118,8, sobrepondo a via-in-pad GND do U1.2 (119,0; 53,42; Ø 0,5 → bordo 118,75) — a verificação de colisão era feita antes de adicionar os segmentos. Movido para o 5b como **fase M** (`detour_5v_in1`, x = 117,6, verificação após inserir, rollback) — assim o Freerouting já desvia da nova geometria; M1 do 5c mantém-se como fallback (no-op quando M já foi aplicada).
- DSN: `(clearance 160 (type via_via))` (3 pares `hole_clearance` via↔via do FR). **Não** `wire_pin` 160: o baseline já tem trilhas a 0,10 de pinos PTH → 159 violações fixas e o Freerouting estagnou em 28 não roteados (corrida 26-10 10:06); a trilha +12V In2 do FR a 0,2317 do furo do P1.B7 é afunilada pelo 5c (`fix_track_vs_hole`, ≥ 0,1375). Vias de costura +3V3 do U7 só são aceites dentro do contorno da zona In1 (`_in_3v3_plane`) — evita `via_dangling` (C61.1 em x = 95,5; C59.1 em y = 37,3). Trilhas do FR com largura < 0,1375 (neck-down junto a 0402, ex.: LED_GREEN 0,10 / BLUE- 0,12, apesar de `automatic_neckdown=false`) são alargadas em `widen_thin_tracks` para 0,20/0,16/0,14 sem colisão.
- Resultado da corrida de 26-10 09:23 (antes destes últimos ajustes): `unrouted_final` 0, `unconnected_items` 0. Pendentes herdados do baseline e não tocados: 8 `hole_clearance` P1 PTH/NPTH, `isolated_copper` 1, `drill_out_of_range` 1, `courtyards_overlap` D7/U9, 2 `copper_edge_clearance`, silk/text/lib mismatches (ver `03_RESEARCH\STEP5_layout_H725.md`).
- Status: ATIVA.

## D-30 — Pré-rota travada BUS2_RX, pontes +3V3 sem via nova e micro-segmentos
- Data: 2026-10-26
- Fato: após D-29 as corridas 12/13/14 do pipeline repetiam o mesmo par não ligado: **BUS2_RX U7.123 (B.Cu) ↔ U9.4 (F.Cu)**. O Freerouting fecha o pino 123 entre as faixas BUS2_STB (diagonal + y = 54,74) e BUS0_STB (y = 55,26) em B.Cu (canal ≈ 0,13 mm) e o 5c não consegue rip-up porque são duas redes bloqueadoras (regra de rede única em `blockers`). Em vez de confiar na não-determinação do FR, `step5b_route.py` ganhou a **fase R** (`PREROUTE`/`preroute_pair`): antes do DSN, com a área ainda livre, procura em grelha (passo 0,05, raio ≤ 2,5 mm à volta do pad destino) uma posição de via 0,5/0,3 em que os segmentos B.Cu (pino U7 → via) e F.Cu (via → pad) fiquem sem colisão (`via_collides`/`seg_collides`) e insere-os **travados** — o Freerouting passa a desviar deles.
- Ilha +3V3 em U9.5 (125,8; 56,2): `fix_clusters` não encontrava ponto livre no preenchimento In1 (via 0,6/0,5) a ≤ 5 mm. Fallback novo: trilha directa / em Z / A* em F.Cu ou B.Cu desde a ilha até um item (via, pad, extremo de trilha) do agrupamento principal, a ≤ 6 mm, larguras 0,3 → 0,2 → 0,15, **sem via nova**.
- `track_dangling` de 0,007 mm (+3V3 F.Cu em 106,87; 70,68) criado por uma junção do 5c: no fim do 5c removem-se segmentos com comprimento < 0,02 mm (`micro_segments_removed`).
- Generalização da fase R (corridas 15–19): `PREROUTE` descobre todos os pares U7 `BUS*_TX/RX` ↔ U8–U11 e tenta pré-rotear por ordem de distância (passo 0,1, raio ≤ 2,0 — o passo 0,05/2,5 demorava ≈ 5 min). Só os dois pares de BUS2 (U7.122↔U9.1, U7.123↔U9.4) têm posição de via livre; os outros 6 falham com "sem posição de via livre" e ficam para o Freerouting (nunca falharam nele). O par 123↔4 precisa de saída horizontal do pad LQFP (0,8–1,8 mm) antes da diagonal — a diagonal directa colide com U7.124.
- Curto emitido pelo próprio Freerouting (corrida 15): via BUS1O_RX (101,93; 47,65) a 0,09 mm de uma trilha SBU1_ADC em In2 — `shorting_items` presente já no SES. O 5c ganhou `fix_shorts` (remove via/trilha destravada + stubs; religa na rodada seguinte) e `nshort` entrou na condição de paragem.
- Folga de furo (hole_clearance 0,25) nas verificações de colisão do 5b (`via_collides`) e do 5c (`seg_collides`, A*): necessária porque as trilhas/A* do 5c geravam `hole_clearance` contra vias do FR e `fix_holes` arrancava a via errada (BUS1N_RX, 12 itens). Descoberta: a via-in-pad do U1.2 (119,0; 53,42) fica a **exactamente 0,250 mm** da trilha USB_PWR F.Cu (118,5; 51,7→53,8, w 0,2); `SHAPE::Collide(…, clearance)` é estrito (<) tal como o DRC, portanto a margem tem de ser 0,25 exacto — 0,2501 (corrida 19) rejeitava a via e deixava U1.2 GND não ligado (o fallback de `fix_clusters` também não encontra ponte para um pad isolado entre U7.118/U7.120 e a trilha USB_PWR).
- Limpeza final do 5c: vias destravadas ligadas numa só camada (contando trilhas, pads e preenchimento de zona da mesma rede) são removidas com os seus stubs (`dangling_vias_removed`).
- Resultado: ver `03_RESEARCH\STEP5_layout_H725.md` §7 (corrida final).
- Status: ATIVA.

## D-31 — Esconder a serigrafia das referências dos componentes adicionados no STEP 5 (`step5d_silk.py`)
- Contexto: após o pipeline 5a→5c o DRC acusava 20 `silk_over_copper` + 19 `silk_overlap` novos face ao baseline, todos do texto de referência (0402, passo 0,5–0,65 mm junto ao U7) dos 37 componentes adicionados (C38–C63, D13/D14, FB1, J1, L5, R28–R33) sobre pads/serigrafia vizinhos.
- Alternativas: (a) reposicionar 37 textos manualmente/por script evitando pads — frágil, sem ganho real numa zona densa; (b) esconder a referência (`Reference().SetVisible(False)`) como o baseline já faz para vários 0402 — escolhida. A serigrafia não afecta a electricidade; a identificação fica na BOM/CPL (`07_FABRICATION`).
- Consequência: `silk_over_copper` 20→0, `silk_overlap` 22→4 (3 baseline + 1 nova C23×Y1, cosmética). Total DRC 217→179 (baseline 194). Relatório `06_REPORTS\step5d_silk.json`; a placa final é o snapshot `.step5_final`.
- Status: ATIVA.

## D-32 - Correctores pos-pipeline fix_audit.py / fix_drc_regressions.py (commits anteriores)
- Contexto: apos 5a-5d o `final_audit.py` acusava vias dentro de pads SMD deixadas pelo 5c (estrategia via-in-pad) e faltavam fiduciais; o `fix_audit.py` moveu-as para fora dos pads com stub e adicionou FID1-FID6; o `fix_drc_regressions.py` corrigia as regressoes de DRC com coordenadas fixas da geometria de entao. Ficaram 4 via-in-pad (D13.1, U1.2, C30.2, C33.2) sem posicao livre na zona densa U8/U11/D13/P1.
- Status: SUBSTITUIDA em parte por D-33 (`fix_drc_regressions.py` deixa de ser aplicavel; `fix_audit.py` mantem-se).

## D-33 - Relayout leste (+3 mm) para eliminar as via-in-pad restantes (`step5e_relayout_east.py`)
- Contexto: as 4 via-in-pad de D-32 nao tinham solucao local: mover C30/C33 0,3-0,4 mm criava curtos com BUS0_RX/+5V e remover as vias GND de D13.1/U1.2 deixava os pads sem ligacao. O dono autorizou aumentar a placa ("pode aumentar o tamanho da pcb em si para nao dar conflito", "vamos deixar mais tranquilo ao inves de lotar a placa").
- Decisao: novo passo 5e entre 5a e 5b: Edge.Cuts +3 mm para leste (x_max 139,535 -> 142,535; placa 47,625 x 46,75 -> **50,625 x 46,75 mm**); bloco com x > 123 translada +3 mm (U8/U9/U10/U11, D1/D2/D5-D9, P1 continua flush com a borda, U3, Q4, caps/resistencias associadas, D13 +3,5/+0,3); C30/C31 so +2 mm e Q1/Q2 +2,4 mm (abrem 1 mm entre o U7 e os transceptores); R24 sobe 0,8 mm; C40 (VCAP do U7) nao acompanha. Zonas (+5V F.Cu, USB_PWR, +12V, 12V_Protected, +5V In2) e serigrafia seguem a borda. Trilhas de Q1/Q2/R24/C30/C31 sao desligadas e reroteadas. Fase M do 5b: via GND do U1.2 passa para (121,35; 53,4) com desvio da USB_PWR; `Z3_OUTLINE` ate x = 130. `fix_audit.py`: D7xU9 resolve-se movendo U9 0,25 mm para oeste. Novo `fix_drc_relayout.py` (orientado por uuid do DRC) substitui `fix_drc_regressions.py`. Novo `fix_vip_reroute.py` para a ultima via-in-pad (U8.3 +5V -> via em (123,06; 61,99) na trilha F.Cu a oeste de C30, trilha B.Cu reencaminhada por (125,56; 62,74)).
- Resultado (2026-10-27): 5b 4 nao roteados -> 5c 0; 5d DRC 0/0/178; fix_audit 44 via-in-pad movidas + 6 FID; fix_drc_relayout (via do keepout SW1, via GNDxSWDIO, trilha solta, FID2 -> 140,485; 76,71); 1 unconnected (+3V3: ilha In1 cortada pelas vias movidas) fechado por `step5c --rounds 3` (via +3V3 em 113,125; 50,75); fix_vip_reroute -> **via-in-pad 0**; DRC **0 clearance / 0 unconnected / 182** (starved_thermal 17, resto herdado); step7 `failures` vazio; final_audit ALTO = 8 hole_clearance P1 + BOM sem MPN (herdados), MEDIO = caixas U3/P1 fora do contorno (conectores de borda).
- Limites: as folgas de courtyard < 1 mm dentro do bloco transladado (U8xD6, U9xD7, UxxCyy, Dx x P1) sao as do baseline OpenBlackPanda e nao foram alteradas; so se abriu espaco entre o U7 e o bloco. As caixas STL do baseline ja nao serviam (D-24) e agora a largura tambem muda. Nenhuma verificacao fisica; "nao fabricar" mantem-se.
- Status: ATIVA. Snapshot aceite: `HybridPanda.kicad_pcb.step5_final` (= placa actual).

## D-34 - Campanha de correcao pos-auditoria em passos com gate de DRC (commits a8b98a9 .. final)
- Contexto: as auditorias de footprint (06_REPORTS/footprint_audit), SI/PI (06_REPORTS/si_pi_audit, 36 itens) e BOM (06_REPORTS/bom_real) encontraram erros reais no snapshot `.step5_final` (VFBSMPS separado de VCAP, pads de Q1/Q2/Q3 fora da geometria, R1 1k no gate do Q4, sem ESD no USB, etc.).
- Decisao: aplicar as correcoes por passos (1 footprints, 2 criticos de alimentacao, 3 ALTO, 4 BOM, 5 MEDIO, final) com scripts idempotentes `05_SCRIPTS/corr_step*.py` e um gate unico `05_SCRIPTS/corr_gate.py` (kicad-cli DRC JSON apos cada edicao; aceite = 0 clearance / 0 unconnected / 0 paridade e nenhuma categoria de erro nova face ao baseline). Esquema e PCB alterados em conjunto. Item que falhe o gate e revertido e registado como deferido, nunca forcado.
- Resultado: DRC 182 -> 135 (0/0/0), ERC 0, via-in-pad 0, step7 sem falhas. Tabela completa em `06_REPORTS/CORRECOES_APLICADAS.md`.
- Status: ATIVA. O snapshot `.step5_final` deixa de ser a placa aceite; a placa aceite e o HEAD de main.

## D-35 - VFBSMPS unido a VCAP (topologia Direct SMPS, AN5419) e PF9 em jumper JP1
- Contexto: o esquema tinha VFBSMPS e VCAP como redes distintas; em Direct SMPS o pino 17 (VFBSMPS) tem de ligar ao no VCAP (DS13311 ?6.3.3 / AN5419 fig. 5). PF7-PF10 estavam todos a GND, o que fixa HW_TYPE RED sem possibilidade de distinguir a placa hibrida.
- Decisao: renomear os labels VFBSMPS para VCAP; C64 2.2 uF 0402 junto a U7.103 (0603 nao cabe) e C65 4.7 uF 0603 junto a VDDSMPS U7.16; PF9 passa a JP1 (SolderJumper_2_Open): fechado = RED (id1 = 0), aberto = HYBRID (id1 = 4) - decisao de firmware fica em aberto, por defeito fechado.
- Status: ATIVA (commit a5d60b8).

## D-36 - Desvios aceites face a proposed_changes.md
- Item 6: Cin do TPS5450 10 uF em 0805 50 V X5R (1206 nao cabe sem mover L4/C6/C7); derating DC registado.
- Item 30: anel anular minimo 0.125 mm (nao 0.13): os PTH do footprint TYPE-C-31-M-04 do P1 tem anel 0.125 e nao podem ser alterados sem trocar o footprint.
- Item 20/17: 12V_Protected e VCAP mantem um trecho em In1 (0.35/0.3 mm) porque remove-lo deixa redes abertas; so In2 ficou livre de +12V/12V_Protected.
- Item 26: 9 segmentos CAN ficam em 0.15 mm (borda da placa junto a BUS1N_H e entrada do P1).
- Item 32: hole_clearance do P1 (8) aceite como desvio herdado; deslocar os PTH 0.15 mm cria curto com BUS0_H/SBU2.
- Item 15: 5 vias termicas no EP do U6 em vez de 8 (SWDIO em In2 passa por baixo da fila inferior). final_audit.py passa a distinguir via termica (mesma rede, pad >= 2 mm) de via-in-pad.
- Status: ATIVA.

## D-37 - Itens deferidos por exigirem relayout (nao aplicar sem nova sessao de floorplan)
- 9 (funcao do D10), 10 (100 nF opcionais), 16 (no SW do TPS5450), 21/22/23 (C41/C42/C38/U5 junto ao U7), 25 (D8/D5 junto ao P1), 27 (In2 so GND), 29 pad 69 (via-in-pad em U12.6), 34 (D1 junto ao P1), 36 (polimero 7343), C8 0603, U1 TPS2553.
- Motivo comum: cada um exige mover blocos de componentes e rerotear redes com o Freerouting (nao deterministico) ou decisao do dono; nenhum e bloqueante para o DRC. Lista com razoes em `06_REPORTS/CORRECOES_APLICADAS.md` ?5.
- Status: ATIVA (em aberto).

## D-38 - BOM com MPN/LCSC no esquema, codigos "a verificar"
- Contexto: step8_fabricate.py exporta BOM_JLC.csv a partir dos campos MPN/LCSC do esquema; antes estavam vazios.
- Decisao: campos MPN/LCSC preenchidos no `.kicad_sch` (commit 9305ef2) a partir de `06_REPORTS/bom_real/BOM_HYBRIDPANDA_v1.csv`; 117/119 referencias com LCSC (JP1 e U1 sem). Nenhum codigo foi confirmado no catalogo JLC em sessao - todos "a verificar" antes de encomendar; C23/C24 18 pF: C1555 nao confirmado (alternativa CL05C180JB5NNNC C307443).
- Status: ATIVA.
