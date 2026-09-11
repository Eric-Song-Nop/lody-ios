"""Exercise fragmented PNG output and delayed process exit through real pipes."""
import base64
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib
from png_capture import capture


def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))


PNG = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0))
       + chunk(b'IDAT', zlib.compress(b'\0\x12\x34\x56\xff')) + chunk(b'IEND', b''))


class CaptureTest(unittest.TestCase):
    def run_capture(self, data, suffix=''):
        script = ("import base64,os,time; data=base64.b64decode('"
                  + base64.b64encode(data).decode() + "'); "
                  "[os.write(1,data[i:i+3]) for i in range(0,len(data),3)]; " + suffix)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'capture.png'
            result = capture([sys.executable, '-c', script], path, timeout=2)
            self.assertEqual(path.read_bytes(), data)
            return result

    def test_complete_pixels_precede_process_exit(self):
        result = self.run_capture(PNG, 'time.sleep(0.25)')
        self.assertGreater(result['processCompleteSeconds'] - result['pngCompleteSeconds'], 0.20)
        self.assertEqual(result['bytes'], len(PNG))

    def test_missing_end_and_bad_checksum_fail(self):
        for data in (PNG[:-12], PNG[:-1] + bytes([PNG[-1] ^ 1])):
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.run_capture(data)

    def test_complete_png_does_not_hide_process_failure(self):
        with self.assertRaises(RuntimeError):
            self.run_capture(PNG, 'raise SystemExit(7)')

    def test_stalled_output_times_out_without_publishing_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'capture.png'
            with self.assertRaises(TimeoutError):
                capture([sys.executable, '-c', 'import time; time.sleep(10)'],
                        path, timeout=0.1)
            self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()
