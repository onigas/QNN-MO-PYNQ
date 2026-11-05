# Magyar — QNN-MO-PYNQ laboratóriumok

**Az oktatási feldolgozás szerzője:** Prof. dr. ing. habil. Stefan Oniga  
**Műszaki alap:** [Xilinx/QNN-MO-PYNQ](https://github.com/Xilinx/QNN-MO-PYNQ). Az eredeti licencek és szerzői jogi megjegyzések változatlanul érvényesek.

## PYNQ-Z2 laboratóriumok

| Szám | Téma | Notebook |
| --- | --- | --- |
| 01 | Bevezetés a gépi tanulásba és a hálózatok kvantálásába | [01 megnyitása](01_Machine_Learning_on_PYNQ.ipynb) |
| 02 | Címkézett ImageNet-képek osztályozása DoReFaNet hálózattal | [02 megnyitása](02_dorefanet-imagenet-samples.ipynb) |
| 03 | Saját kép osztályozása DoReFaNet hálózattal | [03 megnyitása](03_dorefanet-classification.ipynb) |
| 04 | Képkönyvtár sorozatos osztályozása | [04 megnyitása](04_dorefanet-imagenet-loop.ipynb) |
| 05 | Objektumok felismerése egy képen Tinier-YOLO modellel | [05 megnyitása](05_tiny-yolo-image.ipynb) |
| 06 | Objektumfelismerés képfájlok sorozatában | [06 megnyitása](06_tiny-yolo-image-loop.ipynb) |
| 07 | USB-kamera és kérésre történő objektumfelismerés | [07 megnyitása](07_tiny-yolo-usb-camera.ipynb) |
| 08 | Objektumszámlálás, célzóna és LED0-riasztás | [08 megnyitása](08_tiny-yolo-counting-zone-led.ipynb) |

## Kiegészítő Raspberry Pi-laboratóriumok

| Szám | Téma | Notebook |
| --- | --- | --- |
| 02.1 | DoReFaNet/ImageNet — ARM CPU-referencia | [02.1 megnyitása](02.1_dorefanet-imagenet-rpi.ipynb) |
| 02.2 | MobileNet v1 és OpenCV DNN | [02.2 megnyitása](02.2_mobilenet-opencv-imagenet-rpi.ipynb) |
| 05.1 | Tinier-YOLO — CPU-referencia és kamerakép | [05.1 megnyitása](05.1_tiny-yolo-image-rpi.ipynb) |

**Mind a 11 notebook fordítása elkészült.** Ugyanazokat a modelleket és erőforrásokat használják, amelyeket a szülő `notebooks/` könyvtár tartalmaz. Ne másolja át a notebookokat önmagukban más könyvtárba az elérési utak módosítása nélkül.

**Ellenőrzési állapot:** az inferenciakód az angol változatból származik; a PYNQ-feladatokban csak a közös erőforráskönyvtár felkutatása bővült. A lefordított példányokat külön, valódi hardveren még nem teszteltük. A Raspberry Pi telepítési útmutatója [angolul](../../raspberry_pi/README.md) olvasható.

[Nyelvválasztás](../README.md) · [Angol változat](../en/README.md) · [A projekt főoldala](../../README.md)
