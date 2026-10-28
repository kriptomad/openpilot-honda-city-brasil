# A5 - Impedance of the USB and CAN pairs (file stackup vs JLCPCB JLC7628)

Date: 2026-10-28 16:32:42. Script: `hardware/scripts/vpcb_a5_impedance.py` (read-only). Data: `impedance.json`.

## Method

- Single microstrip (outer layer over the first inner plane): Hammerstad and Jensen 1980 closed forms for Z0 and eps_eff, with the
  Wheeler/HJ strip-thickness correction (the same equations referenced by IPC-2141A section 4 and used in `step6_reports.py`).
- Edge-coupled pair: Kirschning and Jansen 1984 quasi-static even/odd-mode model (IEEE Trans. MTT-32, with the Jansen finite-thickness
  correction); Zdiff = 2 Zodd, Zcm = Zeven / 2. Cross-check column: IPC-2141 approximation Zdiff = 2 Z0 (1 - 0.48 exp(-0.96 s/h)).
- Reference plane assumed directly under the outer layer (F.Cu over In1.Cu, B.Cu over In2.Cu). On this board In1.Cu is GND outside the
  +3V3/+5V pours (see `step6_reports.py`), In2.Cu is a continuous GND plane; the numbers are the same for both outer layers because
  the prepreg is symmetric. KiCad DRC does not check impedance; nothing here is measured.

## Stackups

| Case | h (outer Cu to first plane) | er | outer Cu t | Note |
|---|---|---|---|---|
| file (.kicad_pcb stackup) | 0.2000 mm | 4.5 | 0.035 mm | outer Cu 35 um, prepreg 0.2 mm er 4.5, core 1.065 mm, inner Cu 17.5 um; total 1.59 mm |
| JLCPCB JLC7628 4-layer 1.6 mm | 0.2104 mm | 4.4 (1 GHz) / 4.6 (low f) | 0.035 mm | outer Cu 1 oz (0.035 mm), prepreg 7628 0.2104 mm, er 4.4 @ 1 GHz (4.6 low frequency), core 1.065 mm, inner Cu 0.5 oz; values from the JLCPCB impedance-calculator stackup table (not a fabricator-confirmed stackup for this order) |

Netclasses before this pass: CAN_DIFF w/gap = 0.25/0.20 mm; USB w/gap = 0.20/0.25 mm (USB pair was not routed coupled, see `usb-reroute.md`).

## file (.kicad_pcb stackup), er = 4.5

### Single-ended Z0

| w (mm) | Z0 (ohm) | eps_eff |
|---|---|---|
| 0.127 | 82.0 | 2.93 |
| 0.150 | 76.8 | 2.98 |
| 0.200 | 67.8 | 3.06 |
| 0.250 | 60.9 | 3.13 |
| 0.300 | 55.4 | 3.19 |
| 0.350 | 50.9 | 3.24 |
| 0.400 | 47.1 | 3.29 |
| 0.500 | 41.1 | 3.37 |

### Differential pairs

| Case | w (mm) | s (mm) | Zodd | Zeven | Zdiff K-J (ohm) | Zdiff IPC-2141 (ohm) | Zcm |
|---|---|---|---|---|---|---|---|
| CAN_DIFF rule now | 0.250 | 0.200 | 54.0 | 71.1 | **108.0** | 99.4 | 35.6 |
| USB rule now | 0.200 | 0.250 | 62.1 | 78.2 | **124.2** | 116.0 | 39.1 |
| 0.20/0.15 | 0.200 | 0.150 | 57.0 | 82.5 | **114.0** | 103.9 | 41.3 |
| 0.25/0.15 | 0.250 | 0.150 | 51.5 | 73.1 | **103.0** | 93.3 | 36.6 |
| 0.28/0.15 | 0.280 | 0.150 | 48.8 | 68.5 | **97.5** | 88.1 | 34.2 |
| 0.30/0.15 | 0.300 | 0.150 | 47.1 | 65.7 | **94.3** | 84.9 | 32.9 |
| 0.30/0.20 | 0.300 | 0.200 | 49.3 | 64.1 | **98.6** | 90.4 | 32.1 |
| 0.127/0.30 | 0.127 | 0.300 | 77.6 | 94.4 | **155.2** | 145.4 | 47.2 |
| 0.127/0.50 | 0.127 | 0.500 | 82.0 | 90.1 | **164.0** | 156.9 | 45.0 |
| 0.15/0.40 | 0.150 | 0.400 | 74.9 | 85.5 | **149.9** | 142.8 | 42.7 |

### Width needed for Zdiff = 90 ohm (K-J), by gap

| s (mm) | w (mm) | >= min track 0.127 |
|---|---|---|
| 0.127 | 0.312 | yes |
| 0.150 | 0.329 | yes |
| 0.200 | 0.356 | yes |
| 0.250 | 0.374 | yes |
| 0.300 | 0.387 | yes |
| 0.400 | 0.405 | yes |
| 0.500 | 0.416 | yes |

Gap needed at the CAN_DIFF width 0.25 mm: none (even an isolated 0.25 mm trace is below 90 ohm differential)

### Width needed for Zdiff = 120 ohm (K-J), by gap

| s (mm) | w (mm) | >= min track 0.127 |
|---|---|---|
| 0.127 | 0.164 | yes |
| 0.150 | 0.177 | yes |
| 0.200 | 0.200 | yes |
| 0.250 | 0.215 | yes |
| 0.300 | 0.226 | yes |
| 0.400 | 0.241 | yes |
| 0.500 | 0.250 | yes |

Gap needed at the CAN_DIFF width 0.25 mm: 0.503 mm

## JLCPCB JLC7628 4-layer 1.6 mm, er = 4.4

### Single-ended Z0

| w (mm) | Z0 (ohm) | eps_eff |
|---|---|---|
| 0.127 | 84.5 | 2.87 |
| 0.150 | 79.2 | 2.91 |
| 0.200 | 70.1 | 2.99 |
| 0.250 | 63.1 | 3.06 |
| 0.300 | 57.5 | 3.12 |
| 0.350 | 52.9 | 3.17 |
| 0.400 | 49.0 | 3.21 |
| 0.500 | 42.8 | 3.29 |

### Differential pairs

| Case | w (mm) | s (mm) | Zodd | Zeven | Zdiff K-J (ohm) | Zdiff IPC-2141 (ohm) | Zcm |
|---|---|---|---|---|---|---|---|
| CAN_DIFF rule now | 0.250 | 0.200 | 55.4 | 74.3 | **110.8** | 101.9 | 37.1 |
| USB rule now | 0.200 | 0.250 | 63.7 | 81.5 | **127.4** | 118.7 | 40.7 |
| 0.20/0.15 | 0.200 | 0.150 | 58.2 | 86.0 | **116.5** | 106.3 | 43.0 |
| 0.25/0.15 | 0.250 | 0.150 | 52.7 | 76.3 | **105.5** | 95.7 | 38.2 |
| 0.28/0.15 | 0.280 | 0.150 | 50.0 | 71.6 | **100.0** | 90.4 | 35.8 |
| 0.30/0.15 | 0.300 | 0.150 | 48.4 | 68.7 | **96.8** | 87.2 | 34.4 |
| 0.30/0.20 | 0.300 | 0.200 | 50.7 | 67.0 | **101.4** | 92.9 | 33.5 |
| 0.127/0.30 | 0.127 | 0.300 | 79.3 | 97.9 | **158.7** | 148.3 | 48.9 |
| 0.127/0.50 | 0.127 | 0.500 | 84.2 | 93.2 | **168.3** | 160.7 | 46.6 |
| 0.15/0.40 | 0.150 | 0.400 | 76.9 | 88.6 | **153.8** | 146.2 | 44.3 |

### Width needed for Zdiff = 90 ohm (K-J), by gap

| s (mm) | w (mm) | >= min track 0.127 |
|---|---|---|
| 0.127 | 0.328 | yes |
| 0.150 | 0.347 | yes |
| 0.200 | 0.376 | yes |
| 0.250 | 0.396 | yes |
| 0.300 | 0.411 | yes |
| 0.400 | 0.430 | yes |
| 0.500 | 0.442 | yes |

Gap needed at the CAN_DIFF width 0.25 mm: none (even an isolated 0.25 mm trace is below 90 ohm differential)

### Width needed for Zdiff = 120 ohm (K-J), by gap

| s (mm) | w (mm) | >= min track 0.127 |
|---|---|---|
| 0.127 | 0.171 | yes |
| 0.150 | 0.186 | yes |
| 0.200 | 0.211 | yes |
| 0.250 | 0.227 | yes |
| 0.300 | 0.240 | yes |
| 0.400 | 0.256 | yes |
| 0.500 | 0.266 | yes |

Gap needed at the CAN_DIFF width 0.25 mm: 0.358 mm

## JLCPCB JLC7628 4-layer 1.6 mm, er = 4.6

### Single-ended Z0

| w (mm) | Z0 (ohm) | eps_eff |
|---|---|---|
| 0.127 | 83.0 | 2.98 |
| 0.150 | 77.8 | 3.03 |
| 0.200 | 68.9 | 3.11 |
| 0.250 | 62.0 | 3.18 |
| 0.300 | 56.5 | 3.24 |
| 0.350 | 51.9 | 3.29 |
| 0.400 | 48.1 | 3.34 |
| 0.500 | 42.0 | 3.42 |

### Differential pairs

| Case | w (mm) | s (mm) | Zodd | Zeven | Zdiff K-J (ohm) | Zdiff IPC-2141 (ohm) | Zcm |
|---|---|---|---|---|---|---|---|
| CAN_DIFF rule now | 0.250 | 0.200 | 54.4 | 72.8 | **108.8** | 100.0 | 36.4 |
| USB rule now | 0.200 | 0.250 | 62.5 | 79.9 | **125.0** | 116.6 | 39.9 |
| 0.20/0.15 | 0.200 | 0.150 | 57.2 | 84.3 | **114.3** | 104.4 | 42.1 |
| 0.25/0.15 | 0.250 | 0.150 | 51.8 | 74.8 | **103.5** | 93.9 | 37.4 |
| 0.28/0.15 | 0.280 | 0.150 | 49.1 | 70.1 | **98.2** | 88.7 | 35.1 |
| 0.30/0.15 | 0.300 | 0.150 | 47.5 | 67.4 | **95.0** | 85.6 | 33.7 |
| 0.30/0.20 | 0.300 | 0.200 | 49.7 | 65.7 | **99.4** | 91.1 | 32.8 |
| 0.127/0.30 | 0.127 | 0.300 | 77.9 | 96.0 | **155.7** | 145.8 | 48.0 |
| 0.127/0.50 | 0.127 | 0.500 | 82.6 | 91.4 | **165.2** | 157.9 | 45.7 |
| 0.15/0.40 | 0.150 | 0.400 | 75.4 | 86.9 | **150.9** | 143.6 | 43.5 |

### Width needed for Zdiff = 90 ohm (K-J), by gap

| s (mm) | w (mm) | >= min track 0.127 |
|---|---|---|
| 0.127 | 0.316 | yes |
| 0.150 | 0.334 | yes |
| 0.200 | 0.363 | yes |
| 0.250 | 0.383 | yes |
| 0.300 | 0.397 | yes |
| 0.400 | 0.416 | yes |
| 0.500 | 0.428 | yes |

Gap needed at the CAN_DIFF width 0.25 mm: none (even an isolated 0.25 mm trace is below 90 ohm differential)

### Width needed for Zdiff = 120 ohm (K-J), by gap

| s (mm) | w (mm) | >= min track 0.127 |
|---|---|---|
| 0.127 | 0.164 | yes |
| 0.150 | 0.178 | yes |
| 0.200 | 0.202 | yes |
| 0.250 | 0.218 | yes |
| 0.300 | 0.230 | yes |
| 0.400 | 0.246 | yes |
| 0.500 | 0.256 | yes |

Gap needed at the CAN_DIFF width 0.25 mm: 0.433 mm

## Results and decisions

### USB (target 90 ohm differential, Full Speed 12 Mbit/s)

- Chosen rule for the USB netclass (JLC7628, er 4.4 at 1 GHz, rounded to 0.01 mm): **w = 0.35 mm, s = 0.15 mm** -> Zdiff = 89.6 ohm (er 4.6: 87.9 ohm; file stackup: 87.1 ohm), Zcm = 31.3 ohm.
- The gap 0.15 mm was preferred over 0.20 mm to keep the pair narrow (2w + s = 0.85 mm). Where the pair passes between the MCU
  decoupling capacitors (0.83 mm corridor, see `usb-reroute.md`) it is necked to 0.20/0.15 mm (about 116 ohm) for a few mm; the
  MCU pad stubs are 0.20 mm because the LQFP pads are 0.30 mm wide.
- USB FS edges are 4-20 ns; the whole pair is about 20 mm (< 1/20 of the edge length in FR-4), so the impedance mismatch of the old
  0.20 mm uncoupled tracks (about 70 ohm single-ended on JLC7628) is electrically tolerable. The rule change is for consistency with the
  fabricator stackup, not a functional fix.

### CAN (target 120 ohm differential, classic CAN 500 kbit/s, CAN FD up to 5 Mbit/s)

- Current CAN_DIFF rule 0.25/0.20 on JLC7628: Zdiff = 110.8 ohm (er 4.4), i.e. about 9 ohm (8 percent) below target - inside the
  usual +-10 percent fabricator tolerance, so not 'far off', but correctable without moving any track.
- 120 ohm on JLC7628 needs w = 0.211 mm at s = 0.20 mm, 0.24 mm at s = 0.30 mm, 0.266 mm at s = 0.50 mm (all above the 0.127 mm minimum track).
- Decision: keep the present pair centre pitch (0.45 mm) and narrow the copper: **CAN_DIFF w = 0.22 mm, s = 0.23 mm** -> Zdiff = 120.4 ohm
  (er 4.6: 118.1 ohm; file stackup: 117.3 ohm). Applied with `--apply-can`: netclass updated in the .kicad_pro and every CAN segment that was
  0.25 mm wide was set to 0.22 mm (BUS0_H: 2, BUS0_L: 3, BUS1N_H: 6, BUS1N_L: 7, BUS1O_H: 10, BUS1O_L: 7, BUS2_H: 6, BUS2_L: 5). Narrowing a track never reduces a clearance, so no DRC clearance item can result; the DRC
  after the pass is in `drc-cleanup.md`. The CAN segments are 6-21 mm F.Cu stubs between transceiver and OBD-C connector with mixed
  0.15-0.25 mm necks at the pads (not touched); at 500 kbit/s (and even CAN FD 5 Mbit/s, edges > 20 ns) they are far shorter than 1/10
  of the edge length, so the bus sees the external 120 ohm terminations, not the PCB trace. The change is a consistency improvement,
  not a functional fix. The actual gap of the existing pairs varies along the route (they were not routed as a strict coupled pair);
  only the rule and the widths were normalised.

### Limits

- Quasi-static formulas; the stated accuracy of the K-J model is about 1 percent for 0.1 <= w/h <= 10 and 0.1 <= s/h <= 10, which the
  cases above satisfy (w/h 0.6-2.4, s/h 0.6-2.4). Solder mask (about 0.01-0.02 mm, er ~3.5) typically lowers Zdiff by 2-4 ohm and is
  not modelled. Copper roughness and etch factor are not modelled. The fabricator's own impedance calculator should be used before
  ordering controlled impedance; nothing here was measured (no TDR, no board built).

---

pt-BR: Impedancia calculada analiticamente (Hammerstad-Jensen para trilha simples, Kirschning-Jansen para par acoplado) com o stackup
do ficheiro e com o JLC7628 da JLCPCB. USB: regra nova w=0.35 mm, s=0.15 mm (~90 ohm diferencial no JLC7628). CAN: a regra 0.25/0.20 dava
~111 ohm (-8 por cento); a classe CAN_DIFF passou a 0.22/0.23 mm (~120 ohm) mantendo o passo entre centros, e os segmentos CAN de 0.25 mm
foram estreitados para 0.22 mm (estreitar nunca cria erro de clearance). Em 500 kbit/s os stubs curtos sao tolerantes; nada foi medido fisicamente.
