# Română — Laboratoare QNN-MO-PYNQ

**Autorul adaptării didactice:** Prof. dr. ing. habil. Stefan Oniga  
**Fundament tehnic:** [Xilinx/QNN-MO-PYNQ](https://github.com/Xilinx/QNN-MO-PYNQ); licențele și creditele originale rămân valabile.

## Laboratoarele PYNQ-Z2

| Nr. | Subiect | Notebook |
| --- | --- | --- |
| 01 | Introducere în învățarea automată și cuantizare | [Deschide 01](01_Machine_Learning_on_PYNQ.ipynb) |
| 02 | Clasificarea imaginilor ImageNet cu DoReFaNet | [Deschide 02](02_dorefanet-imagenet-samples.ipynb) |
| 03 | Clasificarea unei imagini proprii | [Deschide 03](03_dorefanet-classification.ipynb) |
| 04 | Clasificarea unui director de imagini | [Deschide 04](04_dorefanet-imagenet-loop.ipynb) |
| 05 | Detecția obiectelor într-o imagine | [Deschide 05](05_tiny-yolo-image.ipynb) |
| 06 | Detecția obiectelor într-un director | [Deschide 06](06_tiny-yolo-image-loop.ipynb) |
| 07 | Detecția folosind o cameră USB | [Deschide 07](07_tiny-yolo-usb-camera.ipynb) |
| 08 | Numărarea obiectelor, zona ROI și alarma LED0 | [Deschide 08](08_tiny-yolo-counting-zone-led.ipynb) |

## Laboratoarele suplimentare Raspberry Pi

| Nr. | Subiect | Notebook |
| --- | --- | --- |
| 02.1 | DoReFaNet/ImageNet pe CPU ARM64 | [Deschide 02.1](02.1_dorefanet-imagenet-rpi.ipynb) |
| 02.2 | MobileNet + OpenCV DNN pe CPU | [Deschide 02.2](02.2_mobilenet-opencv-imagenet-rpi.ipynb) |
| 05.1 | Tinier-YOLO, fișier imagine sau captură de cameră | [Deschide 05.1](05.1_tiny-yolo-image-rpi.ipynb) |

[Ghidul Raspberry Pi (în engleză)](../../raspberry_pi/README.md)

**Notă importantă:** fișierele traduse folosesc modelele și resursele din directorul părinte `notebooks/`. Nu le mutați separat de repository. Codul de calcul a fost păstrat; în laboratoarele PYNQ 02–08 s-a extins numai căutarea datelor în directorul părinte. Mesajele produse de Python pot rămâne în engleză. Copiile traduse nu au fost încă validate separat pe plăcile fizice.

[Selectarea limbii](../README.md) · [Pagina principală](../../README.md) · [Versiunea engleză](../en/README.md)
