# firmware/

panda firmware for the black panda (STM32F413) and for the Hybrid Panda (STM32H725).
Nothing here has been executed on a board.

| Path | What it is | Goes with |
|---|---|---|
| `panda-revive-f4/` (submodule, [kriptomad/panda](https://github.com/kriptomad/panda) branch `revive-f4`, commit `a8225ef3`) | Current commaai/panda master with the STM32F4 / black panda target restored. Compiles (debug and release), MISRA clean, `test.sh` green. | openpilot master with the pandarevive host side: [kriptomad/openpilot](https://github.com/kriptomad/openpilot) branch `revive-f4` (commits on commaai `0152aab4`, see [../docs/pandarevive.md](../docs/pandarevive.md) and [kriptomad/pandarevive](https://github.com/kriptomad/pandarevive)). Also the tree for bench tests of the firmware itself. |
| `panda-hybrid-h725/` (submodule, same fork, branch `hybrid-h725`, commit `78e37994`) | `revive-f4` plus the Hybrid Panda target: `HW_TYPE_HYBRID_PANDA` (11), targets `panda_h7_hybrid` and `panda_h7_ldo`, Direct SMPS / VFBSMPS handling. Compiles, MISRA clean. | The Hybrid Panda PCB in [../hardware/hybrid-panda](../hardware/hybrid-panda) (no board exists yet). |
| `prebuilt/flowpilot-black-panda/` | Black panda binaries built from the panda tree embedded in the flowpilot fork (commaai/panda `abdc4185`): `bootstub.panda.bin`, `panda.bin`, `panda.bin.signed`, `panda.elf`, `version` (`DEV-a2f1983c-DEBUG`), `SHA256SUMS.txt`. | The flowpilot APK ([../software/flowpilot-city-g7](../software/flowpilot-city-g7)). |
| `prebuilt/revive-f4-black-panda/` | Black panda binaries built from `panda-revive-f4`: `bootstub.panda.bin`, `panda.bin.signed`, `version` (`DEV-e78c41e6-DEBUG`), `SHA256SUMS.txt`. | Bench tests of the `revive-f4` firmware with the matching `panda` Python package from the submodule. Not usable with the flowpilot APK or openpilot v0.9.9. |

The openpilot v0.9.9 track has no prebuilt binary: `scons` in
[../software/openpilot-v0.9.9-city-g7](../software/openpilot-v0.9.9-city-g7) builds the
panda submodule (commaai/panda `e462c34d`) and `pandad` flashes it at start-up.

The three trees speak different USB protocol versions and are not interchangeable: flash the
one that matches the software you will run. All prebuilt binaries are signed with comma's
public debug key; a board with a comma release bootstub will not accept them until the
bootstub is replaced over DFU.

Flashing procedure (SW1 = BOOT0 on the Loetkolben BlackPanda v2, `PandaDFU(None).recover()`
then `Panda().flash(fn=...)`): [../docs/flashing/flash-black-panda-city-g7.md](../docs/flashing/flash-black-panda-city-g7.md)
([pt-BR](../docs/flashing/flash-black-panda-city-g7.pt-br.md)). Firmware port report for the
Hybrid Panda: [../hardware/research/hybrid-fw-port.md](../hardware/research/hybrid-fw-port.md).

Verify a download with `sha256sum -c SHA256SUMS.txt` (or `Get-FileHash` on Windows) before
flashing.

---

pt-BR: firmware do panda para o black panda (STM32F413) e para o Hybrid Panda (STM32H725).
Dois submodulos (`revive-f4`, `hybrid-h725`) e binarios pre-compilados em `prebuilt/`. As
tres arvores de firmware nao sao intercambiaveis; use a que corresponde ao software. Nada foi
executado em placa. Procedimento de gravacao em `docs/flashing/`.
