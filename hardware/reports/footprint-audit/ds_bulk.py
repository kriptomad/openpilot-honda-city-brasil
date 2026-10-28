#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ds_bulk.py - download the datasheet list into ./datasheets with retries (proxy is flaky)."""
import urllib.request, time, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
DSD = os.path.join(HERE, "datasheets")
os.makedirs(DSD, exist_ok=True)
URLS = {
 "SOT782-1":"https://www.nxp.com/docs/en/package-information/SOT782-1.pdf",
 "TJA1042":"https://www.nxp.com/docs/en/data-sheet/TJA1042.pdf",
 "TPS5450":"https://www.ti.com/lit/ds/symlink/tps5450.pdf",
 "STM32H725ZG":"https://www.st.com/resource/en/datasheet/stm32h725zg.pdf",
 "AP22615":"https://www.diodes.com/assets/Datasheets/AP22615.pdf",
 "SMAJ":"https://www.diodes.com/assets/Datasheets/ds18005.pdf",
 "PESD2CAN":"https://assets.nexperia.com/documents/data-sheet/PESD2CAN.pdf",
 "PDTC114EU":"https://assets.nexperia.com/documents/data-sheet/PDTC114E_SER.pdf",
 "BAS40WS":"https://assets.nexperia.com/documents/data-sheet/BAS40_SER.pdf",
 "BAT54S":"https://assets.nexperia.com/documents/data-sheet/BAT54_SER.pdf",
 "BAS70H":"https://assets.nexperia.com/documents/data-sheet/BAS70_SER.pdf",
 "DDTA143ECA":"https://www.diodes.com/assets/Datasheets/ds30390.pdf",
 "B320A":"https://www.diodes.com/assets/Datasheets/ds13006.pdf",
 "XL1509":"https://datasheet.lcsc.com/lcsc/1809050422_XLSEMI-XL1509-5-0E1_C61063.pdf",
 "TYPEC31M04":"https://atta.szlcsc.com/upload/public/pdf/source/20190321/C129018_ECAF745BBC5FC08427E0CBD0F9A58A2A.pdf",
 "FMB1921":"https://atta.szlcsc.com/upload/public/pdf/source/20210824/394DCB7C803784CE665F52BCF49E41B5.pdf",
 "DFE201610E":"https://www.murata.com/products/productdata/8807028637726/DFE201610E.pdf",
 "SOT23_nexperia":"https://assets.nexperia.com/documents/package-information/SOT23.pdf",
 "SOT323_nexperia":"https://assets.nexperia.com/documents/package-information/SOT323.pdf",
 "SOD323_nexperia":"https://assets.nexperia.com/documents/package-information/SOD323.pdf",
 "SOD123F_nexperia":"https://assets.nexperia.com/documents/package-information/SOD123F.pdf",
 "SM540C":"https://www.mccsemi.com/pdf/Products/SM520C-SM5100C(SMC).pdf",
 "HY12P03C2":"https://datasheet.lcsc.com/lcsc/2304140030_HOOYI-HY12P03C2_C5199101.pdf",
 "SMMS0650":"https://datasheet.lcsc.com/lcsc/1811061709_Sunlord-SMMS0650-470M_C169437.pdf",
 "USBA_10_0QHHTZB6_3":"https://datasheet.lcsc.com/lcsc/1912111437_Korean-Hroparts-Elec-USB-A-10-0QHHTZB6-3_C698534.pdf",
 "X322525MOB4SI":"https://datasheet.lcsc.com/lcsc/1810171117_Yangxing-Tech-X322525MOB4SI_C9006.pdf",
 "SKQG":"https://tech.alpsalpine.com/e/products/detail/SKQGABE010/",
 "AP22615_lcsc":"https://datasheet.lcsc.com/lcsc/2108071730_Diodes-Incorporated-AP22615AWU-7_C2680357.pdf",
}
only = sys.argv[1:]
for k, u in URLS.items():
    if only and k not in only:
        continue
    f = os.path.join(DSD, k + ".pdf")
    if os.path.exists(f) and os.path.getsize(f) > 5000:
        print(k, "cached", os.path.getsize(f)); continue
    for attempt in range(6):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36", "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if len(data) < 2000:
                print(k, "attempt", attempt, "short", len(data)); time.sleep(5); continue
            open(f, "wb").write(data)
            print(k, "OK", len(data), data[:5], flush=True)
            break
        except Exception as e:
            print(k, "attempt", attempt, "ERR", str(e)[:100], flush=True); time.sleep(5)
