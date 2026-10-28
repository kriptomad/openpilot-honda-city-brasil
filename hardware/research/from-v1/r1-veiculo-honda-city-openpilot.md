Tenho evidências suficientes e primárias para compilar o relatório completo. Não preciso de mais buscas.

---

# Relatório: Honda City 2023 (BR) e viabilidade de hardware openpilot/panda

**Data de acesso de todas as fontes: 22/10/2026**

## Sumário executivo

A premissa de que o Honda City 2023 (mercado brasileiro, plataforma GN, Honda Sensing com câmera Bosch) "exige CAN‑FD" é **REFUTADA**. Evidência de fonte primária (código‑fonte oficial `commaai/opendbc`) mostra que o City 2023 BR é tratado como um Honda Bosch **"radarless" em CAN clássico (2.0B)**, usando o mesmo DBC e a mesma flag de outros modelos Bosch radarless (Civic 2022‑26, HR‑V 2023‑27, Prelude 2026), e **não** a flag/classe reservada para veículos CAN‑FD (que no catálogo atual da Honda são apenas Accord 2023‑25/Hybrid 2023‑26, CR‑V 2023‑26/Hybrid, Pilot 2023‑25/2026 MMR, Passport 2026, Acura MDX 2025‑26 MMR e Acura TLX 2025 MMR). Além disso, o Honda City (Brasil) já está **oficialmente suportado** pelo openpilot/opendbc desde a release `opendbc` 0.3.0, com harness definido ("Honda Bosch B"), DBC e fingerprint publicados.

---

## 1. Arquitetura CAN do Honda City 2023 BR e a questão CAN‑FD

### 1.1 Classificação de hardware no código oficial (CONFIRMADO)

No arquivo `opendbc/car/honda/values.py` (ramo `master`, consultado via commit `c3955753ae7258412814e2cdca3ee8af979e4679`), o Honda City 2023 é declarado assim:

```python
HONDA_CITY_7G = HondaBoschPlatformConfig(
  [HondaCarDocs("Honda City (Brazil only) 2023", "All")],
  CarSpecs(wheelbase=2.6, steerRatio=19.0, centerToFrontRatio=0.41, minSteerSpeed=23. * CV.KPH_TO_MS),
  {Bus.pt: 'honda_bosch_radarless_generated'},
  flags=HondaFlags.BOSCH_RADARLESS,
)
```
Fonte: `commaai/opendbc:opendbc/car/honda/values.py` (linhas ~248‑253). CONFIRMADO (fonte primária/código oficial).

Pontos‑chave:
- Classe `HondaBoschPlatformConfig` (CAN clássico) — **não** `HondaBoschCANFDPlatformConfig`, que é a classe reservada exclusivamente para veículos CAN‑FD e que adiciona a flag `HondaFlags.BOSCH_CANFD` e troca o DBC para `honda_common_canfd_generated` (`opendbc/car/honda/values.py`, definição da classe em ~linhas 143‑149).
- DBC usado: `honda_bosch_radarless_generated` — o **mesmo** DBC do Honda Civic 2022‑26 (`HONDA_CIVIC_2022`, linhas ~209‑221) e do Honda HR‑V 2023‑27 (`HONDA_HRV_3G`, linhas ~242‑247), ambos também com `flags=HondaFlags.BOSCH_RADARLESS`.
- Em contraste, modelos que **são** CAN‑FD usam explicitamente `HondaBoschCANFDPlatformConfig`, por exemplo:
  - `HONDA_ACCORD_11G = HondaBoschCANFDPlatformConfig(...)` — "Honda Accord 2023‑25"/"Accord Hybrid 2023‑26" (linha ~187)
  - `HONDA_CRV_6G = HondaBoschCANFDPlatformConfig(...)` — "CR‑V 2023‑26"/"CR‑V Hybrid 2023‑27" (linha ~229)
  - `HONDA_PILOT_4G`, `HONDA_PILOT_4G_MMR`, `HONDA_PASSPORT_4G`, `ACURA_MDX_4G_MMR`, `ACURA_TLX_2G_MMR` (linhas ~281‑327)

Fonte: `commaai/opendbc:opendbc/car/honda/values.py`. CONFIRMADO.

### 1.2 Safety firmware do panda confirma a distinção (CONFIRMADO)

Em `opendbc/safety/modes/honda.h` existem flags de hardware separadas e mutuamente distintas:
```c
static bool honda_bosch_radarless = false;
static bool honda_bosch_canfd = false;
...
const uint16_t HONDA_PARAM_RADARLESS = 8;
const uint16_t HONDA_PARAM_BOSCH_CANFD = 16;
...
honda_bosch_radarless = GET_FLAG(param, HONDA_PARAM_RADARLESS);
honda_bosch_canfd = GET_FLAG(param, HONDA_PARAM_BOSCH_CANFD);
```
e os conjuntos de mensagens TX diferem conforme o parâmetro (`HONDA_RADARLESS_TX_MSGS` vs `HONDA_CANFD_TX_MSGS`), mas **ambos usam `CanMsg`/`CANPacket_t` compartilhados com o restante do código Honda clássico** (sem tipos de frame FD separados no nível de safety para o radarless). Isso demonstra que o firmware do panda trata "radarless" (caso do City) e "CAN‑FD" (caso do Accord/CR‑V novos) como **modos distintos**, e o City está classificado no primeiro. Fonte: `commaai/opendbc:opendbc/safety/modes/honda.h`. CONFIRMADO.

### 1.3 Layout de barramentos CAN e onde o panda intercepta (CONFIRMADO, genérico à plataforma Honda Bosch)

Comentário de código em `opendbc/car/honda/hondacan.py`:
```python
# CAN bus layout with relay
# 0 = ACC-CAN - radar side
# 1 = F-CAN B - powertrain
# 2 = ACC-CAN - camera side
# 3 = F-CAN A - OBDII port
```
E a lógica de atribuição de barramento (classe `CanBus`):
```python
# powertrain bus is split instead of radar on radarless and CAN FD Bosch
if CP is not None and CP.flags & HondaFlags.BOSCH and not (CP.flags & (HondaFlags.BOSCH_RADARLESS | HondaFlags.BOSCH_CANFD)):
  self._pt, self._radar = self.offset + 1, self.offset
  self._lkas = self._pt if CP.openpilotLongitudinalControl else self._radar
else:
  self._pt, self._radar, self._lkas = self.offset, self.offset + 1, self.offset
```
Fonte: `commaai/opendbc:opendbc/car/honda/hondacan.py` (linhas ~1‑35). CONFIRMADO.

Interpretação para o **Honda City 7G (radarless)**: por ser radarless, powertrain (`pt`) e LKAS ficam no bus "offset" (0 — fisicamente, a "ACC‑CAN lado radar/câmera" que o painel/girafa interno do panda relaya), enquanto o bus "offset+1" carrega o que seria o radar (inexistente fisicamente neste modelo, pois não há radar — só câmera). O bus "offset+2" é dedicado à câmera e o "offset+3" corresponde fisicamente ao F‑CAN A, que é o barramento acessível no conector OBD‑II. Essa é a arquitetura de referência do framework (não documentação exclusiva do City, mas a lógica aplicada a ele por herdar a classe Bosch comum). INFERÊNCIA (extrapolação direta do código, mas não há documento Honda oficial específico do City que descreva nomes físicos "F‑CAN"/"B‑CAN" do GN).

### 1.4 Harness/chicote oficial: "Honda Bosch B" (CONFIRMADO)

O arquivo de documentação oficial dos carros suportados confirma o chicote físico exato recomendado:

```
|Honda|City (Brazil only) 2023|All|openpilot available|0 mph|14 mph|...
Parts: - 1 Honda Bosch B connector - 1 OBD-C cable (2 ft) - 1 comma four - 1 comma power v3 - 1 harness box - 1 mount
Buy Here: https://comma.ai/shop/comma-3x?harness=Honda City (Brazil only) 2023
```
Fonte: `commaai/openpilot:docs/CARS.md` (gerado automaticamente a partir de `opendbc`). CONFIRMADO.

Confirma-se também que os três veículos "radarless" citados (City 2023 BR, Civic 2022‑26, HR‑V 2023‑27) usam **o mesmo chicote "Honda Bosch B"**, enquanto o CR‑V 2023‑26 (CAN‑FD) usa **"Honda Bosch C"** — ou seja, o próprio catálogo de hardware da comma distingue fisicamente os veículos CAN‑FD (chicote C) dos radarless/clássico (chicote B). Isso é evidência adicional, indireta mas de fonte oficial, de que o City está no grupo CAN clássico. CONFIRMADO.

A lógica de mapeamento de chicote também está no código (`opendbc/car/honda/values.py`, `HondaCarDocs.init_make`):
```python
if CP.flags & HondaFlags.BOSCH:
  if CP.flags & HondaFlags.BOSCH_CANFD:
    harness = CarHarness.bosch_c
  elif CP.flags & HondaFlags.BOSCH_RADARLESS:
    harness = CarHarness.bosch_b
  else:
    harness = CarHarness.bosch_a
```
Como o City usa `flags=HondaFlags.BOSCH_RADARLESS`, o harness atribuído automaticamente é `bosch_b`. CONFIRMADO.

### 1.5 Modelos irmãos (HR‑V 2023, Civic 2022+) — checagem cruzada

- **Honda HR‑V 2023‑27** (mesma plataforma GN/"5G"): `HONDA_HRV_3G = HondaBoschPlatformConfig(..., flags=HondaFlags.BOSCH_RADARLESS)` — **radarless, CAN clássico**, harness "Honda Bosch B" (`docs/CARS.md`, linha 102). Portanto, **não** é CAN‑FD, ao contrário do que às vezes se assume por ser "modelo recente". CONFIRMADO.
- **Honda Civic 2022‑26 (11ª geração, "HONDA_CIVIC_2022")**: também `HondaBoschPlatformConfig(..., flags=HondaFlags.BOSCH_RADARLESS)`, DBC `honda_bosch_radarless_generated`, harness "Honda Bosch B" (`docs/CARS.md`, linha 86). Isto **contradiz** a suposição citada na tarefa de que "Civic 2022+ é CAN‑FD e exige red panda" — segundo o código oficial atual do openpilot/opendbc, o Civic 11G é radarless/CAN clássico, não CAN‑FD. Uma fonte de terceiros (resposta de busca na web, não oficial) alegou erroneamente que o Civic 2022 "usa CAN‑FD" e exige harness "Bosch C" — isso é **NÃO VERIFICADO / provavelmente incorreto** frente à fonte primária acima, e deve ser tratado com cautela (pode refletir confusão com o Accord/CR‑V 2023+, que são os modelos realmente CAN‑FD no catálogo atual). Classificação: a crença popular "Civic 2022+ = CAN‑FD" é **HIPÓTESE NÃO CONFIRMADA / contradita pela fonte primária**.
- **Honda Accord 2023‑25 / CR‑V 2023‑26 / Pilot 2023‑25+ / Passport 2026 / Acura MDX 2025‑26 / TLX 2025**: estes sim são `HondaBoschCANFDPlatformConfig`, harness "Honda Bosch C" — **estes são os modelos que realmente requerem CAN‑FD** no catálogo Honda atual do openpilot. CONFIRMADO.

> **Observação metodológica:** não há, nas fontes consultadas, uma declaração explícita e dedicada da Honda (documentação de serviço oficial) descrevendo a topologia elétrica do GN (City/HR‑V BR) nomeando literalmente "F‑CAN"/"B‑CAN" para este modelo específico — a nomenclatura F‑CAN/B‑CAN vem de artigos genéricos sobre a arquitetura Honda (ex.: AutoCodes.com, eobdcode.com — fontes secundárias, não oficiais da Honda) e do comentário de código do opendbc (`hondacan.py`), que é uma fonte primária de software mas não um documento de engenharia elétrica da Honda. Portanto, a nomenclatura F‑CAN A/B aplicada ao City é **INFERÊNCIA** por analogia de plataforma, não **CONFIRMADO** por manual de serviço Honda.

### 1.6 Veredito sobre a premissa CAN‑FD

**REFUTADO**: a afirmação "Honda City 2023 BR requer CAN‑FD" é falsa segundo a fonte primária oficial (`commaai/opendbc`). O veículo está catalogado como Honda Bosch **radarless em CAN clássico (2.0B)**, compatível com panda/panda branco ou panda cinza padrão (não exige necessariamente red panda), usando harness "Honda Bosch B".

### 1.7 Bitrate dos barramentos (NÃO VERIFICADO para o City especificamente)

Não foi encontrada, nas fontes primárias consultadas (opendbc/openpilot), uma declaração explícita do bitrate (ex.: 500 kbps) configurado para os barramentos do City 7G — o código do opendbc não fixa bitrates por modelo nesse nível (o panda normalmente configura 500 kbps para os barramentos CAN de powertrain Honda, por convenção observada em outros Honda Bosch, mas isso não está disponível como constante dedicada e documentada no values.py do City). Fontes genéricas de terceiros (AutoCodes.com, eobdcode.com) afirmam que a arquitetura F‑CAN opera tipicamente a 500 kbps e B‑CAN a 33,3/125 kbps em Hondas em geral — mas isso é uma generalização de plataforma Honda, **não uma confirmação específica para o City 2023 BR**. Classificação: **INFERÊNCIA / NÃO VERIFICADO** — recomenda‑se confirmação empírica (ver seção 3).

---

## 2. Suporte atual no openpilot/opendbc

### 2.1 Está no código oficial? Sim — CONFIRMADO

| Item | Status | Caminho/arquivo |
|---|---|---|
| Enum `CAR.HONDA_CITY_7G` | Presente | `opendbc/car/honda/values.py` |
| `PlatformConfig` (specs, DBC, flags) | Presente, classe `HondaBoschPlatformConfig`, `flags=HondaFlags.BOSCH_RADARLESS` | `opendbc/car/honda/values.py` (linhas ~248‑253) |
| Fingerprint de FW (ECU EPS) | Presente: `(Ecu.eps, 0x18da30f1, None): [b'39990-T14-B030\x00\x00']` | `opendbc/car/honda/fingerprints.py` |
| DBC gerado | `honda_bosch_radarless_generated` (compartilhado com Civic 2022‑26 e HR‑V 2023‑27) | `opendbc/dbc/` (referenciado em `values.py`) |
| Rota de teste de regressão (CI) | `CarTestRoute("56b2cf1dacdcd033/00000017--d24ffdb376", HONDA.HONDA_CITY_7G)  # Brazilian model` | `opendbc/car/tests/routes.py` |
| Dados de direção (torque) | `"HONDA_CITY_7G" = [1.2, 1.2, 0.23]` | `opendbc/car/torque_data/override.toml` |
| Limiar de torque de direção (STEER_THRESHOLD) | `CAR.HONDA_CITY_7G: 600` | `opendbc/car/honda/values.py` |
| Safety flags no panda (`safety_honda.h`/`honda.h`) | `HONDA_BOSCH` + `honda_bosch_radarless=true`, `honda_bosch_canfd=false` (via `HondaSafetyFlags.RADARLESS`) | `opendbc/safety/modes/honda.h` |
| Harness oficial à venda | "Honda Bosch B" (parte física), vendido junto com comma 3X/comma four | `openpilot/docs/CARS.md` (linha do Honda City), loja comma.ai |
| Status de suporte declarado | "openpilot available" (controle completo de direção e ACC via openpilot, respeitando 0 mph mínimo p/ ACC e 14 mph mínimo p/ ALC) | `openpilot/docs/CARS.md` |

Fontes: `commaai/opendbc` (arquivos citados), `commaai/openpilot:docs/CARS.md`. CONFIRMADO.

### 2.2 Histórico/changelog (CONFIRMADO)

A nota oficial de release do `opendbc` confirma quem e quando o suporte foi adicionado:

> "Honda City 2023 support thanks to vanillagorillaa and drFritz!" — Release **opendbc 0.3.0**, publicada por **sshane** (mantenedor comma.ai), 22 de abril (ano corrente do repositório — a release lista também suporte simultâneo a Accord 2023‑25, CR‑V 2023‑25/26, Pilot 2023‑25, Passport 2026 e Acura MDX 2025, todos como famílias de modelos Honda separadas e explicitamente usando classes diferentes no código, conforme seção 1).

Fonte: GitHub Releases — `commaai/opendbc` — https://github.com/commaai/opendbc/releases (release 0.3.0). CONFIRMADO.

### 2.3 O que falta para um "port" — resposta: nada crítico, já está pronto (CONFIRMADO/INFERÊNCIA)

Como o City 7G já possui CarInterface herdado da classe Honda Bosch genérica (`opendbc/car/honda/interface.py`, `carstate.py`, `carcontroller.py`, `hondacan.py` — todos compartilhados com os demais Honda Bosch radarless), **não existe lacuna de porte**: fingerprint, DBC, safety flags e harness já estão publicados e versionados. O único elemento que pode exigir validação adicional pelo usuário final é:
- Confirmar que a variante específica do mercado BR (ex.: trims EXL/Touring, ano‑modelo exato, eventual facelift) bate com o fingerprint publicado (`39990-T14-B030`) — pois a Honda pode usar números de peça EPS diferentes entre variantes/anos, o que geraria "fingerprint não reconhecido" mesmo com suporte de plataforma já existente. Isso é **INFERÊNCIA** de risco prático, não documentado explicitamente como problema conhecido nas fontes consultadas.
- Forks (sunnypilot, frogpilot): não foi encontrada, nas buscas realizadas, menção específica adicional de PRs ou issues tratando do Honda City no GitHub desses forks nesta sessão de pesquisa — **NÃO VERIFICADO** (a pesquisa não teve acesso dedicado aos repositórios sunnypilot/frogpilot; apenas opendbc/openpilot oficiais foram inspecionados diretamente). Recomenda-se busca adicional direta nos repositórios `sunnypilot/sunnypilot` e `FrogAi/FrogPilot` caso se deseje usar esses forks em vez do openpilot stock.

---

## 3. Procedimento seguro, somente‑leitura, para o usuário confirmar empiricamente (caso deseje validação própria)

Mesmo com a forte evidência de que o City 7G é CAN clássico (seção 1), é prudente confirmar fisicamente antes de instalar hardware definitivo, especialmente se o veículo do usuário for de um ano‑modelo/trim não coberto pelo fingerprint publicado. Procedimento:

### 3.1 Avisos de segurança (ler antes de iniciar)
- **Ignição ligada, motor desligado** (modo "ACC"/posição II, sem o motor rodando) é suficiente para a maioria dos módulos acordarem no barramento; não é necessário dirigir o veículo.
- **Nunca transmita (TX) quadros no barramento** até ter certeza absoluta do protocolo e das consequências — ative sempre o **modo listen‑only (somente escuta)** no adaptador antes de conectar aos conectores do veículo.
- Não injete comandos de diagnóstico, não use ferramentas de "flash"/reprogramação, e não conecte simultaneamente múltiplos adaptadores ativos no mesmo barramento sem necessidade.
- Se o veículo estiver sob garantia, documente o procedimento (fotos antes/depois) e evite modificações permanentes na chicotaria; prefira captura via conector não destrutivo tipo "T" ou breakout no próprio conector da câmera/harness oficial "Honda Bosch B" da comma (que é não invasivo, por ser plugável).
- Desligue a ignição e remova a chave/break o contato de bateria (12V) antes de conectar/desconectar fisicamente qualquer chicote, para evitar arco elétrico ou picos de tensão.
- Interrompa a captura e desconecte imediatamente se notar: luzes de aviso novas no painel, comportamento anômalo do ADAS (ex.: ACC ou LKAS desligando sozinho), ou cheiro de queimado/fumaça.

### 3.2 Ferramentas recomendadas
- Um **panda** (clássico, CAN 2.0B — suficiente se a hipótese do relatório estiver correta) **ou** um **red panda** (suporta CAN‑FD nativamente e também CAN clássico) — usar o red panda cobre os dois cenários possíveis, sendo a opção mais segura para o teste exploratório.
- Alternativamente, um adaptador FD genérico (PCAN‑FD da PEAK, ou um dispositivo com firmware "candleLight FD"/gs_usb FD) com SocketCAN no Linux.
- Software: `candump`/`cansniffer` (pacote `can-utils`, Linux/SocketCAN) e/ou **SavvyCAN** (multiplataforma, com suporte a listen‑only e CAN‑FD).

### 3.3 Passo a passo (somente leitura)
1. **Preparação**: veículo estacionado, freio de estacionamento acionado, motor desligado, ignição na posição "ligado/acessórios" (ACC ou "II", conforme o GN).
2. **Conectar o adaptador no conector OBD‑II** (padrão SAE J1962, sob o painel do motorista) — este conector, segundo a arquitetura de referência do opendbc (seção 1.3), deveria expor o F‑CAN A (candidato ao powertrain/diagnóstico). Opcionalmente, repetir o teste no conector do harness da câmera ADAS (Honda Bosch B), se o usuário já tiver esse chicote instalado, para comparar os barramentos "ACC‑CAN" (câmera/LKAS).
3. **Configurar modo listen‑only antes de subir a interface**:
   - Linha de comando (Linux/SocketCAN, exemplo genérico):
     ```
     sudo ip link set can0 type can bitrate 500000 listen-only on
     sudo ip link set can0 up
     candump can0
     ```
   - Se o adaptador suportar CAN‑FD nativamente e quiser testar a hipótese de FD, repita habilitando o modo FD explicitamente, por exemplo:
     ```
     sudo ip link set can0 type can bitrate 500000 dbitrate 2000000 fd on listen-only on
     sudo ip link set can0 up
     candump -tz can0
     ```
   - Em SavvyCAN: abrir a janela de conexão, marcar a caixa "Listen Only" para cada barramento antes de conectar; se o dispositivo suportar, marcar também a opção CAN‑FD.
4. **Critério para identificar CAN‑FD vs. CAN clássico**:
   - Quadros CAN clássico têm DLC (comprimento de dados) de **0 a 8 bytes**.
   - Quadros CAN‑FD podem ter DLC estendido correspondendo a payloads de **12, 16, 20, 24, 32, 48 ou 64 bytes**, e o adaptador/ferramenta normalmente sinaliza explicitamente a flag "FD"/"BRS" (Bit Rate Switch) no quadro capturado.
   - Se, ao capturar com `candump`/SavvyCAN em modo **não‑FD**, você não vir nenhum erro de "frame length" e todos os quadros tiverem ≤8 bytes, é forte indício de CAN clássico (consistente com a seção 1). Se houver erros de quadro ou dados truncados, repita em modo FD explícito e veja se os mesmos endereços aparecem com DLC > 8 bytes — isso confirmaria CAN‑FD.
   - Teste de taxa (bitrate): comece com 500 kbps (valor típico Honda, conforme fontes genéricas citadas na seção 1.7). Se não houver tráfego ou houver apenas erros de "bit error"/"stuff error" constantes, tente 125 kbps e 250 kbps apenas em modo listen‑only (nunca em modo ativo) para varrer possíveis barramentos de corpo (B‑CAN).
5. **Critérios de parada (stop criteria)**:
   - Encerre a captura assim que tiver pelo menos 30 a 60 segundos de tráfego estável e repetível para documentar a presença/ausência de quadros FD.
   - Pare imediatamente e desconecte se: o veículo apresentar qualquer comportamento elétrico anômalo, se o adaptador reportar sobrecarga/curto, ou se não for possível manter o modo listen‑only (risco de transmissão acidental).
   - Nunca prossiga para testes de transmissão (envio de quadros) como parte deste procedimento — isso está fora do escopo de uma verificação segura e pode acionar funções de segurança do veículo (ex.: AEB, cancelamento de ACC) de forma imprevisível.
6. **Registro**: salve os arquivos de captura (`.log`/`.asc`/formato SavvyCAN) com timestamp, localização do conector usado, ignição/estado do motor, e bitrate testado, para permitir comparação posterior com o DBC `honda_bosch_radarless_generated` do opendbc.

---

## Tabela de classificação resumida

| Pergunta | Resposta | Classificação |
|---|---|---|
| Honda City 2023 BR exige CAN‑FD? | Não — é Bosch "radarless" em CAN clássico | **REFUTADO** (fonte primária) |
| Honda City 2023 BR já suportado no opendbc/openpilot? | Sim, desde release 0.3.0 | **CONFIRMADO** |
| Harness físico correto | "Honda Bosch B" | **CONFIRMADO** |
| HR‑V 2023 BR (mesma plataforma) também é CAN clássico? | Sim, mesma flag/DBC do City | **CONFIRMADO** |
| Civic 2022+ é CAN‑FD (crença comum)? | Não, segundo o código atual — é radarless/CAN clássico, harness B | **Contradiz hipótese popular — classificar a crença como NÃO VERIFICADO/REFUTADA** |
| Accord 2023+/CR‑V 2023+ são CAN‑FD? | Sim, harness "Bosch C" | **CONFIRMADO** |
| Bitrate exato dos barramentos do City | Provavelmente 500 kbps (padrão F‑CAN Honda), mas não documentado explicitamente para o City | **INFERÊNCIA/NÃO VERIFICADO** |

---

## Fontes consultadas

| # | Título | URL | Tipo | Data de acesso |
|---|---|---|---|---|
| 1 | `opendbc/car/honda/values.py` (commit c3955753) | https://github.com/commaai/opendbc/blob/master/opendbc/car/honda/values.py | Primária (código oficial) | 22/10/2026 |
| 2 | `opendbc/car/honda/fingerprints.py` | https://github.com/commaai/opendbc/blob/master/opendbc/car/honda/fingerprints.py | Primária (código oficial) | 22/10/2026 |
| 3 | `opendbc/car/torque_data/override.toml` | https://github.com/commaai/opendbc/blob/master/opendbc/car/torque_data/override.toml | Primária | 22/10/2026 |
| 4 | `opendbc/car/tests/routes.py` | https://github.com/commaai/opendbc/blob/master/opendbc/car/tests/routes.py | Primária | 22/10/2026 |
| 5 | `opendbc/safety/modes/honda.h` | https://github.com/commaai/opendbc/blob/master/opendbc/safety/modes/honda.h | Primária (firmware panda) | 22/10/2026 |
| 6 | `opendbc/car/honda/hondacan.py` | https://github.com/commaai/opendbc/blob/master/opendbc/car/honda/hondacan.py | Primária | 22/10/2026 |
| 7 | `openpilot/docs/CARS.md` ("Supported Cars") | https://github.com/commaai/openpilot/blob/master/docs/CARS.md | Primária (documentação oficial gerada) | 22/10/2026 |
| 8 | Releases · commaai/opendbc (release 0.3.0/0.3.1) | https://github.com/commaai/opendbc/releases | Primária (changelog oficial) | 22/10/2026 |
| 9 | "Honda B-CAN And F-CAN" | https://www.autocodes.com/articles/32/honda-b-can-and-f-can.html | Secundária (não Honda oficial) | 22/10/2026 |
| 10 | "Honda B-CAN And F-CAN" | https://www.eobdcode.com/en/magazine-en/honda-b-can-and-f-can/ | Secundária | 22/10/2026 |
| 11 | DeepWiki — "Hardware Requirements" / "Supported Vehicles and Releases" (commaai/openpilot-docs) | https://deepwiki.com/commaai/openpilot-docs/4.2-hardware-requirements e https://deepwiki.com/commaai/openpilot/1.1-supported-vehicles-and-releases | Terciária (resumo não oficial, baseado no código oficial) | 22/10/2026 |
| 12 | comma.ai — loja de chicotes para carro | https://comma.ai/shop/car-harness | Primária (comercial) — **FALHA DE ACESSO**: tentativa de `web_fetch` retornou erro de transporte/DNS; conteúdo não verificado diretamente nesta sessão, apenas via resumo de busca de terceiros | 22/10/2026 (tentativa) |
| 13 | GitHub Issue "Automatic switching between CAN 2.0 and CAN FD for Red Panda" | https://github.com/commaai/panda/issues/795 | Primária (discussão de engenharia comma.ai) | 22/10/2026 |
| 14 | SavvyCAN — "9. Connection Window" (documentação) | https://www.savvycan.com/docs/connectionwindow.html | Primária (documentação da ferramenta) | 22/10/2026 |
| 15 | "Reading Your Car's CAN Bus with SavvyCAN Safely" | https://www.bigiron.cc/guides/reading-your-cars-can-bus-savvycan-safely | Secundária (guia de terceiros) | 22/10/2026 |
| 16 | "2022 Honda Civic OpenPilot Car Harness" | https://harbn.com/2022-honda-civic-openpilot-car-harness/ | Secundária (relato de usuário, **contradiz a fonte primária nº 1 sobre CAN‑FD do Civic** — tratado como NÃO VERIFICADO/possível erro) | 22/10/2026 |
| 17 | CommaGuide — "Honda City (Brazil only) 2023: openpilot Compatibility" | https://commaguide.com/cars/honda-city-brazil-only-2023/ | Terciária (site não oficial espelhando dados do opendbc) | 22/10/2026 |

### Limitações e lacunas declaradas
- Não foi possível acessar diretamente `comma.ai/shop/car-harness` (falha de DNS/transporte na ferramenta de fetch); as informações sobre harnesses A/B/C vieram de uma síntese de busca que cita essa página como fonte, mas não foi verificada byte a byte nesta sessão — classificar qualquer detalhe exclusivo dessa página como **NÃO VERIFICADO** até confirmação direta.
- Não foi feita varredura dedicada dos repositórios `sunnypilot/sunnypilot` e `FrogAi/FrogPilot` nem do Discord oficial da comma.ai nesta sessão (ferramentas usadas não têm acesso a histórico de Discord); portanto, qualquer menção de experiência de usuários Brasil nesses canais permanece **NÃO VERIFICADO**.
- Nenhuma fonte de documentação de serviço oficial da Honda (manual de oficina/circuito elétrico) foi localizada ou consultada diretamente — toda a análise de barramentos é baseada em código‑fonte do opendbc (primário quanto ao software, mas não um documento de engenharia elétrica da fabricante) e em artigos genéricos de terceiros sobre a arquitetura CAN da Honda.
- O bitrate exato dos barramentos do GN/City (500 kbps presumido) não está confirmado por nenhuma fonte primária específica ao modelo; permanece **INFERÊNCIA**, daí a recomendação do procedimento de captura na seção 3.


## Adenda 2026-10-26 — black panda (F4) × City 2023: incompatibilidade temporal (verificado no git)

| Evento | Data | Commit | Fonte |
|---|---|---|---|
| Remoção de white/black panda do firmware (`board/boards/black.h` apagado, `HW_TYPE_BLACK_PANDA` removido) | 2025-07-19 | panda `3d272335` "Deprecate white and black pandas (#2227)" | `hardware\reference\panda_full` |
| Último release openpilot com F4 | 2025-06-05 | tag `v0.9.9` | `hardware\reference\openpilot` |
| Honda City (Brazil only) 2023 adicionado | **2025-08-19** | opendbc `43006b9a` "Honda: Honda City (Brazil only) 2023 (#2425)" | `hardware\reference\opendbc` |
| openpilot actual (`ff47f484`, 2026-10-22) | — | `panda/python/__init__.py:153` `SUPPORTED_DEVICES = H7_DEVICES`; `:355/:436` `assert hw_type in SUPPORTED_DEVICES` | — |

Conclusão: **não existe versão oficial do openpilot que suporte simultaneamente o black panda (STM32F4) e o
Honda City 2023 BR.** Um black panda físico (placa OpenBlackPanda) fala CAN clássico com o City sem problema
eléctrico, mas o openpilot ≥ 0.10 rejeita-o (`Unknown HW`) e o openpilot ≤ 0.9.9 não conhece o City.
Só funcionaria com fork/backport manual do `HONDA_CITY_7G` para opendbc antigo — fora do escopo deste projecto.
Isto confirma a necessidade da variante H7 (red panda, `HW_TYPE_RED_PANDA = 7`) deste repositório.
