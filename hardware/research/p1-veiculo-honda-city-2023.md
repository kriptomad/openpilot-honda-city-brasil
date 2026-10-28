# P1 — Honda City 2023 BR: CAN-FD? ADAS Bosch?

Status: **REFUTADA (parte CAN-FD) / CONFIRMADA (parte ADAS Bosch)**
Data da verificação: 2026-10-22 (pesquisa completa em `from_v1/R1_veiculo_honda_city_openpilot.md`,
re-verificada contra o clone local `02_REFERENCE/opendbc` @ `c3955753ae7258412814e2cdca3ee8af979e4679`).

## Fatos com fonte

| # | Fato | Fonte (caminho no clone / URL) |
|---|------|-------------------------------|
| 1 | `HONDA_CITY_7G = HondaBoschPlatformConfig(... {Bus.pt: 'honda_bosch_radarless_generated'}, flags=HondaFlags.BOSCH_RADARLESS)` — classe **CAN clássico**, DBC radarless | `02_REFERENCE/opendbc/opendbc/car/honda/values.py` |
| 2 | Veículos CAN-FD Honda usam `HondaBoschCANFDPlatformConfig` (flag `BOSCH_CANFD`, DBC `honda_common_canfd_generated`): Accord 11G, CR-V 6G, Pilot 4G, Passport 4G, MDX/TLX MMR. City **não** está nessa lista | idem |
| 3 | Safety: flags separadas `HONDA_PARAM_RADARLESS=8` e `HONDA_PARAM_BOSCH_CANFD=16` | `02_REFERENCE/opendbc/opendbc/safety/modes/honda.h` |
| 4 | Harness oficial: `CarHarness.bosch_b` ("Honda Bosch B") | `values.py` (HondaCarDocs/HondaBoschPlatformConfig → `car_parts`) |
| 5 | Layout de bus: 0 = ACC-CAN lado radar/câmera (pt+lkas no radarless), 1 = F-CAN B, 2 = ACC-CAN lado câmera, 3 = F-CAN A (OBD) | `02_REFERENCE/opendbc/opendbc/car/honda/hondacan.py` |
| 6 | Câmera Honda Sensing do City é Bosch (radarless = só câmera) | inferência direta da flag `BOSCH_RADARLESS` (fonte primária: código) |

## Conclusão e impacto no projeto

- **CAN-FD não é exigido** pelo Honda City 2023 BR segundo o suporte oficial do openpilot. O hardware
  CAN-FD (H7 + transceivers 5 Mbps) é **retrocompatível** com CAN clássico (FDCAN em modo clássico,
  `llfdcan.h` suporta ambos), portanto não prejudica o uso — mas a motivação declarada (P1) está refutada.
- Decisão do usuário (registrada em sessão, 2026-10-22): **prosseguir com o H7 mesmo assim**
  (firmware do black panda F413 foi descontinuado no `panda` master — `board/boards/black.h`
  não existe mais no commit `408e14d4`; apenas `red.h`, `tres.h`, `cuatro.h`).
- Taxa de bits: F-CAN Honda = 500 kbit/s (fonte: DBCs Honda e prática openpilot — **NÃO VERIFICADO em
  documento Honda oficial**; valor de rede CAN típica, usado pelo panda por padrão em `can_set_speed` 5000 = 500k).

## Procedimento de captura passiva (para confirmação com analisador)

1. Carro desligado, chave fora. Conectar o analisador **somente aos pinos CANH/CANL do OBD-II**
   (pino 6 = CANH, pino 14 = CANL, SAE J1962 — fato normativo, **fonte: SAE J1962 / ISO 15031-3**,
   NÃO VERIFICADO no manual Honda) com transceiver em **modo listen-only / silent** (sem ACK).
2. Ligar a ignição (sem dar partida). Capturar 60 s a 500 kbit/s; se houver 100 % de erros de forma,
   tentar 125/250 kbit/s. Registrar: taxa, nº de IDs, presença de frames com FDF=1 (CAN-FD), DLC > 8.
3. Nunca transmitir. Critério de parada: qualquer DTC novo no painel → desconectar.
4. Repetir no conector da câmera (harness Bosch B) **somente** com o harness de desvio comma e o
   analisador em listen-only, com carro parado.
5. Resultado esperado (pelo P1): CAN clássico 500 kbit/s, sem FDF.
