# pandarevive: a black panda no openpilot master atual

Resumo curto do trabalho pandarevive. A descricao completa, os hashes
exatos e os resultados de CI estao no repositorio dedicado
[kriptomad/pandarevive](https://github.com/kriptomad/pandarevive)
(`README.pt-BR.md`, `STATUS.md`). Versao em ingles: `pandarevive.md`.

Situacao: compila e passa nos jobs do CI upstream que rodam em runners do
GitHub. Nunca executado em uma black panda. Nenhum pull request no
upstream.

## O que e

Duas branches em forks, as duas chamadas `revive-f4`:

| Componente | Branch | Base | Head |
|---|---|---|---|
| firmware do panda | [kriptomad/panda `revive-f4`](https://github.com/kriptomad/panda/tree/revive-f4) (tambem o submodulo [../firmware/panda-revive-f4](../firmware/panda-revive-f4)) | commaai/panda master `1305b78c` (2026-10-25) | `a8225ef3` |
| lado host do openpilot | [kriptomad/openpilot `revive-f4`](https://github.com/kriptomad/openpilot/tree/revive-f4) | commaai/openpilot master `0152aab4` (2026-10-25) | `941cab937` |

O lado do firmware esta descrito em
[../hardware/research/pandarevive-scope.md](../hardware/research/pandarevive-scope.md)
(secoes 1-6). Este documento cobre o lado do openpilot, adicionado em
2026-10-30.

## Por que foi preciso

- commaai/panda `3d272335` (2025-07) e `1ce986f7` "bye bye f4" (2025-08)
  removeram `board/boards/black.h`, `board/stm32f4/*`, bxCAN, o alvo de
  build F4 e `McuType.F4` / `HW_TYPE_BLACK` da biblioteca Python.
- commaai/openpilot `96d1b876b` (2026-02) removeu o transporte libusb do
  `pandad` (so SPI) e `9aca13cf2` fixou o tipo de MCU em H7. A black panda
  so fala USB.

## Branch `revive-f4` do openpilot

| Commit | Assunto | Arquivos |
|---|---|---|
| `45b12a352` | panda: point submodule to the revive-f4 fork | `.gitmodules`, gitlink `panda` -> `a8225ef3` |
| `92b862b5e` | pandad: restore USB comms for external pandas | `selfdrive/pandad/panda_comms.h`, `usb.cc` (novo, o antigo `panda_comms.cc`), `spi.cc`, `panda.cc`, `panda.h`, `SConscript` |
| `c1e41b44b` | pandad: flash an external panda through its own bootloader request | `selfdrive/pandad/pandad.py` |
| `941cab937` | pandad: cover the black panda in the host side tests | `tests/test_pandad_canprotocol.cc`, `tests/test_pandad_flash.py` (novo) |

O que muda no comportamento:

- O `pandad` tenta USB (`PandaUsbHandle`, VID 0x3801 PID 0xddcc) antes de
  SPI; `Panda::list()` devolve seriais USB e SPI.
- Em um PC (`COMMA_HARDWARE` falso) o `flash_panda()` pede ao firmware para
  entrar no bootstub e depois no bootloader da ST antes do
  `PandaDFU.recover()` e do `Panda.flash()`; em um dispositivo comma as
  linhas de reset do SoM continuam sendo usadas.
- O submodulo panda e o fork, entao o `scons` gera
  `panda/board/obj/panda.bin.signed` (F4) ao lado de `panda_h7.bin.signed`,
  e a biblioteca Python volta a conhecer `McuType.F4` / `HW_TYPE_BLACK`.

Nada mudou no opendbc (codigo de safety compartilhado), em
`common/hardware` (`HardwarePc` serve como esta), no cereal
(`blackPanda @3` nunca saiu) nem na configuracao de processos.

## CI

O GitHub nao executa workflows no fork `kriptomad/openpilot`, entao a
arvore de `941cab937` foi enviada ao repositorio pandarevive (branch
`ci/openpilot-revive-f4`) e rodada la:
https://github.com/kriptomad/pandarevive/actions/runs/41112766789

build release, build macOS, static analysis, unit tests (957 passaram,
49 pulados, 1 xfailed, incluindo o novo `test_pandad_flash.py` e o
`test_pandad_canprotocol` nativo), process replay e Create UI Report:
sucesso. simulator driving: pulado (so commaai). Passos que precisam de
secrets da commaai ou runners proprios nao rodam no fork.

## O que nao esta feito

- Nenhuma execucao em hardware: enumeracao USB, timing do bxCAN, deteccao
  de harness, entrada em DFU, self test do F4, regioes da MPU.
- Nenhum pull request no upstream.
- O `import libusb` no `SConscript` do pandad so foi compilado no ambiente
  do CI, nao dentro de uma imagem de dispositivo comma.
- A base do firmware `1305b78c` esta dois commits (so firmware) atras do
  commit do panda que o openpilot fixava antes (`f38f504f`).

## Como usar

```
git clone -b revive-f4 --recurse-submodules https://github.com/kriptomad/openpilot.git
```

Para gravar uma black panda manualmente veja
[flashing/flash-black-panda-city-g7.pt-br.md](flashing/flash-black-panda-city-g7.pt-br.md).

## Relacao com este repositorio

O port do Honda City G7 (trilhas A e B) roda em arvores mais antigas
(flowpilot, openpilot v0.9.9). O pandarevive e o caminho para rodar a
mesma black panda no openpilot master atual. A PCB Hybrid Panda em
[../hardware/hybrid-panda](../hardware/hybrid-panda) e a alternativa de
hardware para quem nao tem uma black panda.
