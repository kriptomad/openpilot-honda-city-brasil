# software/

Three software tracks for the Honda City G7 (2023, Brazil), plus the port documentation that
does not belong to any single fork. Nothing has been tested in a car.

| Path | What it is |
|---|---|
| `openpilot-v0.9.9-city-g7/` (submodule, [kriptomad/openpilot](https://github.com/kriptomad/openpilot) branch `v0.9.9-cityg7-blackpanda`, commit `9ad0dbb08`) | openpilot v0.9.9 (tag `8aadf02b`, the last release with native black panda support) with the City G7 port. CI green on the fork. Large: more than 1 GB with its own submodules. |
| `opendbc-v0.9.9-city-g7/` (submodule, [kriptomad/opendbc](https://github.com/kriptomad/opendbc) branch `firmwarecityg7-v0.9.9`, commit `6cbc8005`) | opendbc at the v0.9.9 base (`e370a036`) with the City G7 car port cherry-picked byte-for-byte from upstream `43006b9a`, plus the `HAS_EPB`, `steerActuatorDelay`, `ki` and `GEARBOX_CVT` backports. Used by the openpilot submodule above. |
| `flowpilot-city-g7/` (submodule, [kriptomad/flowpilot-city-g7](https://github.com/kriptomad/flowpilot-city-g7) branch `flowpilot-city-g7-brazil`, commit `94248de`) | flowpilot standalone Android APK (jagheterfredrik snapshot `9ea918ea`) with the City G7 car layer and the repaired build pipeline. APK release `v0.1-city-g7-brazil`. |
| `openpilot-port/` | Documentation of the openpilot/opendbc v0.9.9 port: [readme.md](openpilot-port/readme.md) (what was done, how it was validated, bench checklist), [auditoria-port-city-v099.md](openpilot-port/auditoria-port-city-v099.md) (first audit), [audit2/](openpilot-port/audit2) (independent adversarial audit with its replay scripts), [patches/](openpilot-port/patches) (`git format-patch` series: 9 for opendbc, 10 for openpilot), [tools/](openpilot-port/tools) (DBC comparison, route rate scan, branch note helper). |
| `flowpilot-port/` | Documentation of the flowpilot port: [flowpilot-scope.md](flowpilot-port/flowpilot-scope.md) (phase A research: state of flowpilot and its forks, device requirements), [port-city-flowpilot.md](flowpilot-port/port-city-flowpilot.md) (phase B: files changed, deviations from upstream, APK build, install, what is not verified), [tests-windows/](flowpilot-port/tests-windows) (shims and runners used to execute the car and safety tests on Windows, with their logs). |

Which firmware goes with which track is explained in [../firmware/readme.md](../firmware/readme.md).
The main project README ([../README.md](../README.md)) has the quick start for each track.

Initialise a single track with `git submodule update --init [--recursive] software/<name>`.

---

pt-BR: tres trilhas de software (openpilot v0.9.9, opendbc v0.9.9 e flowpilot, como
submodulos) e a documentacao dos ports em `openpilot-port/` e `flowpilot-port/`. Nada foi
testado em carro. O firmware correspondente a cada trilha esta em `../firmware/readme.md`.
