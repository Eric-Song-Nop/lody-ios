"""One non-suppressing UiAutomation connection for a complete TalkBack case."""
import base64
import json
import os
import selectors
import subprocess
import time
import xml.etree.ElementTree as ET


class Observer:
    def __init__(self, adb, serial, remote, output):
        self.output = output
        self.stderr = (output / 'accessibility-observer.log').open('wb')
        self.process = subprocess.Popen(
            [*adb, '-s', serial, 'shell', '-T', f'CLASSPATH={remote}',
             'app_process', '/', 'AccessibilityDump', '--serve'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.buffer = b''
        self.requests = 0
        try:
            if self._line() != b'observer-ready':
                raise RuntimeError('Unexpected accessibility observer readiness response')
        except BaseException:
            self.close()
            raise

    def _line(self):
        deadline = time.monotonic() + 15
        while b'\n' not in self.buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.selector.select(remaining):
                raise TimeoutError('Accessibility observer response exceeded 15 seconds')
            chunk = os.read(self.process.stdout.fileno(), 65536)
            if not chunk:
                raise RuntimeError('Accessibility observer exited before response; inspect its log')
            self.buffer += chunk
            if len(self.buffer) > 8 * 1024 * 1024:
                raise RuntimeError('Accessibility observer response exceeds 8 MiB')
        line, self.buffer = self.buffer.split(b'\n', 1)
        return line.rstrip(b'\r')

    def _request(self, name):
        if self.process.poll() is not None:
            raise RuntimeError('Accessibility observer is no longer running')
        self.process.stdin.write(name.encode('ascii') + b'\n')
        self.process.stdin.flush()
        self.requests += 1
        return self._line()

    def snapshot(self):
        return ET.fromstring(base64.b64decode(self._request('snapshot'), validate=True))

    def save_events(self):
        events = json.loads(self._request('events'))
        (self.output / 'accessibility-events.json').write_text(json.dumps(events, indent=2) + '\n')

    def close(self):
        try:
            if self.process.poll() is None:
                self.process.stdin.write(b'stop\n')
                self.process.stdin.flush()
                self.process.stdin.close()
                try:
                    code = self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.terminate()
                    self.process.wait(timeout=5)
                    raise RuntimeError('Accessibility observer did not stop cleanly')
            else:
                code = self.process.returncode
            if code != 0:
                raise RuntimeError(f'Accessibility observer exited with code {code}')
        finally:
            if self.process.poll() is None:
                self.process.kill()
                self.process.wait(timeout=5)
            self.selector.close()
            if not self.process.stdin.closed:
                self.process.stdin.close()
            self.process.stdout.close()
            self.stderr.close()
