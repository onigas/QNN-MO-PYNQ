# Raspberry Pi 4 — comparație CPU cu PYNQ

Notebookuri separate, cu modelele și greutățile originale:

- [02.1 — DoReFaNet ImageNet](../notebooks/02.1_dorefanet-imagenet-rpi.ipynb)
- [05.1 — Tinier-YOLO, fișier sau cameră Logitech](../notebooks/05.1_tiny-yolo-image-rpi.ipynb)

Ținta este **Raspberry Pi 4 Model B, 4 GB, Debian 13 Trixie ARM64**.
`uname -m` trebuie să afișeze `aarch64`. Nu instalați pachetul PYNQ și nu executați
`pip install .` pentru acest port. Notebookurile PYNQ 01–08 rămân separate.

**Stare:** adaptoare și notebookuri pregătite pentru validare pe dispozitiv.
Cele cinci teste locale au trecut, inclusiv adaptorul Darknet compilat pe x86_64.
Celulele ambelor notebookuri au fost executate local cu ieșirea nucleului ARM64 înlocuită
de date de referință; aceasta verifică fluxul Python, nu corectitudinea inferenței pe Pi. Rulați obligatoriu cele două verificări de referință de mai jos.
Nu sunt publicate rezultate de performanță măsurate pe Raspberry Pi.

## 1. Instalare pe Pi

Păstrați uStreamer și Home Assistant în funcțiune. Nu este necesară modificarea camerei.
Dintr-un terminal pe Raspberry Pi:

```bash
sudo apt update
sudo apt install -y git build-essential python3-venv python3-numpy python3-opencv python3-matplotlib python3-pil python3-notebook python3-ipykernel python3-threadpoolctl libbz2-1.0 libssl3t64 zlib1g
cd ~
git clone --depth=1 https://github.com/onigas/QNN-MO-PYNQ.git
cd QNN-MO-PYNQ
bash raspberry_pi/setup_rpi.sh
```

Dacă aveți deja un checkout fără modificări locale, folosiți `git pull --ff-only` în el,
apoi comanda de instalare. Nu suprascrieți notebookuri modificate. Folosiți o cale scurtă,
fără spații (de exemplu `~/QNN-MO-PYNQ`), deoarece Darknet este un proiect C vechi.
Instalarea descarcă surse și decomprimă greutăți mari; sunt necesare spațiu liber și internet.
Pe Pi cu 4 GB, închideți alte notebookuri de inferență înainte de DoReFaNet.

Scriptul creează un mediu local `.venv` care folosește pachetele Python Debian,
descarcă și verifică SHA256 pentru pachetul Debian ARM64 `libzip4`, îl extrage doar în
`.deps/libzip4`, și compilează Darknet CPU cu două joburi.
Nu înlocuiește libzip din sistem și nu creează legături între ABI-urile libzip5 și libzip4.
Bibliotecile software originale `qnn/libraries/ultra96/lib_sw_W1A2.so` și `lib_sw_W1A3.so`
sunt binare ARM64; adaptoarele verifică SHA256 înainte de încărcare. Ele nu folosesc FPGA.

Darknet provine din `giuliogamba/darknet`, commit fix
`3bbbe379de1ecd8d8e533b73795f105f650da8e5`, cu GPU/CUDNN/OpenCV/OpenMP dezactivate.
`darknet_compat.h` declară funcția `load_alphabet_path` care lipsește din antetul original;
acest lucru evită trunchierea pointerilor pe 64 de biți. `-fcommon` permite definițiile
globale vechi. Sursele externe sunt ținute în `.deps`, nu instalate global.

## 2. Verificare înainte de benchmark

În directorul rădăcină al repository-ului:

```bash
raspberry_pi/.venv/bin/python raspberry_pi/validate_native.py --load-only
raspberry_pi/.venv/bin/python raspberry_pi/validate_native.py --model dorefanet
raspberry_pi/.venv/bin/python raspberry_pi/validate_native.py --model tinier-yolo
```

Primul test verifică numai încărcarea bibliotecilor. Următoarele execută efectiv nucleele
CPU cu intrările binare din `tests/Test_image` și compară octeții canalelor valide cu
`verification.bin`, excluzând padding-ul, exact ca `OffloadUtils::verifyBuffers`.
Pentru DoReFaNet, bufferul de intrare din fișier are 393216 octeți, dar intrarea efectivă
are 279936; se folosesc primii 279936, ca în executabilul original C++.
Versiunea inițială a validatorului transmitea întregul fișier și compara inclusiv padding-ul;
actualizați repository-ul și repetați testul dacă ați folosit acea versiune.
Continuați la notebookuri numai după `PASS` pentru modelul respectiv. La `FAIL`, opriți
comparația și păstrați mesajul complet pentru diagnostic.

Referința C++/HLS nu este un runtime AI optimizat pentru Pi. Inferența poate dura minute.
La fiecare 15 secunde apare timpul scurs, fără estimare de progres. Întreruperea din Jupyter
poate fi întârziată până la revenirea apelului nativ. Nu porniți o a doua inferență în paralel.

## 3. Pornire Jupyter

```bash
bash raspberry_pi/start_jupyter.sh
```

Deschideți URL-ul local cu token afișat de Jupyter. Pentru acces de pe alt calculator,
folosiți un tunel SSH către portul afișat (exemplu pentru portul 8888):

```bash
ssh -L 8888:127.0.0.1:8888 UTILIZATOR@ADRESA_RPI
```

Apoi deschideți în browser URL-ul `127.0.0.1:8888` cu tokenul serverului de pe Pi.
Scriptul limitează BLAS/OpenMP la un thread; notebookurile aplică și `threadpoolctl`.
Rulați celulele în ordine. La final executați celula de eliberare a memoriei.

## 4. Aceeași cameră Logitech pentru Home Assistant și teste

uStreamer continuă să dețină camera USB și să transmită către Home Assistant.
Notebookul 05.1 cere doar o imagine statică de la serverul existent:

```python
SOURCE = 'snapshot'
SNAPSHOT_URL = 'http://127.0.0.1:8080/snapshot'
```

Nu folosește `VideoCapture`, nu deschide `/dev/video0` și nu oprește servicii.
URL-ul trebuie să returneze JPEG/PNG, nu fluxul multipart de la `/stream`.
Dacă uStreamer ascultă pe alt port, schimbați URL-ul. Un timeout sau o eroare HTTP trebuie
rezolvată verificând serverul existent, fără a porni un al doilea proces pe cameră.
05.1 procesează un singur cadru per rulare; nu este un detector video în timp real.

Captura stă în memorie. Darknet cere căi de fișiere: intrarea PNG și ieșirile lui temporare
sunt create în `/dev/shm` și șterse la ieșirea din context, inclusiv la excepții Python.
Nu există fallback pe cardul SD și nu sunt salvate automat capturi sau fișiere JSON.
O terminare forțată a procesului poate lăsa temporare în RAM până la curățare/restart.
Jupyter poate include imaginile afișate în notebook la salvare; ștergeți ieșirile înainte
de salvare dacă nu doriți să persiste acolo.

## 5. Comparație corectă

Folosiți inițial `SOURCE = 'file'` și exact același fișier pe ambele platforme.
02.1 folosește implicit `n01484850_0.jpg`, 05.1 `dog.jpg`.
Fiecare notebook afișează SHA256 al intrării și al ieșirii cuantizate.
Un cadru nou de cameră nu este aceeași intrare ca un cadru capturat anterior pe PYNQ.

| Măsurătoare | Include |
| --- | --- |
| `quantized_core_s` | Numai apelul `classifier.inference`, echivalent limitei offload PYNQ |
| `first_cpu_s`, `last_cpu_s` | Convoluția inițială și FC/convoluția finală pe CPU |
| `packing_s`, `unpacking_s` | Conversia bufferelor pentru nucleul cuantizat |
| `preprocess_s` | Citire/transformare imagine pentru model |
| `decode_draw_ram_io_s` (05.1) | Decodare, desenare, fișiere temporare în RAM |
| Achiziție snapshot | Raportată separat, în afara inferenței |

Suma etapelor din noile notebookuri nu are aceleași limite ca suma graficelor PYNQ 02/05,
care nu includ preprocesarea și bufferele. Încărcarea modelului, afișarea graficelor și
calculul hash-urilor sunt în afara etapelor cronometrate. Raportul CPU/FPGA descrie această
referință software, nu viteza maximă posibilă a unui Raspberry Pi cu un runtime optimizat.

Folosiți o rulare de încălzire, apoi mai multe măsurători și mediana. Notați temperatura,
alimentarea, versiunea OS/NumPy/BLAS, limita de threaduri și faptul că uStreamer este activ.
Diferențele BLAS pot afecta ușor etapele float; verificați mai întâi ieșirea cuantizată.
Nu sunt modificate pragurile/greutățile pentru a produce rezultate mai favorabile.

## Teste pentru dezvoltare

```bash
raspberry_pi/.venv/bin/python -m unittest discover -s tests -p 'test_rpi*.py' -v
```

Aceste teste verifică împachetarea biților, snapshot HTTP, curățarea temporarelor RAM,
structura notebookurilor și adaptorul Darknet dacă biblioteca sa este disponibilă.
Nu înlocuiesc verificarea inferenței ARM64 din secțiunea 2.
