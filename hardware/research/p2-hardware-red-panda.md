# P2 — Hardware do Red Panda: o que a commaai publica e o que NÃO publica

## Resultado da busca (2026-10-23)
`gh repo list commaai --limit 300` → 300 repositórios inspecionados por nome. Clonados em `02_REFERENCE\`:

| Repo | HEAD | Conteúdo relevante | Esquema do red panda? |
|---|---|---|---|
| commaai/hardware | a42a4752 | `panda/README.md` (tabela: red panda MCU **STM32H725**, OBD-C, USB-A, 3×CAN-FD + 1 mux, sem GPS; fotos), `harness/OBD-C.sch.pdf`, `harness/v3/*.pdf` (Harness_Box, Honda_Bosch_B…), `harness/v1/boards/*.sch/.brd` (Eagle), `tools/panda_debug`, `ultimate_provisioning`, `comma_four/debug_connector_pinout.pdf` | **NÃO** (só foto + README) |
| commaai/neo | 9869dee9 (arquivado) | hardware do EON/neo (MIT, LICENSE.neo) | não |
| commaai/panda_jungle | b80539fc (arquivado) | firmware do jungle (bancada) | não |
| commaai/harness_tester_challenge | 069f7243 | desafio de tester de harness (MIT) | não |
| commaai/openpilot-docs | 8a007654 | docs | não |
| commaai/panda | 408e14d4 | **firmware** (fonte de verdade: red.h, stm32h7/*) | pinout derivado |

**Conclusão [F]:** a commaai **não publica** esquema/PCB/BOM do red panda (nem do black/white/uno/dos). O firmware (MIT) é a única especificação pública do hardware → metodologia do protocolo (HRS derivado do firmware) é a correta e a única possível. Valores de componentes passivos (pull-ups, divisor VOLT_S, ESD) são **inferências** marcadas NV e precisam de decisão de engenharia própria (DECISIONS.md).

## Identificação do MCU
- README: "STM32H725" (sem sufixo) **[F]**.
- Firmware exige: Flash 1 MB (linker + provisioning em 0x080FFFC0) → sufixo **G**; GPIOF/GPIOG usados (PF7–11, PG9–11) → **não** TFBGA100 (sem portas F/G completas); `clock.h` só aceita PKGR = TFBGA100 (LDO), LQFP144 (SMPS) ou UFBGA169 (SMPS) **[F]**.
- Candidatos coerentes: **STM32H725ZGT6 (LQFP144, SMPS)**, STM32H725IGK6/IGT6 (UFBGA176/LQFP176 — rejeitado pelo PKGR), STM32H725AGI6 (UFBGA169). Escolha: **ZGT6** (D-02). Grau de temperatura real do red panda: NV (sufixo 6 = −40…85 °C é o único disponível na linha H725).

## Fotos (hardware/panda/red-panda.jpg)
Imagem 20 % do README; resolução insuficiente para ler marcações de componentes — não usada como fonte de fatos.

## Itens úteis do repo hardware para este projeto
- `harness/OBD-C.sch.pdf` + `harness/v3/Harness_Box.pdf` → pinout OBD-C e lógica SBU (P10).
- `harness/v3/Honda_Bosch_B_Harness.pdf` → conectores do City (P1/P10).
- `ultimate_provisioning/` → fluxo oficial de flash/provisionamento (STEP 8 bring-up).
- `tools/panda_debug/` → conector de debug (STEP 8).
