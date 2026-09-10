"""Build and drive one continuous shell gesture on the API 36 test device."""
import os
from pathlib import Path
import subprocess
import time


def build(sdk, output):
    directory = output / 'gesture-driver'
    directory.mkdir()
    source = Path(__file__).with_name('GestureInput.java')
    android_jar = sdk / 'platforms/android-36/android.jar'
    java_home = os.environ.get('JAVA_HOME')
    javac = str(Path(java_home) / 'bin/javac') if java_home else 'javac'
    subprocess.run([javac, '-source', '8', '-target', '8', '-classpath', str(android_jar), '-d', str(directory), str(source)], check=True, timeout=60)
    subprocess.run([str(sdk / 'build-tools/36.0.0/d8'), '--lib', str(android_jar), '--output', str(directory), str(directory / 'GestureInput.class')], check=True, timeout=60)
    return directory / 'classes.dex'


def cancel(adb, serial, dex, output, width, height, screenshot):
    remote = '/data/local/tmp/lody-verify-gesture.dex'
    device = [*adb, '-s', serial]
    subprocess.run([*device, 'push', str(dex), remote], check=True, capture_output=True, timeout=30)
    log_path = output / 'gesture-input.log'
    try:
        with log_path.open('w') as log:
            process = subprocess.Popen([*device, 'shell', f'CLASSPATH={remote}', 'app_process', '/', 'GestureInput', str(width // 4), str(height // 2)], stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 15
                while 'gesture-preview-ready' not in log_path.read_text():
                    if process.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError(f'Gesture preview did not start: {log_path.read_text()}')
                    time.sleep(0.05)
                screenshot('back-gesture-preview')
                if 'gesture-cancel-released' in log_path.read_text():
                    raise RuntimeError('Preview capture finished after the gesture was released')
                if process.wait(timeout=15) != 0 or 'gesture-cancel-released' not in log_path.read_text():
                    raise RuntimeError(f'Gesture failed: {log_path.read_text()}')
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
    finally:
        subprocess.run([*device, 'shell', 'rm', '-f', remote], check=True, timeout=15)
