# R4 — Capacidades do fabricante (JLCPCB, 4 camadas) e regras de projeto adotadas

Data da consulta: 2026-10-22

## Status da fonte

- Página oficial `https://jlcpcb.com/capabilities/pcb-capabilities`: **BLOQUEADO** neste ambiente
  (falha TLS/DNS em `web_fetch`, em `Invoke-WebRequest` e em todos os agentes de pesquisa — ver R3 §10).
- Fonte utilizada (SECUNDÁRIA, consolida a página oficial "as of late 2025"):
  "JLCPCB Design Rules and Capabilities: Complete Specification Guide" — schemalyzer.com,
  `https://www.schemalyzer.com/en/blog/manufacturing/jlcpcb/jlcpcb-design-rules` (acesso 2026-10-22).
- Corroboração parcial (fóruns, também secundários): `https://forum.kicad.info/t/help-with-jlcpcb-settings/40866`,
  `https://embdev.net/topic/478351`.
- **Todos os valores abaixo são NÃO VERIFICADOS na fonte primária.** Antes de encomendar, conferir manualmente na
  página oficial e no DFM automático do pedido JLCPCB.

## Valores publicados (fonte secundária) — 4 camadas, 1 oz externo / 0,5 oz interno

| Parâmetro | Valor publicado | Regra adotada no HybridPanda.kicad_pcb | Margem |
|---|---|---|---|
| Trilha/espaçamento mín. | 0,10 mm (4 mil), sem custo extra | 0,127 mm (5 mil) | +27 % |
| Furo de via mín. (mecânico) | 0,20 mm | 0,30 mm (`min_through_hole`) | +50 % |
| Pad de via mín. | 0,45 mm | 0,45 mm (`min_via_diameter`); netclass Default 0,6/0,3 | igual / maior |
| Anel anular mín. | 0,15 mm (recomendado 0,20) | 0,13 mm (`min_via_annular_width`) — ver nota 1 | **abaixo** |
| Via-a-via (hole-to-hole) | 0,127 mm (via); hole clearance 0,25 mm | hole-to-hole 0,50 mm; hole clearance 0,25 mm | maior |
| PTH mín. | 0,15 mm | 0,30 mm | maior |
| NPTH mín. | 0,50 mm | furos NPTH do P1 = 0,80 mm (footprint original) | ok |
| Cobre → borda | ≥ 0,30 mm (checklist DFM) / 0,20 mm (fórum) | 0,30 mm (`copper_edge_clearance`) | igual |
| Dam de máscara mín. | 0,10 mm | padrão KiCad (0,0 expansão; verificar no DFM) | — |
| Silk: largura / altura mín. | 0,15 mm / 1,0 mm (alta precisão 0,10 / 0,80) | 0,10 mm / 0,60 mm — ver nota 2 | **abaixo** |
| Espessura | 0,8–1,6 mm padrão | 1,6 mm (herdado do original) | ok |
| Nº de camadas | 1–20 (fonte secundária); usuário informa "até 10" (NÃO VERIFICADO na página oficial) | 4 camadas (herdado do original) | ok |
| Impedância controlada | sem custo extra, ±10 %, calculadora JLCPCB | ver nota 3 | — |

Notas:
1. O anel mínimo de 0,13 mm foi configurado para permitir a passagem do footprint original do conector P1
   (anel 0,10 mm; ainda assim viola). Para fabricação, usar vias com anel ≥ 0,15 mm (netclasses já usam 0,15/0,15/0,2).
   As violações remanescentes do P1 (anel 0,10 mm; hole-to-hole 0,40 mm) são **inerentes ao footprint do conector
   original** (`TYPE-C-31-M-04` do BlackPanda.pretty) e estão listadas como exceções no relatório de DRC.
2. Texto de referência em silk foi reduzido a 0,6 mm / 0,1 mm apenas para o rascunho de posicionamento; as referências
   dos passivos 0402/0603 estão ocultas no silk (permanecem em F.Fab/B.Fab). Antes de fabricar, aumentar para ≥ 0,8/0,10
   ou aceitar o alargamento automático do JLCPCB.
3. CANH/CANL: pares diferenciais 120 Ω não são críticos em trilhas de poucos cm para 2–5 Mbit/s (comprimento elétrico
   ≪ tempo de subida); a regra adotada é apenas comprimento casado (±1 mm) e roteamento acoplado 0,25/0,20 mm.
   Isto é uma INFERÊNCIA de engenharia, não uma exigência do datasheet TCAN1044V (que exige 120 Ω apenas na terminação
   de barramento). USB-FS: 90 Ω diferencial, igualmente pouco crítico em < 5 cm.

## Montagem SMT (JLCPCB)
- Página `https://jlcpcb.com/smt-assembly`: **BLOQUEADO**. Classificação Basic/Extended de cada LCSC P/N:
  NÃO VERIFICADO (ver R3, tabelas de distribuidores).
