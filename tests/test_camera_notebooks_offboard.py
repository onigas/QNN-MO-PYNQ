"""Off-board smoke/regression checks; no FPGA, USB or native Darknet validation.

Run from a checkout: python tests/test_camera_notebooks_offboard.py
Requires numpy, pillow, matplotlib. All notebook outputs remain empty on disk.
"""
import ast, contextlib, ctypes, importlib.util, io, json, os, sys, tempfile, types
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
NB_DIR = ROOT / 'notebooks' if (ROOT / 'notebooks').is_dir() else HERE
UTILS = ROOT / 'qnn/utils.py' if (ROOT / 'qnn/utils.py').is_file() else ROOT / 'mo_audit02/utils.py'
CFG = HERE / 'yolo.cfg' if (HERE / 'yolo.cfg').is_file() else ROOT / 'qnn/params/tinier-yolo-bwn-3bit-relu-nomaxpool.cfg'
spec = importlib.util.spec_from_file_location('original_utils', UTILS)
utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils)

class Hardware:
    overlay = None
    fail_base = False
    leds = [0] * 4

class Accelerator:
    instances = []
    fail = False
    def __init__(self):
        self.init = False
        self.instances.append(self)
    def load_network(self):
        return {'conv1': {'input': [2, 208, 208]}, 'conv7': {'output': [1, 13, 13]}}
    def init_accelerator(self):
        Hardware.overlay = 'yolo'
        self.init = True
    def deinit_accelerator(self):
        self.init = False
    def get_accel_buffer(self, channels, dim):
        assert self.init and Hardware.overlay == 'yolo'
        return np.zeros((dim, dim, channels), np.uint8)
    def prepare_buffer(self, values):
        assert values.shape == (2, 208, 208)
        return values.astype(np.uint8)
    def inference(self, inputs, output):
        assert self.init and Hardware.overlay == 'yolo' and inputs.flags.c_contiguous
        if self.fail:
            raise RuntimeError('simulated FPGA error')
        output[:] = 1
    def postprocess_buffer(self, values):
        return values.flatten().astype(np.float32)

class Led:
    def __init__(self, index): self.index = index
    def write(self, value):
        assert Hardware.overlay == 'base'
        Hardware.leds[self.index] = value
    def off(self): self.write(0)

class BaseOverlay:
    def __init__(self, bitfile):
        assert bitfile == 'base.bit'
        assert not any(a.init for a in Accelerator.instances), 'FPGA replaced before deinit'
        if Hardware.fail_base:
            raise RuntimeError('simulated base.bit missing')
        Hardware.overlay = 'base'
        self.leds = [Led(i) for i in range(4)]
    def is_loaded(self): return Hardware.overlay == 'base'

class Camera:
    instances = []
    opened = True
    bad_frame = False
    def __init__(self, device, backend):
        self.released = False
        self.instances.append(self)
    def isOpened(self): return self.opened
    def set(self, *args): return True
    def read(self):
        if self.bad_frame: return False, None
        return True, np.full((480, 640, 3), [20, 80, 200], dtype=np.uint8)
    def release(self): self.released = True

class CV2(types.ModuleType):
    CAP_V4L2 = 200
    CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT = 3, 4
    COLOR_BGR2RGB = 4
    VideoCapture = Camera
    def cvtColor(self, frame, conversion): return frame[:, :, ::-1].copy()
    def imwrite(self, path, frame):
        Image.fromarray(frame[:, :, ::-1]).save(path)
        return True

class CFunc:
    def __init__(self, fn): self.fn = fn
    def __call__(self, *args): return self.fn(*args)

class CImage(ctypes.Structure):
    _fields_ = [('w', ctypes.c_int), ('h', ctypes.c_int), ('c', ctypes.c_int),
                ('data', ctypes.POINTER(ctypes.c_float))]

class Darknet(types.ModuleType):
    def __init__(self):
        super().__init__('darknet')
        self.networks, self.images = set(), {}
        self.serial = 1000
        self.lib = types.SimpleNamespace(parse_network_cfg=CFunc(self.parse),
            free_network=CFunc(self.free), forward_region_layer_pointer_nolayer=CFunc(self.forward),
            draw_detection_python=CFunc(self.draw))
    def parse(self, path):
        self.serial += 1
        self.networks.add(self.serial)
        return self.serial
    def free(self, pointer): self.networks.remove(pointer)
    def forward(self, pointer, output): assert pointer in self.networks
    def draw(self, pointer, image, threshold, hierarchy, names, root, output, probs):
        with Image.open(image.decode()) as im: im.save(output.decode()+'.png')
        Path(probs.decode()).write_text('person: 80%\n')
    def load_image(self, path, width, height):
        values = np.ones((3, 416, 416), np.float32)
        pointer = values.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        self.images[ctypes.addressof(pointer.contents)] = values
        return CImage(416, 416, 3, pointer)
    def letterbox_image(self, image, width, height): return self.load_image(b'', width, height)
    def free_image(self, image): self.images.pop(ctypes.addressof(image.data.contents))

class Control:
    def __init__(self, *args, **kwargs):
        self.disabled, self.closed, self.callbacks = False, False, []
        self.value = args[0] if args else ''
    def on_click(self, fn): self.callbacks.append(fn)
    def click(self):
        if not self.disabled:
            for fn in self.callbacks: fn(self)
    def close(self): self.closed = True
    def __enter__(self): return self
    def __exit__(self, *args): return False

WIDGETS = types.ModuleType('ipywidgets')
for name in ('Button', 'HTML', 'Output', 'VBox', 'HBox'): setattr(WIDGETS, name, Control)
IP = types.ModuleType('IPython')
IP.get_ipython = lambda: None
IP.version_info = (8, 0)
DISPLAY = types.ModuleType('IPython.display')
shown = []
DISPLAY.display = lambda *values: shown.extend(values)

VOC = 'aeroplane bicycle bird boat bottle bus car cat chair cow diningtable dog horse motorbike person pottedplant sheep sofa train tvmonitor'.split()

def synthetic_head(row=6, col=6, anchor=0, class_id=14):
    head = np.zeros((5, 25, 13, 13), np.float32)
    head[:, 4] = -30
    head[anchor, 4, row, col] = 12
    head[anchor, 5+class_id, row, col] = 12
    return head.reshape(125, 13, 13)

def check_decoder(env):
    decode, zone = env['decode_boxes'], env['apply_zone']
    result = decode(synthetic_head(), 640, 480)
    assert len(result) == 1 and result[0]['label'] == 'person'
    np.testing.assert_allclose(result[0]['center'], [320, 240])
    np.testing.assert_allclose(result[0]['box'], [320-1.08*640/26, 240-1.19*640/26,
                                                320+1.08*640/26, 240+1.19*640/26], rtol=1e-6)
    assert zone(result, 640, 480, (.25, .2, .75, .9), 'person')['alarm']
    assert not zone(result, 640, 480, (.0, .0, .2, 1.), 'person')['alarm']
    assert not zone(result, 640, 480, (.25, .2, .75, .9), 'bottle')['alarm']
    # Portrait and odd image dimensions preserve Darknet's integer letterbox correction.
    portrait = decode(synthetic_head(), 481, 641)[0]
    np.testing.assert_allclose(portrait['center'], [240.5, 320.5])
    empty = np.zeros((125, 13, 13), np.float32)
    assert decode(empty, 640, 480) == []
    assert np.all(np.isfinite(env['sigmoid'](np.array([-10000, 0, 10000]))))
    # A second same-class anchor predicting the same box is suppressed.
    head = synthetic_head().reshape(5, 25, 13, 13)
    head[1, 4, 6, 6] = 10
    head[1, 19, 6, 6] = 12
    head[1, 2:4, 6, 6] = np.log(env['ANCHORS'][0]/env['ANCHORS'][1])
    assert len(decode(head.reshape(125, 13, 13), 640, 480)) == 1
    # Two spatially distinct people must not merge or be counted over multiple frames.
    head = synthetic_head().reshape(5, 25, 13, 13)
    head[0, 4, 6, 10] = 12
    head[0, 19, 6, 10] = 12
    two = decode(head.reshape(125, 13, 13), 640, 480)
    decision = zone(two, 640, 480, (.25, .2, .75, .9), 'person')
    assert decision['counts'] == {'person': 2} and len(decision['inside']) == 1
    # Box overlap alone is insufficient: the predicted center is the rule.
    outside = decode(synthetic_head(col=10), 640, 480)
    assert not zone(outside, 640, 480, (.25, .2, .75, .9), 'person')['alarm']
    for bad in ((.8, .2, .1, .9), (-.1, .2, .5, .9), (.2, .2, .5, 2)):
        try: zone([], 640, 480, bad, 'person')
        except ValueError: pass
        else: raise AssertionError('Invalid ROI accepted')


def run():
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        params = work/'installed/python3.8/site-packages/qnn/params'
        params.mkdir(parents=True)
        pkg = params.parent
        (pkg/'__init__.py').touch()
        np.save(params/'tinier-yolo-conv0-W.npy', np.ones((3, 3, 3, 2), np.float32)*.01)
        np.save(params/'tinier-yolo-conv8-W.npy', np.ones((1, 1, 1, 125), np.float32))
        np.save(params/'tinier-yolo-conv0-bias.npy', np.zeros(2, np.float32))
        np.save(params/'tinier-yolo-conv8-bias.npy', np.zeros(125, np.float32))
        (params/'tinier-yolo-layers.json').write_text('{}')
        (params/'tinier-yolo-bwn-3bit-relu-nomaxpool.cfg').write_text(CFG.read_text())
        dark_dir = work/'darknet'
        for name in ('python/darknet.py', 'libdarknet.so', 'data/voc.names'):
            p = dark_dir/name; p.parent.mkdir(parents=True, exist_ok=True); p.touch()
        (dark_dir/'data/voc.names').write_text('\n'.join(VOC))
        (dark_dir/'data/labels').mkdir()
        for size in range(8):
            for char in range(32, 127): (dark_dir/f'data/labels/{char}_{size}.png').touch()
        notebook_dir = work/'notebooks'; notebook_dir.mkdir()
        (notebook_dir/'Tinier-YOLO-topology.svg').touch()
        qnn = types.ModuleType('qnn'); qnn.__file__ = str(pkg/'__init__.py')
        qnn.TinierYolo, qnn.utils = Accelerator, utils
        base = types.ModuleType('pynq.overlays.base'); base.BaseOverlay = BaseOverlay
        modules = {'qnn': qnn, 'cv2': CV2('cv2'), 'IPython': IP, 'IPython.display': DISPLAY,
                   'ipywidgets': WIDGETS, 'pynq': types.ModuleType('pynq'),
                   'pynq.overlays': types.ModuleType('pynq.overlays'), 'pynq.overlays.base': base}
        original_cwd = Path.cwd()
        os.chdir(notebook_dir)
        try:
            for name in ('07_tiny-yolo-usb-camera.ipynb', '08_tiny-yolo-counting-zone-led.ipynb'):
                nb = json.loads((NB_DIR/name).read_text())
                assert nb['nbformat'] == 4
                sources = []
                for cell in nb['cells']:
                    if cell['cell_type'] == 'code':
                        assert cell['execution_count'] is None and not cell['outputs']
                        ast.parse(cell['source'], feature_version=(3, 8))
                        assert 'clear_output' not in cell['source']
                        sources.append(cell['source'])
                sources[0] = sources[0].replace('Path("/opt/darknet")', f'Path({str(dark_dir)!r})')
                dn = Darknet(); modules['darknet'] = dn
                env = {}
                with patch.dict(sys.modules, modules), patch.dict(os.environ, {'BOARD': 'Pynq-Z2'}), contextlib.redirect_stdout(io.StringIO()):
                    # Execute definitions, UI and empty history; defer the final cleanup.
                    for i, source in enumerate(sources[:-1]): exec(compile(source, f'{name}:{i}', 'exec'), env)
                    assert env['classifier'].init
                    env['preview_button'].click()
                    env['detect_button'].click()
                    assert len(env['detection_history']) == 1
                    first = env['detection_history'][0]
                    assert Path(first['capture']).is_file() and Path(first['result']).is_file()
                    assert Path(first['result']).with_suffix('.json').is_file()
                    with Image.open(first['capture']) as im: assert im.getpixel((0, 0)) == (200, 80, 20)
                    assert all(cap.released for cap in Camera.instances) and not dn.images
                    if name.startswith('08'):
                        check_decoder(env)
                        assert first['counts'] == {} and not first['alarm'] and Hardware.leds[0] == 0
                        env['last_convolution'] = lambda values: synthetic_head()
                        env['detect_button'].click()
                        assert env['detection_history'][-1]['alarm'] and Hardware.leds[0] == 1
                        assert Hardware.overlay == 'base' and not env['classifier'].init
                        env['last_convolution'] = lambda values: synthetic_head(col=10)
                        env['detect_button'].click()
                        assert not env['detection_history'][-1]['alarm'] and Hardware.leds[0] == 0
                        env['PHYSICAL_LED'] = False
                        env['detect_button'].click()
                        assert Hardware.overlay == 'yolo' and env['classifier'].init
                        env['PHYSICAL_LED'] = True
                        Hardware.fail_base = True
                        env['base_overlay'] = None
                        env['detect_button'].click()
                        assert env['detection_history'][-1]['led_error'] is not None
                        Hardware.fail_base = False
                    # Images are immutable paths and previous outputs are never cleared.
                    assert Path(first['result']).is_file()
                    assert len({r['result'] for r in env['detection_history']}) == len(env['detection_history'])
                    before = len(env['detection_history'])
                    Camera.bad_frame = True
                    with contextlib.redirect_stderr(io.StringIO()): env['detect_button'].click()
                    Camera.bad_frame = False
                    assert len(env['detection_history']) == before
                    assert all(cap.released for cap in Camera.instances)
                    Accelerator.fail = True
                    with contextlib.redirect_stderr(io.StringIO()): env['detect_button'].click()
                    Accelerator.fail = False
                    assert not env['classifier'].init
                    env['detect_button'].click()  # recovery reinitializes YOLO
                    assert len(env['detection_history']) == before + 1
                    old_buttons = env['ui_buttons'][:]
                    exec(next(s for s in sources if s.startswith('# Close old controls')), env)
                    assert all(b.disabled for b in old_buttons)
                    env['finish_button'].click()
                    assert env['classifier'] is None and not dn.networks and not dn.images
                    assert all(button.disabled for button in env['ui_buttons'])
                    assert Hardware.leds[0] == 0
                    exec(sources[-1], env)  # idempotent final cleanup
                    # Reloading weights releases the previous instance/native network.
                    exec(sources[1], env); old = env['classifier']; exec(sources[1], env)
                    assert not old.init and len(dn.networks) == 1
                    env['widgets'] = None
                    exec(next(s for s in sources if s.startswith('# Close old controls')), env)
                    assert env['ui_panel'] is None
                    env['capture_and_detect']()  # manual mode without ipywidgets
                    env['finish_session']()
                    assert not dn.networks and not any(a.init for a in Accelerator.instances)
                print('PASS', name, ': all cells, actual NumPy stages, buttons, capture colors, history, failures, recovery, cleanup')
            print('PASS decoder: known boxes, portrait letterbox, stable scores, NMS, counts, center-in-zone and invalid ROI')
        finally:
            os.chdir(original_cwd)

if __name__ == '__main__': run()
