"""SDK gRPC hardware touch on the runner-owned emulator's main display."""
import hashlib
import importlib
from pathlib import Path
import subprocess
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

        def send(pressure):
            event = self.messages.TouchEvent(display=0, touches=[
                self.messages.Touch(x=x, y=y, identifier=1, pressure=pressure,
                                    touch_major=8, touch_minor=8)])
            rpc(event, timeout=5, metadata=(('authorization', 'Bearer ' + self.token),))
            events.append({'at': time.monotonic(), 'pressure': pressure})

        def tap(duration):
            try:
                send(1)
                time.sleep(duration)
            finally:
                send(0)

        try:
            if mode == 'explore':
                tap(0.15)
            else:
                tap(0.06)
                time.sleep(0.08)
                tap(0.8 if mode == 'hold' else 0.06)
        finally:
            channel.close()
        return {'transport': 'emulator-grpc-sendTouch', 'mode': mode,
                'protoSha256': self.proto_hash, 'display': 0, 'point': [x, y], 'events': events}
