import ast
import io
import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'raspberry_pi'))
from qnn_cpu import CPUBackend, DarknetCPU, snapshot, temporary_image

class Helpers(unittest.TestCase):
    def test_pack_independent_reference(self):
        for bits, channels in ((2,68),(2,256),(3,16),(3,512)):
            model = CPUBackend.__new__(CPUBackend)
            model.init = True
            model.network_json = {'parameters': {'ACTIVATION_BITS': bits}}
            values = (np.arange(channels*4) % (1<<bits)).astype(np.uint8).reshape(channels,2,2)
            packed = model.prepare_buffer(values)
            for y in range(2):
                for x in range(2):
                    number = sum(int(v) << (bits*i) for i,v in enumerate(values[:,y,x]))
                    self.assertEqual(packed[y,x].tobytes(),number.to_bytes((channels*bits+7)//8,'little'))
            buf=np.zeros((2,2,channels),dtype=np.uint8)
            buf[...,:packed.shape[-1]]=packed
            np.testing.assert_array_equal(model.postprocess_buffer(buf),np.moveaxis(values,0,-1).ravel())

    def test_snapshot_http(self):
        data=io.BytesIO()
        Image.new('RGB',(12,8),'red').save(data,format='JPEG')
        jpeg=data.getvalue()
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-Type','image/jpeg' if self.path=='/snapshot' else 'multipart/x-mixed-replace')
                self.end_headers()
                self.wfile.write(jpeg)
            def log_message(self,*args): pass
        server=HTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            url='http://127.0.0.1:'+str(server.server_port)
            self.assertEqual(snapshot(url+'/snapshot').size,(12,8))
            with self.assertRaises(ValueError): snapshot(url+'/stream')
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_ram_cleanup_on_error(self):
        with self.assertRaisesRegex(RuntimeError,'deliberate'):
            with temporary_image(Image.new('RGB',(2,2))) as path:
                self.assertEqual(path.parent.parent,Path('/dev/shm'))
                self.assertTrue(path.exists())
                raise RuntimeError('deliberate')
        self.assertFalse(path.exists())
        self.assertFalse(path.parent.exists())

    @unittest.skipUnless((ROOT/'raspberry_pi/.deps/darknet/libdarknet.so').exists(),'Build Darknet first')
    def test_darknet_native(self):
        model=DarknetCPU()
        before=set(Path('/dev/shm').glob('qnn-rpi-*'))
        try:
            image=ROOT/'notebooks/yoloimages/dog.jpg'
            pixels=model.load_image(image)
            self.assertEqual(pixels.shape,(1,416,416,3))
            self.assertTrue(np.all(np.isfinite(pixels)))
            preview, detections=model.draw(image,np.zeros((125,13,13),dtype=np.float32))
            self.assertGreater(preview.width,0)
            self.assertEqual(detections,[])
        finally:
            model.close(); model.close()
        self.assertEqual(before,set(Path('/dev/shm').glob('qnn-rpi-*')))

    def test_notebooks_clean_and_valid_python(self):
        for filename in ('02.1_dorefanet-imagenet-rpi.ipynb','05.1_tiny-yolo-image-rpi.ipynb'):
            notebook=json.loads((ROOT/'notebooks'/filename).read_text())
            for cell in notebook['cells']:
                if cell['cell_type']=='code':
                    self.assertEqual(cell['outputs'],[])
                    self.assertIsNone(cell['execution_count'])
                    tree=ast.parse(''.join(cell['source']))
                    for node in ast.walk(tree):
                        if isinstance(node,ast.Import):
                            self.assertFalse(any(a.name in ('qnn','pynq') for a in node.names))
                        elif isinstance(node,ast.ImportFrom):
                            self.assertNotIn(node.module,('qnn','pynq'))

if __name__=='__main__': unittest.main()
