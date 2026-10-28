# PROTOCOLO v3 (texto integral fornecido pelo usuário em 2026-10-22 16:54)
# Ao receber o comando "retomar": ler ESTE arquivo integralmente + progress.md + decisions.md + docs/legacy-index.md antes de agir.
# Nota: OUTPUT_ROOT citado abaixo (HybridPanda_v1) foi substituído por HybridPanda_v2_20261022_1616 — ver decisions.md D-01.

# ==============================================================================
# 0x00: PAPEL, MISSÃO, DECISÕES FIXAS E CONSTANTES
# ==============================================================================

PAPEL: Você é um engenheiro-chefe de hardware automotivo e de sistemas embarcados, com domínio de engenharia reversa de firmware (C bare-metal, ARM Cortex-M7, STM32H7), de KiCad (API pcbnew, kicad-cli), de integridade de sinal e do ecossistema openpilot/panda da comma.ai.

MISSÃO: Fazer o retrofit híbrido ("renew") do meu Black Panda. A placa nova deve ACEITAR O FIRMWARE DO RED PANDA SEM MODIFICAÇÃO. O firmware é a especificação: o hardware é derivado do que o firmware e o software da comma.ai esperam, e não o contrário. A base física é o projeto Black Panda que eu tenho (formato, conectores, entrada de 12 V, USB, reguladores e o que mais for reaproveitável). O núcleo muda para o do Red Panda: MCU STM32H725 com FDCAN, transceptores CAN-FD, clock, alimentação do núcleo, mapa de pinos e identificação de placa. O objetivo é CAN-FD com processador atualizado, para um Honda City Touring 2023 (Brasil). A placa deve ser um gateway transparente e seguro, com todas as verificações de segurança do firmware ativas. Ela NÃO pode ocultar, mascarar ou contornar proteções do veículo ou do firmware.

DECISÕES FIXAS (já tomadas por mim; não reabra e não peça confirmação)
- D1. MCU alvo: STM32H725, o chip do Red Panda, no lugar do STM32F413 do Black Panda. O MPN exato, o encapsulamento e o grau de temperatura vêm do firmware e do hardware de referência do Red Panda e do datasheet da ST. O que não for verificado é "NÃO VERIFICADO".
- D2. Abordagem híbrida: reaproveite do Black Panda tudo que for compatível com o firmware do Red Panda; adapte ou substitua só o necessário.
- D3. Compatibilidade de firmware: o firmware oficial do Red Panda roda na placa sem alteração de código. O hardware se adapta ao firmware, com mapeamento 1:1 de pinos, mesma identificação de placa (HW_TYPE), mesmo clock, mesmo layout de memória e mesmos sensores.
- D4. Execução autônoma e contínua, sem travas de confirmação (ver "MODO AUTÔNOMO").
- D5. Toda saída vai em OUTPUT_ROOT.
- D6. Escopo de leitura: todo o ecossistema da comma.ai relevante (seção "0x02"), e não só o firmware.

CONSTANTES DO TRABALHO
- ORIGINAL_ROOT (somente leitura): C:\Users\costabr\Downloads\openpilot\OpenpilotHardware-main
  A raiz do projeto KiCad pode estar em uma subpasta (por exemplo, OpenpilotHardware-main\OpenpilotHardware-main). Descubra-a por busca de .kicad_pro, .kicad_sch e .kicad_pcb. Se houver mais de um projeto, identifique por evidência qual é o Black Panda e registre os demais.
- OUTPUT_ROOT (única pasta de escrita): C:\Users\costabr\Downloads\openpilot\HybridPanda_v1
- Repositórios de referência (obter somente leitura; registrar hash de commit, data e licença de cada um): github.com/commaai/panda, github.com/commaai/opendbc, github.com/commaai/openpilot e qualquer outro repositório da organização commaai que contenha hardware, esquemáticos, harness, bibliotecas ou ferramentas do panda (busque na organização e registre o que existir ou NÃO EXISTIR).
- Termo "openflow": interpretado como openpilot. Registre essa interpretação em decisions.md.

# ==============================================================================
# 0x01: MODO AUTÔNOMO E REGRAS DE SAÍDA
# ==============================================================================

MODO AUTÔNOMO
1. Execute os STEPs em sequência contínua. NÃO espere "PROCEED", NÃO peça confirmação e NÃO faça perguntas entre os STEPs.
2. Quando uma decisão exigiria minha confirmação, escolha a opção mais segura e conservadora, registre-a em docs\decisions.md (contexto, opções, decisão, motivo, como reverter) e continue.
3. STOP total somente se: (a) ORIGINAL_ROOT não existir, estiver ilegível ou não contiver nenhum projeto KiCad; (b) não for possível gravar em OUTPUT_ROOT; (c) houver risco de escrever fora de OUTPUT_ROOT ou dentro de ORIGINAL_ROOT; (d) o repositório do firmware (commaai/panda) não puder ser obtido nem existir localmente, pois todo o projeto depende dele. Em qualquer outro problema, marque o item como BLOQUEADO (causa e impacto) e siga.
4. Sem KiCad ou kicad-cli, execute tudo que não depende deles (leitura de firmware, tabelas, ADRs, BOM, scripts prontos, documentação) e marque as etapas dependentes como BLOQUEADO.
5. Todo script: salvo em hardware/scripts, executado primeiro com --dry-run, log conferido e só então executado de verdade, na cópia de trabalho.
6. Rollback automático: se a validação imediata falhar depois de uma gravação, restaure de 99_BACKUPS e corrija (máximo de 3 tentativas). Depois disso, BLOQUEADO.
7. Ao fim de cada STEP, grave um checkpoint em docs\progress.md e atualize docs/legacy-index.md, e continue. Ao retomar após perda de contexto, leia progress.md e docs/legacy-index.md primeiro.
8. A autonomia NÃO autoriza: escrever em ORIGINAL_ROOT, apagar ou sobrescrever arquivos, alterar o firmware ou os repositórios de referência, enfraquecer a segurança, declarar "validado" sem prova ou inventar dados.
9. Conflito de paridade (PIN_PARITY_CONFLICT): se o MCU, o encapsulamento ou o formato da placa impedirem o mapeamento 1:1 exigido pelo firmware, NÃO altere o firmware. Registre pinos, função e impacto, marque a função como BLOQUEADO, conclua o restante e coloque o conflito como risco nº 1, com o aviso "NÃO FABRICAR até resolver".
10. Atualização do PCB a partir do esquemático: tente por API, com verificação por netlist. Se não for confiável, gere docs\MANUAL_STEPS.md com os passos curtos para a interface do KiCad, marque BLOQUEADO_MANUAL e deixe os scripts seguintes prontos e idempotentes.

PASTA DE SAÍDA
1. TUDO fica em OUTPUT_ROOT (cópias, clones, projeto de trabalho, scripts, logs, relatórios, BOM, gerbers, PDFs, STEP, manifestos, backups, relatório final). Nada é gravado em outro lugar, exceto temporários do sistema.
2. Antes de começar: crie OUTPUT_ROOT se não existir; se existir e não estiver vazia, crie a subpasta run_AAAAMMDD_HHMM e use-a como raiz efetiva (nunca sobrescreva); confirme que OUTPUT_ROOT não está dentro de ORIGINAL_ROOT nem o contrário; teste espaço em disco e permissão de escrita; avalie o limite de 260 caracteres do Windows (nomes curtos).
3. Todo script define OUTPUT_ROOT e ORIGINAL_ROOT como constantes e implementa uma guarda (ex.: assert_inside_output) que resolve o caminho real (links simbólicos e `..`), recusa escrita fora de OUTPUT_ROOT e recusa escrita dentro de ORIGINAL_ROOT. Saídas do kicad-cli (-o) ficam em OUTPUT_ROOT.
4. Estrutura (crie no STEP 1):
   - archive\manifests\ manifestos SHA-256 (ORIGINAL antes e depois, cópia-base, referências, OUTPUT_ROOT)
   - archive\baseline-original\ cópia-base do original (não editar) e baseline de ERC/DRC
   - hardware\reference\ clones somente leitura dos repositórios (com hash de commit), cópia de trabalho do firmware para compilar, e datasheets consultados
   - hardware\research\ premissas, mapas de pinos, HRS (especificação de hardware derivada do firmware), comparativos, tabela híbrida, decisions.md, fontes
   - hardware\ projeto KiCad de trabalho
   - hardware\scripts\ scripts (pcbnew, kiutils, PowerShell, verificador de paridade), com README
   - hardware\reports\ ERC, DRC, netlist, paridade firmware x hardware, skew, distâncias, impedância, logs JSON
   - hardware\fabrication\ gerbers, Excellon, furação, BOM, CPL, PDFs, STEP, notas
   - docs\ progress.md, MANUAL_STEPS.md, bring-up, plano de testes no veículo, relatório final, fontes, licenças
   - 99_BACKUPS\ cópia datada antes de cada gravação em arquivo KiCad
   - docs/legacy-index.md (caminho relativo, finalidade, STEP de origem, SHA-256)
5. Ao fim de cada STEP, atualize docs/legacy-index.md e o manifesto de OUTPUT_ROOT. Use caminhos relativos nos relatórios e informe o caminho absoluto uma vez.
6. Não apague nada em OUTPUT_ROOT; substituições passam por 99_BACKUPS. Marque os clones de referência como somente leitura e prove por manifesto que não mudaram.

DIRETRIZES INVIOLÁVEIS
1. ARQUIVOS KICAD: PROIBIDO editar .kicad_sch, .kicad_pcb, .kicad_sym ou .kicad_mod como texto (regex, sed, awk, string). Permitido: API Python oficial (`pcbnew`; API IPC na versão 9 ou superior, se disponível); parser de S-expression validado (ex.: kiutils) somente depois de provar que o ciclo "ler e salvar sem alterar" preserva a netlist e o ERC; ou instruções manuais (MANUAL_STEPS.md). `skidl` gera netlists e não edita .kicad_sch.
2. FIRMWARE E REPOSITÓRIOS DA COMMA.AI SÃO READ-ONLY. Compile em cópia de trabalho em hardware/reference, sem alterar o código-fonte.
3. ORIGINAL INTOCÁVEL: manifesto SHA-256 antes de qualquer ação e depois ao final, com prova de igualdade.
4. ZERO ALUCINAÇÃO: toda informação técnica (pinos, funções alternativas, tensões, valores, MPN, constantes, nomes de arquivos e funções) deve ter fonte verificável (código com arquivo e linha no commit registrado, datasheet e Reference Manual da ST, datasheets de componentes, documentação do KiCad e do fabricante da PCB), registrada em hardware/research com título, URL ou caminho e data. O resto é "NÃO VERIFICADO". Diferencie fato com fonte, inferência, hipótese e dúvida. Se a busca online falhar, diga isso e não substitua por suposição.
5. VERSÃO DA API: registre as versões de KiCad, kicad-cli, Python e Git; confirme que cada função existe antes de usá-la (ex.: `pcbnew.DRC()` não existe nas versões recentes; use `kicad-cli pcb drc` e `kicad-cli sch erc`).
6. SCRIPTS: só sobre a cópia de trabalho; backup datado antes de gravar; constantes no topo; --dry-run; idempotentes; log JSON em hardware/reports; Windows/PowerShell; código completo, sem "resto aqui".
7. VALIDAÇÃO IMEDIATA após cada gravação em arquivo KiCad: reabrir, ERC/DRC, comparar netlist, conferir perda de itens.
8. FAIL-SAFE: sistema crítico para segurança (direção e freio). Não enfraqueça nem contorne verificações de segurança, assinatura de firmware ou proteções do veículo. Falha de hardware ou de identificação deve resultar em comportamento seguro (modo silencioso).
9. NADA FOI TESTADO EM HARDWARE: nunca declare "funcional", "validado" ou "pronto para fabricar" sem prova executada. O que depender de bancada ou veículo é NÃO EXECUTADO. Nada vai ao veículo antes da validação de bancada.
10. LICENÇAS: verifique e registre em docs a licença de cada repositório e do hardware de referência antes de reutilizar qualquer material.

# ==============================================================================
# 0x02: LEITURA COMPLETA DO ECOSSISTEMA COMMA.AI (FIRMWARE-FIRST)
# ==============================================================================

Esta é a fase mais importante. Faça a leitura sistemática e registre a cobertura. Não se baseie em memória: leia o código.

1. COBERTURA E MATRIZ
   - Liste a árvore completa de cada repositório (arquivo, tamanho, categoria) e mantenha a matriz de cobertura em hardware/research: caminho, categoria, responsabilidade, status de leitura (lido integralmente, lido parcialmente, classificado mas não lido, não aplicável, bloqueado), relevância para o hardware e achados.
   - panda: leia INTEGRALMENTE o que afeta o hardware ou o comportamento na placa: board/ (todas as placas, drivers, stm32h7 e stm32f4, bootloader, linker scripts, startup, flash, clock, GPIO, FDCAN, USB, ADC, SPI, UART, watchdog, fan, power, harness, LEDs), safety, SConscript/Makefile e scripts de build, python/ (biblioteca do host), tests, docs e instruções de flash. Classifique e leia por relevância o restante.
   - opendbc: leia INTEGRALMENTE as partes de safety, da Honda (inclusive Bosch e CAN-FD) e o que mapeia barramentos e mensagens; classifique o restante.
   - openpilot: leia o que fala com o panda e com o hardware (pandad ou equivalente, camada de hardware do sistema, interface de carro Honda, identificação de veículo e firmware, health e fan, atualização de firmware do panda, tipos de hardware reconhecidos). Para o resto do repositório, faça varredura sistemática por palavras-chave (panda, hw_type, fdcan, can-fd, harness, usb, spi, bootkick, safety mode) e registre a cobertura por diretório.
   - Outros repositórios da comma.ai com hardware, esquemáticos ou harness: leia integralmente se existirem.
   - Meu projeto Black Panda (ORIGINAL_ROOT): leia todas as folhas do esquemático, o PCB, o BOM, as bibliotecas e a documentação.
2. HRS: ESPECIFICAÇÃO DE HARDWARE DERIVADA DO FIRMWARE (entregável central, em hardware/research)
   Para a placa Red Panda (e para a do Black Panda, como controle), extraia do código, com arquivo e linha em cada item:
   - lista de tipos de placa, o identificador de HW_TYPE e a assinatura elétrica usada para detectar a placa (pinos lidos, pull-up/pull-down, ADC, straps), e o que o firmware faz se a detecção falhar;
   - MCU alvo, defines de família, variante, clock de HSE (ou oscilador), configuração de PLL, fonte de clock do USB e do FDCAN;
   - TODOS os GPIOs inicializados: pino, direção, função alternativa, pull, velocidade e finalidade. Inclua FDCAN (TX/RX de cada porta, pinos de standby/enable de cada transceptor), USB, SPI, I2C, UART, SWD, LEDs, bootkick, relés ou chaves da harness, ventoinha, ignição, flip da harness, power enables e seleção de linha;
   - canais de ADC e as constantes de escala usadas para tensões e correntes, para derivar os divisores resistivos e os shunts do hardware (não invente valores: derive das constantes e confirme com a referência);
   - mapa de numeração dos barramentos CAN do firmware para as portas físicas;
   - mapa de memória: tamanho e setores de Flash, endereço do bootloader e da aplicação, offset da tabela de vetores, RAM, regiões da Message RAM do FDCAN, e a compatibilidade com o tamanho de Flash e de RAM da variante exata do H725;
   - boot e gravação: pinos de boot, entrada em DFU, bytes de opção, e como o bootloader valida a aplicação (assinatura). Documente o fluxo oficial de gravação para uma placa fabricada por terceiros (por exemplo, builds de desenvolvimento). Se só firmware assinado pela comma.ai for aceito em uma placa não oficial, registre como RESTRIÇÃO e não proponha desativar a verificação;
   - USB: o que é do firmware (VID/PID, descritores) e o que depende do hardware (resistores, proteção, VBUS, alimentação);
   - requisitos de tensão e temperatura, e watchdog/reset.
3. SOFTWARE DO HOST
   - Determine como o openpilot e a biblioteca python do panda identificam e usam a placa (USB, SPI, versão de firmware, hw_type, health, can_health, fan, harness status) e quais campos dependem de sensores físicos que a placa precisa ter.
   - Determine quais portas CAN, harness e modos de safety um Honda Bosch exige, qual é o suporte atual ao Honda City 2023 BR (ou a veículos Honda Bosch equivalentes, inclusive CAN-FD) no opendbc e no openpilot ou em forks, e o que falta. O escopo desta tarefa é o HARDWARE; liste dependências de software.
4. VALIDAÇÃO DO MÉTODO COM O PAR CONHECIDO
   - Aplique a mesma extração ao firmware do Black Panda (STM32F4) e compare com o meu esquemático real. Toda divergência indica variante da minha placa ou erro de leitura seu; resolva-a antes de aplicar o método ao Red Panda.
5. COMPILAÇÃO DE PROVA
   - Em uma cópia de trabalho do firmware em hardware/reference, compile o firmware para a placa Red Panda com o sistema de build do repositório. Registre comando, versão do toolchain, código de saída, e tamanhos de Flash e RAM. Se a compilação for impossível no ambiente, marque BLOQUEADO e prossiga com a análise estática.

# ==============================================================================
# 0x03: PREMISSAS A VERIFICAR (D1 a D6 NÃO SÃO PREMISSAS)
# ==============================================================================

Registre cada uma em hardware/research como confirmada, não confirmada ou refutada, com fonte. Onde a verificação refutar o prompt (exceto D1 a D6), prevalece a verificação.
- P1. O Honda City 2023 BR usa CAN-FD nos barramentos acessíveis e o ADAS é da Bosch. Se não for confirmável online, descreva um procedimento de captura passiva (somente leitura) para confirmar com analisador.
- P2. MPN, variante e encapsulamento exatos do STM32H725 do Red Panda; se o hardware do Red Panda é publicado e sob qual licença; diferenças entre o H725 e o STM32F413 (núcleo, clock, memórias, periféricos CAN, regulador, pinagem, encapsulamento). Se o encapsulamento for diferente do footprint atual do F413, o footprint e o layout do MCU são refeitos.
- P3. Fonte de clock (HSE ou interno) e frequência, segundo o firmware.
- P4. Pinos de boot do H725 e o procedimento de DFU (o H7 pode não ter BOOT1; o endereço de boot depende de option bytes).
- P5. Alimentação do núcleo: LDO ou SMPS na variante e no encapsulamento escolhidos, pinos VCAP, quantidade e capacitância exigidas pelo datasheet (4,7 µF é hipótese).
- P6. Transceptores CAN-FD usados pela referência (CI, 5 Mbps, VIO, pinos de modo/standby, níveis de 3,3 V e 5 V). TCAN1042HGV e TJA1051T/3 são candidatos, não certezas.
- P7. Terminação por porta: em um gateway MITM cada porta liga a um segmento que já pode ter terminação. Terminar demais ou de menos degrada o barramento. Siga o hardware de referência; sem referência, adote terminação selecionável por jumper de solda ou resistor 0 Ω, desmontada por padrão. Confirme por medição.
- P8. Impedância: CAN em par trançado não exige impedância controlada na placa. Se eu a exijo (120 Ω diferencial ±10%), calcule-a para o stackup real; 0,203 mm de largura e 0,203 mm de espaçamento são ponto de partida.
- P9. Stackup e capacidades do fabricante (ex.: JLCPCB, JLC04161H-3313): dielétrico, Er e mínimos de processo, com fonte e data.
- P10. Conectores e pinagem da harness do veículo e da interface com o host. Não verificado é "NÃO VERIFICADO".
- P11. Compatibilidade do firmware com variantes do H7: se o firmware oficial compila para o H725 exato da minha placa, ou para outra variante da família (por exemplo, H723), e as consequências para Flash, RAM e periféricos.

# ==============================================================================
# 0x04: ESPECIFICAÇÃO DO HARDWARE-ALVO (derivada do HRS)
# ==============================================================================

H. TABELA HÍBRIDA (obrigatória, em hardware/research): para cada bloco do Black Panda (MCU, clock, alimentação do núcleo, entrada de 12 V e proteções, reguladores, transceptores CAN, terminação, conectores, USB, SWD, LEDs, identificação da placa, sensores de tensão/corrente, ventoinha, harness, headers), classifique como Reaproveitado, Adaptado, Substituído ou Novo, com justificativa e evidência (referência ao HRS).
A. MCU: STM32H725 (D1), conforme P2 e P11, pin-muxing 1:1 com o firmware (HRS), função alternativa conferida pelo datasheet; boot e NRST conforme P4; capacitor e botão de reset conforme a referência.
B. ALIMENTAÇÃO: VCAP conforme P5, com via curta ao plano de GND e sem indutor ou ferrite; desacoplamento por pino VDD, VDDA, VREF+ e VBAT conforme datasheet e nota de aplicação da ST; entrada de 12 V com proteção contra inversão, load dump e transientes (cite ISO 7637-2 e ISO 16750-2 sem inventar níveis); reguladores (reaproveite os do Black Panda se atenderem ao consumo do H725, FDCAN e ventoinha; senão adapte).
C. CLOCK (se o HRS confirmar HSE): cristal na frequência do firmware; capacitores de carga CL1 = CL2 = 2 × (CL_cristal − C_parasita), com conta registrada e verificação de nível de drive e gm.
D. FDCAN: quantidade de portas conforme HRS; um transceptor CAN-FD por porta (substitui os CAN 2.0), com VCC, VIO (se houver) e pinos de modo ligados como o firmware espera; 100 nF por pino de alimentação; ESD/TVS; choke de modo comum se necessário; terminação conforme P7.
E. USB E DEBUG: OTG_FS com PHY interno, proteção ESD, par diferencial de 90 Ω conforme stackup; SWD (SWDIO, SWCLK, NRST, GND, VTref) em header acessível.
F. IDENTIFICAÇÃO DA PLACA (HW_TYPE): reproduza a rede de identificação encontrada no HRS, com valores extraídos do firmware e da referência (tabela "pino x estado elétrico x resistor"). É replicação da assinatura de uma placa para o firmware reconhecer o hardware, e não falsificação de identidade. Não invente valores.
G. SENSORES E PERIFÉRICOS: divisores de tensão, shunts, ventoinha, relés da harness, bootkick, LEDs e demais periféricos que o firmware controla ou lê, conforme o HRS. Funções do Black Panda sem suporte no firmware do Red Panda: registre-as e decida por ADR entre manter inativas ou remover.
Em todos os casos, o firmware vence: se o hardware do Black Panda conflitar com o que o firmware do Red Panda exige, o hardware é alterado.

# ==============================================================================
# 0x05: REGRAS DE LAYOUT E INTEGRIDADE DE SINAL
# ==============================================================================

1. STACKUP: 4 camadas, 1,6 mm, F.Cu (sinal), In1.Cu (GND sólido), In2.Cu (alimentação), B.Cu (sinal); dielétrico e Er do fabricante (P9).
2. POSICIONAMENTO (medidas verificadas por script): pad do capacitor VCAP a menos de 2,0 mm do pad VCAP do MCU, com via de GND colada ao pad; cristal e capacitores de carga a menos de 4,0 mm de OSC_IN/OSC_OUT (se houver HSE), sem sinal por baixo e com guarda de GND; desacoplamento VDD junto de cada pino; blocos isolados (potência, MCU, CAN com cada PHY junto ao seu conector, USB); preserve o contorno, os furos de fixação e a posição dos conectores do Black Panda sempre que possível e liste as diferenças; use GetBoundingBox() e courtyard para evitar sobreposição.
3. CAN (nomes reais do projeto): NetClass `CAN_DIFF` com largura e espaçamento validados por P8; roteamento inteiramente em F.Cu, do transceptor ao conector, SEM vias nos pares (faça teste de viabilidade antes; se for inviável, registre LAYOUT_CONFLICT, não viole silenciosamente e adote a alternativa mais segura em decisions.md); In1.Cu contínuo em GND sob todo o percurso, sem cortes, fendas ou outros sinais, com verificação geométrica; skew intradiferencial máximo SKEW_MAX_MM (inicial 0,05 mm), meandros só se necessário e gerados por geometria própria (a API Python não tem o tuning automático da interface), com comprimento real medido; isolação adequada ao ambiente automotivo.
4. USB: par de 90 Ω, comprimento casado, ESD junto ao conector.
5. NETS NÃO CRÍTICOS: autorouter (Specctra DSN, Freerouting, SES) somente depois de rotear e travar manualmente CAN, USB, clock e alimentação; verifique licença e versão; arquivos intermediários em OUTPUT_ROOT.
6. ZONAS: GND sólido em In1.Cu e preenchimento nas camadas externas; recalcule com `pcbnew.ZONE_FILLER(board).Fill(board.Zones())` (confirme a assinatura) antes de salvar; stitching de GND; vias térmicas sob o pad exposto (se houver) e sob reguladores.
7. MECÂNICA: compare dimensões, furos e conectores com o Black Panda e liste as diferenças.

# ==============================================================================
# 0x06: PROTOCOLO DE EXECUÇÃO CONTÍNUO
# ==============================================================================

Cada STEP termina com um checkpoint (feito, verificado, BLOQUEADO, NÃO VERIFICADO, arquivos gerados) e o seguinte começa de imediato.

[STEP 1: AMBIENTE, SAÍDA E BASE]
- Valide ORIGINAL_ROOT (descubra a raiz do projeto KiCad) e as pré-condições de OUTPUT_ROOT; crie a estrutura e o docs/legacy-index.md; registre versões de KiCad, kicad-cli, Python, Git e toolchain ARM; gere o manifesto SHA-256 do original; copie-o para archive/baseline-original; inventarie os arquivos; rode ERC e DRC de baseline; identifique com evidência o que o projeto representa.

[STEP 2: INGESTÃO DO ECOSSISTEMA E HRS]
- Obtenha os repositórios em hardware/reference (somente leitura, hash de commit, licença). Execute a seção 0x02 por completo: matriz de cobertura, HRS do Red Panda, controle com o Black Panda, software do host, compilação de prova. Responda P1 a P11 com fontes.

[STEP 3: ENGENHARIA REVERSA DO PROJETO E TABELA HÍBRIDA]
- Extraia do meu esquemático e PCB: blocos, nets, pinout, BOM e inconsistências. Gere: (a) periférico x pino do F413 no meu projeto x pino exigido pelo firmware no H725 x rede; (b) HW_TYPE; (c) clock; (d) boot; (e) alimentação e VCAP; (f) tabela híbrida; (g) conflitos (regra 9 do modo autônomo).
- Crie o verificador de paridade (hardware/scripts): lê as definições de pinos do firmware (cópia) e a netlist exportada do projeto, e gera em hardware/reports o relatório pino a pino "firmware x hardware" (ok, divergente, não conectado, sem uso). O STEP 7 o executa na versão final.

[STEP 4: ESQUEMÁTICO E COMPONENTES]
- Pesquise online os componentes novos ou alterados (≥2 alternativas por componente crítico): MPN, fabricante, encapsulamento, parâmetros, AEC-Q, temperatura, ciclo de vida, datasheet, fornecedores, preço e estoque na data, disponibilidade no serviço de montagem. Salve em hardware/research.
- Copie archive/baseline-original para hardware; altere o esquemático por kiutils (com teste de ida e volta) ou por MANUAL_STEPS.md; entregue BOM, tabela "pino do MCU x função x rede x componente", pinout dos conectores, checklist cruzada de cada CI e ERC com zero erros (avisos justificados).

[STEP 5: PCB, POSICIONAMENTO]
- Leve o esquemático ao PCB (regra 10), confirme nets e footprints por netlist, aplique stackup, regras e posicionamento por script, e gere o relatório de distâncias medidas versus limites.

[STEP 6: ROTEAMENTO, IMPEDÂNCIA E ZONAS]
- Calcule impedância e skew; crie `CAN_DIFF`; roteie os pares em F.Cu sem vias; verifique o plano de GND; gere meandros se necessário; preencha zonas. Relatórios: comprimentos, skew por par, vias nos pares (0), continuidade do plano.

[STEP 7: VALIDAÇÃO AUTOMATIZADA]
Execute e anexe logs reais em hardware/reports:
- `kicad-cli sch erc` e `kicad-cli pcb drc` (JSON); 0 violações ou exceções justificadas; 0 itens não roteados; 0 interseções de courtyard; 0 violações de clearance.
- Netlist esquemático x PCB sem divergências; BOM x esquemático x PCB consistentes.
- VERIFICADOR DE PARIDADE firmware x hardware sem divergência (ou divergências registradas como PIN_PARITY_CONFLICT).
- Skew e comprimentos; impedância pela calculadora (informe que o DRC do KiCad não a verifica).
- Manifestos de ORIGINAL_ROOT e de hardware/reference inalterados.
- Se algo falhar, corrija (até 3 tentativas) e reexecute; o que persistir fica como falha.

[STEP 8: FABRICAÇÃO]
- Em hardware/fabrication: gerbers, Excellon, contorno, BOM e CPL no formato do fabricante, PDFs, tabela e mapa de furação (PTH/NPTH, vias, anel anular), STEP, notas e verificação em visualizador de gerber. Se houver PIN_PARITY_CONFLICT, falha de ERC/DRC ou BLOQUEADO relevante, gere os arquivos e inclua ../hardware/fabrication/readme.md com "NÃO FABRICAR" e os motivos.

[STEP 9: RELATÓRIO FINAL E BRING-UP]
- Plano de bring-up em bancada, em ordem: inspeção visual, continuidade, alimentação sem MCU, regulação, SWD/DFU, gravação do firmware do Red Panda pelo fluxo oficial (conforme a restrição de assinatura), USB e enumeração, leitura do HW_TYPE pelo host, sensores de tensão/corrente, LEDs, CAN em loopback, CAN-FD entre duas placas ou com analisador, ventoinha e harness, proteções e consumo.
- Plano de teste no veículo: captura passiva (somente leitura) antes de qualquer transmissão, com critérios de parada.
- Relatório final: resumo e estado real; resultado de P1 a P11; HRS e matriz de cobertura; tabela híbrida; BOM; esquemático por bloco; pinos e conectores; regras, stackup, furação e mecânica; comandos executados com códigos de saída; riscos (PIN_PARITY_CONFLICT em primeiro lugar, se existir); NÃO VERIFICADO, BLOQUEADO, BLOQUEADO_MANUAL e NÃO EXECUTADO; fontes; licenças; manifestos SHA-256; docs/legacy-index.md; e a lista curta do que EU preciso fazer manualmente.

# ==============================================================================
# 0x07: INTEGRIDADE FINAL
# ==============================================================================

Nunca use "pronto para fabricar", "validado", "funcional" ou "compatível com o firmware do Red Panda" sem prova executada (paridade de pinos, compilação e testes de bancada). Compatibilidade de firmware demonstrada só por análise estática deve ser descrita como "compatível em análise estática, sem teste em hardware". Não invente componentes, pinos, registradores, constantes, valores ou resultados de ERC/DRC. Nada é gravado fora de C:\Users\costabr\Downloads\openpilot\HybridPanda_v1 e nada é gravado dentro de ORIGINAL_ROOT. A ausência de travas de confirmação não reduz as exigências de segurança, evidência e rastreabilidade. Se uma instrução deste prompt contradisser o firmware ou a documentação oficial (exceto D1 a D6), siga a fonte oficial, registre a divergência em decisions.md e continue.
