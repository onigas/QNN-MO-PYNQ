# Română — Laboratoare QNN-MO-PYNQ

**Autorul adaptării didactice:** Prof. dr. ing. habil. Stefan Oniga  
**Bază tehnică:** [Xilinx/QNN-MO-PYNQ](https://github.com/Xilinx/QNN-MO-PYNQ). Licențele și mențiunile de copyright originale rămân în vigoare.

## Laboratoare pentru PYNQ-Z2

| Nr. | Temă | Notebook |
| --- | --- | --- |
| 01 | Introducere în învățarea automată și cuantizarea rețelelor | [Deschide 01](01_Machine_Learning_on_PYNQ.ipynb) |
| 02 | Clasificarea unor imagini ImageNet etichetate cu DoReFaNet | [Deschide 02](02_dorefanet-imagenet-samples.ipynb) |
| 03 | Clasificarea unei imagini proprii cu DoReFaNet | [Deschide 03](03_dorefanet-classification.ipynb) |
| 04 | Clasificarea imaginilor dintr-un director | [Deschide 04](04_dorefanet-imagenet-loop.ipynb) |
| 05 | Detecția obiectelor într-o imagine cu Tinier-YOLO | [Deschide 05](05_tiny-yolo-image.ipynb) |
| 06 | Detecția obiectelor într-un director de imagini | [Deschide 06](06_tiny-yolo-image-loop.ipynb) |
| 07 | Tinier-YOLO cu cameră USB, captură la cerere | [Deschide 07](07_tiny-yolo-usb-camera.ipynb) |
| 08 | Numărarea obiectelor, zona de interes și alarma prin LED0 | [Deschide 08](08_tiny-yolo-counting-zone-led.ipynb) |

## Laboratoare suplimentare pentru Raspberry Pi

| Nr. | Temă | Notebook |
| --- | --- | --- |
| 02.1 | DoReFaNet/ImageNet — referință software pe procesorul ARM | [Deschide 02.1](02.1_dorefanet-imagenet-rpi.ipynb) |
| 02.2 | MobileNet v1 cu OpenCV DNN | [Deschide 02.2](02.2_mobilenet-opencv-imagenet-rpi.ipynb) |
| 05.1 | Tinier-YOLO — referință CPU și captură de cameră | [Deschide 05.1](05.1_tiny-yolo-image-rpi.ipynb) |

**Toate cele 11 notebook-uri sunt traduse.** Acestea folosesc aceleași modele și resurse, disponibile în directorul părinte `notebooks/`. Nu copiați izolat notebook-uri într-un alt director fără a adapta căile către date.

**Stadiul verificării:** codul de inferență este preluat din versiunile engleze, iar în laboratoarele PYNQ a fost extinsă doar detectarea directorului cu resurse. Traducerile nu au fost încă testate pe plăcile fizice. Instrucțiunile pentru Raspberry Pi sunt disponibile în [ghidul tehnic în engleză](../../raspberry_pi/README.md).

[Selectarea limbii](../README.md) · [Versiunea engleză](../en/README.md) · [Pagina principală](../../README.md)
