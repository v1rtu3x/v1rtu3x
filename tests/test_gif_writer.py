import sys
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'source'))
from optimize_gif import save_delta_gif

class GifWriterTests(unittest.TestCase):
    def test_delta_encoding_is_lossless(self):
        palette=[10,20,30, 230,190,120]+[0,0,0]*254
        frames=[]
        for i in range(4):
            im=Image.new('P',(31,19),0)
            im.putpalette(palette)
            im.putpixel((2+i,7),1)
            frames.append(im)
        frames.append(frames[-1].copy())
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.gif'
            durations=[40,40,80,120,40]
            save_delta_gif(frames,path,durations)
            with Image.open(path) as gif:
                self.assertEqual(gif.n_frames,len(frames))
                self.assertEqual(gif.info['loop'],0)
                total=0
                for n,frame in enumerate(frames):
                    gif.seek(n)
                    total+=gif.info['duration']
                    self.assertTrue(np.array_equal(np.asarray(frame.convert('RGB')),
                                                   np.asarray(gif.convert('RGB'))))
                self.assertEqual(total,sum(durations))

    def test_empty_input_is_rejected(self):
        with self.assertRaises(ValueError):
            save_delta_gif([],Path('unused.gif'))

if __name__=='__main__':
    unittest.main()
