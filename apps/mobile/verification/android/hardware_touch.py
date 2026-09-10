"""SDK gRPC hardware touch on the runner-owned emulator's main display."""
import hashlib
import importlib
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import time


def prepare(sdk, output):
    import grpc
    import grpc_tools
    directory = output / 'emulator-proto'
    directory.mkdir()
    proto = sdk / 'emulator/lib/emulator_controller.proto'
    subprocess.run([sys.executable, '-m', 'grpc_tools.protoc',
                    '-I' + str(proto.parent),
                    '-I' + str(Path(grpc_tools.__file__).parent / '_proto'),
                    '--python_out=' + str(directory), str(proto)], check=True, timeout=30)
    sys.path.insert(0, str(directory.resolve()))
    messages = importlib.import_module('emulator_controller_pb2')
    return grpc, messages, hashlib.sha256(proto.read_bytes()).hexdigest()


def connect(prepared, pid, port):
    grpc, messages, proto_hash = prepared
    roots = [Path(tempfile.gettempdir()) / 'avd/running',
             Path.home() / 'Library/Caches/TemporaryItems/avd/running']
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        for path in [root / name for root in roots
                     for name in (f'pid_{pid}.ini', f'pid_{pid}_info.ini')]:
            if not path.is_file():
                continue
            config = dict(line.split('=', 1) for line in path.read_text().splitlines() if '=' in line)
            if config.get('grpc.port') != str(port) or not config.get('grpc.token'):
                continue
            # Token is used only as RPC metadata, never stored in artifacts.
            return Driver(grpc, port, messages, config['grpc.token'], proto_hash)
        time.sleep(0.1)
    raise RuntimeError('Owned emulator authenticated gRPC discovery unavailable')


class Driver:
    def __init__(self, grpc, port, messages, token, proto_hash):
        self.grpc, self.port, self.messages = grpc, port, messages
        self.token, self.proto_hash = token, proto_hash

    def close(self):
        self.token = None

    def screenshot(self, destination):
        started = time.monotonic()
        channel = self.grpc.insecure_channel(
            f'127.0.0.1:{self.port}',
            options=[('grpc.max_receive_message_length', 64 * 1024 * 1024)])
        try:
            rpc = channel.unary_unary(
                '/android.emulation.control.EmulatorController/getScreenshot',
                request_serializer=self.messages.ImageFormat.SerializeToString,
                response_deserializer=self.messages.Image.FromString)
            reply = rpc(self.messages.ImageFormat(format=self.messages.ImageFormat.PNG, display=0),
                        timeout=15, metadata=(('authorization', 'Bearer ' + self.token),))
        finally:
            channel.close()
        received = time.monotonic() - started
        data = reply.image
        width, height = reply.format.width, reply.format.height
        if width <= 0 or height <= 0 or reply.format.format != self.messages.ImageFormat.PNG:
            raise ValueError('Emulator returned an inactive display or wrong screenshot format')
        if (len(data) < 45 or data[:16] != b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
                or data[-12:] != b'\x00\x00\x00\x00IEND\xaeB`\x82'
                or struct.unpack('>II', data[16:24]) != (width, height)):
            raise ValueError('Emulator returned an invalid or mismatched PNG')
        destination.write_bytes(data)
        return {'transport': 'emulator-grpc-getScreenshot', 'display': 0,
                'protoSha256': self.proto_hash, 'width': width, 'height': height,
                'frameTimestampUs': reply.timestampUs, 'receiptSeconds': received,
                'completeSeconds': time.monotonic() - started, 'bytes': len(data)}

    def run(self, x, y, mode):
        if mode not in ('explore', 'activate', 'hold'):
            raise ValueError(mode)
        x, y = int(x), int(y)
        events = []
        # Keep one connection across a double tap, but close before the runner
        # forks adb/observer processes; gRPC poll threads must not cross forks.
        channel = self.grpc.insecure_channel(f'127.0.0.1:{self.port}')
        rpc = channel.unary_unary('/android.emulation.control.EmulatorController/sendTouch',
                                 request_serializer=self.messages.TouchEvent.SerializeToString)

        def send(pressure, touch_x=None):
            current_x = x if touch_x is None else touch_x
            event = self.messages.TouchEvent(display=0, touches=[
                self.messages.Touch(x=current_x, y=y, identifier=1, pressure=pressure,
                                    touch_major=8, touch_minor=8)])
            rpc(event, timeout=5, metadata=(('authorization', 'Bearer ' + self.token),))
            events.append({'at': time.monotonic(), 'pressure': pressure, 'point': [current_x, y]})

        def tap(duration):
            try:
                send(1)
                time.sleep(duration)
            finally:
                send(0)

        try:
            if mode == 'explore':
                # Explore by touch is sustained contact with slow movement,
                # not a short tap that can remain in gesture recognition.
                # Stay within eight pixels of the already measured target center.
                try:
                    send(1, x - 8)
                    time.sleep(0.45)
                    for offset in (-6, -4, -2, 0):
                        send(1, x + offset)
                        time.sleep(0.04)
                finally:
                    send(0)
            else:
                tap(0.06)
                time.sleep(0.08)
                tap(0.8 if mode == 'hold' else 0.06)
        finally:
            channel.close()
        return {'transport': 'emulator-grpc-sendTouch', 'mode': mode,
                'protoSha256': self.proto_hash, 'display': 0, 'point': [x, y], 'events': events}
