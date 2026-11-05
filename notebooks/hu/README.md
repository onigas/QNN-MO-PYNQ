# Magyar — QNN-MO-PYNQ laboratóriumok

**Az oktatási feldolgozás szerzője:** Prof. dr. ing. habil. Stefan Oniga  
**Műszaki alap:** [Xilinx/QNN-MO-PYNQ](https://github.com/Xilinx/QNN-MO-PYNQ); az eredeti licencek és szerzői jogi megjegyzések megmaradnak.

## PYNQ-Z2 laboratóriumok

| Szám | Téma | Notebook |
| --- | --- | --- |
| 01 | Bevezetés a gépi tanulásba és a kvantálásba | [01 megnyitása](01_Machine_Learning_on_PYNQ.ipynb) |
| 02 | ImageNet-képek osztályozása DoReFaNet hálózattal | [02 megnyitása](02_dorefanet-imagenet-samples.ipynb) |
| 03 | Saját kép osztályozása | [03 megnyitása](03_dorefanet-classification.ipynb) |
| 04 | Képek sorozatos osztályozása | [04 megnyitása](04_dorefanet-imagenet-loop.ipynb) |
| 05 | Objektumok felismerése egy képen | [05 megnyitása](05_tiny-yolo-image.ipynb) |
| 06 | Objektumok felismerése képkönyvtárban | [06 megnyitása](06_tiny-yolo-image-loop.ipynb) |
| 07 | Objektumfelismerés USB-kamerával | [07 megnyitása](07_tiny-yolo-usb-camera.ipynb) |
| 08 | Objektumszámlálás, ROI-zóna és LED0-riasztás | [08 megnyitása](08_tiny-yolo-counting-zone-led.ipynb) |

## Raspberry Pi kiegészítő laboratóriumok

| Szám | Téma | Notebook |
| --- | --- | --- |
| 02.1 | DoReFaNet/ImageNet ARM64 CPU-n | [02.1 megnyitása](02.1_dorefanet-imagenet-rpi.ipynb) |
| 02.2 | MobileNet + OpenCV DNN CPU-n | [02.2 megnyitása](02.2_mobilenet-opencv-imagenet-rpi.ipynb) |
| 05.1 | Tinier-YOLO képfájllal vagy kameraképpel | [05.1 megnyitása](05.1_tiny-yolo-image-rpi.ipynb) |

[Raspberry Pi telepítési útmutató (angolul)](../../raspberry_pi/README.md)

**Fontos:** a fordított notebookok a közös `notebooks/` könyvtár modelljeit és adatfájljait használják; ne helyezze át őket külön. A számítási kód változatlan maradt; a PYNQ 02–08 laboratóriumokban csak a szülőkönyvtár adatkeresése bővült. A Python által kiírt üzenetek továbbra is angolul jelenhetnek meg. A fordított példányokat fizikailag még nem teszteltük külön.

[Nyelvválasztás](../README.md) · [Projekt főoldala](../../README.md) · [Angol változat](../en/README.md)
