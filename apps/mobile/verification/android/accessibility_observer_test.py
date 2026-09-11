"""Protocol/lifecycle checks; these do not replace TalkBack device evidence."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

from accessibility_observer import Observer


SERVER = '''
import base64, json, os, sys
print('observer-ready', flush=True)
for request in sys.stdin:
    request = request.strip()
    if request == 'stop':
        break
    if request == 'events':
        print(json.dumps({'dropped': 0, 'events': [{'type': 'focus'}]}), flush=True)
    elif request == 'snapshot':
        xml = '<hierarchy><node text="' + '中文' * 40000 + '"/></hierarchy>'
        reply = base64.b64encode(xml.encode()) + b'\\n'
        for start in range(0, len(reply), 1007):
            os.write(sys.stdout.fileno(), reply[start:start + 1007])
    else:
        sys.exit(7)
'''


class ObserverProtocolTests(unittest.TestCase):
    def test_fragmented_large_reply_and_clean_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            server = output / 'server.py'
            server.write_text(SERVER)
            observer = Observer([sys.executable, str(server)], 'owned', 'dex', output)
            try:
                for _ in range(2):
                    tree = observer.snapshot()
                    self.assertEqual(tree.find('node').get('text'), '中文' * 40000)
                observer.save_events()
                self.assertEqual(json.loads((output / 'accessibility-events.json').read_text())['dropped'], 0)
                self.assertEqual(observer.requests, 3)
            finally:
                observer.close()
            self.assertEqual(observer.process.returncode, 0)
            self.assertTrue(observer.process.stdin.closed)
            self.assertTrue(observer.process.stdout.closed)

    def test_unexpected_observer_exit_is_not_a_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            server = output / 'server.py'
            server.write_text(SERVER.replace("elif request == 'snapshot':", "elif request == 'unreachable':"))
            observer = Observer([sys.executable, str(server)], 'owned', 'dex', output)
            with self.assertRaisesRegex(RuntimeError, 'exited before response'):
                observer.snapshot()
            observer.process.wait(timeout=5)
            with self.assertRaisesRegex(RuntimeError, 'code 7'):
                observer.close()
            self.assertTrue(observer.process.stdin.closed)
            self.assertTrue(observer.process.stdout.closed)


if __name__ == '__main__':
    unittest.main()
