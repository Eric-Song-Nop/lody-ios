"""Measure complete PNG receipt separately from screencap process shutdown."""
import os
import selectors
import struct
import subprocess
import time
import zlib


def capture(command, destination, timeout=15):
    started = time.monotonic()
    received = bytearray()
    offset = 8
    complete = None
    first_byte = None
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    selector.register(process.stderr, selectors.EVENT_READ)
    errors = bytearray()
    try:
        while selector.get_map():
            remaining = timeout - (time.monotonic() - started)
            if remaining <= 0:
                raise TimeoutError('Screenshot output did not finish')
            for key, _ in selector.select(remaining):
                data = os.read(key.fileobj.fileno(), 65536)
                if not data:
                    selector.unregister(key.fileobj)
                    continue
                if key.fileobj is process.stderr:
                    errors.extend(data)
                    if len(errors) > 65536:
                        raise ValueError('Screenshot stderr exceeds limit')
                    continue
                if first_byte is None:
                    first_byte = time.monotonic() - started
                received.extend(data)
                if len(received) > 64 * 1024 * 1024:
                    raise ValueError('Screenshot PNG exceeds limit')
                if len(received) < 8:
                    continue
                if received[:8] != b'\x89PNG\r\n\x1a\n':
                    raise ValueError('Screenshot is not PNG')
                while complete is None and len(received) >= offset + 12:
                    size = struct.unpack_from('>I', received, offset)[0]
                    end = offset + size + 12
                    if end > 64 * 1024 * 1024:
                        raise ValueError('Screenshot chunk exceeds limit')
                    if len(received) < end:
                        break
                    kind = received[offset + 4:offset + 8]
                    checksum = struct.unpack_from('>I', received, end - 4)[0]
                    if zlib.crc32(received[offset + 4:end - 4]) != checksum:
                        raise ValueError('Screenshot PNG checksum mismatch')
                    offset = end
                    if kind == b'IEND':
                        if size != 0:
                            raise ValueError('Invalid PNG end chunk')
                        complete = time.monotonic() - started
        code = process.wait(timeout=max(0.01, timeout - (time.monotonic() - started)))
        if code:
            raise RuntimeError(f'Screenshot exited {code}: {errors.decode(errors="replace")}')
        if complete is None or offset != len(received):
            raise ValueError('Screenshot PNG is incomplete or contains trailing data')
        destination.write_bytes(received)
        return {'firstByteSeconds': first_byte, 'pngCompleteSeconds': complete,
                'processCompleteSeconds': time.monotonic() - started,
                'bytes': len(received)}
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        selector.close()
        process.stdout.close()
        process.stderr.close()
