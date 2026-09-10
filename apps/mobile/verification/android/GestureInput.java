import android.os.SystemClock;
import android.view.InputDevice;
import android.view.InputEvent;
import android.view.MotionEvent;
import java.lang.reflect.Method;

/** Shell-only test driver, never packaged in LodyKit or the application. */
public final class GestureInput {
  private final Object manager;
  private final Method inject;
  private final long downTime = SystemClock.uptimeMillis();
  private final float y;

  private GestureInput(float y) throws Exception {
    // The API 36 verification baseline uses the same service entry as `input`.
    Class<?> type = Class.forName("android.hardware.input.InputManagerGlobal");
    manager = type.getMethod("getInstance").invoke(null);
    inject = type.getMethod("injectInputEvent", InputEvent.class, int.class);
    this.y = y;
  }

  private void event(int action, float x) throws Exception {
    MotionEvent event = MotionEvent.obtain(downTime, SystemClock.uptimeMillis(), action, x, y, 0);
    event.setSource(InputDevice.SOURCE_TOUCHSCREEN);
    try {
      if (!Boolean.TRUE.equals(inject.invoke(manager, event, 2))) {
        throw new IllegalStateException("System rejected gesture input");
      }
    } finally {
      event.recycle();
    }
  }

  private void move(float from, float to) throws Exception {
    for (int step = 1; step <= 24; step++) {
      SystemClock.sleep(16);
      event(MotionEvent.ACTION_MOVE, from + (to - from) * step / 24);
    }
  }

  public static void main(String[] args) {
    GestureInput input = null;
    try {
      float distance = Float.parseFloat(args[0]);
      input = new GestureInput(Float.parseFloat(args[1]));
      input.event(MotionEvent.ACTION_DOWN, 1);
      input.move(1, distance);
      System.out.println("gesture-preview-ready");
      System.out.flush();
      // Give the host time to capture the actual system preview before release.
      SystemClock.sleep(6000);
      input.move(distance, 1);
      input.event(MotionEvent.ACTION_UP, 1);
      System.out.println("gesture-cancel-released");
      System.exit(0);
    } catch (Throwable error) {
      if (input != null) {
        try {
          input.event(MotionEvent.ACTION_CANCEL, 1);
        } catch (Throwable releaseError) {
          error.addSuppressed(releaseError);
        }
      }
      error.printStackTrace();
      System.exit(1);
    }
  }
}
