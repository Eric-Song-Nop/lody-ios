import android.os.SystemClock;
import android.view.InputDevice;
import android.view.InputEvent;
import android.view.MotionEvent;
import java.lang.reflect.Method;

/** Shell-only touchscreen input: keep double-tap timing inside one process. */
public final class TalkBackInput {
  private final Object manager;
  private final Method inject;

  private TalkBackInput() throws Exception {
    Class<?> type = Class.forName("android.hardware.input.InputManagerGlobal");
    manager = type.getMethod("getInstance").invoke(null);
    inject = type.getMethod("injectInputEvent", InputEvent.class, int.class);
  }

  private void event(long down, int action, float x, float y) throws Exception {
    MotionEvent event = MotionEvent.obtain(down, SystemClock.uptimeMillis(), action, x, y, 0);
    event.setSource(InputDevice.SOURCE_TOUCHSCREEN);
    try {
      if (!Boolean.TRUE.equals(inject.invoke(manager, event, 2))) {
        throw new IllegalStateException("System rejected TalkBack gesture input");
      }
      System.out.println(action + ":" + event.getEventTime());
    } finally {
      event.recycle();
    }
  }

  private void tap(float x, float y, long duration) throws Exception {
    long down = SystemClock.uptimeMillis();
    try {
      event(down, MotionEvent.ACTION_DOWN, x, y);
      SystemClock.sleep(duration);
      event(down, MotionEvent.ACTION_UP, x, y);
    } catch (Exception error) {
      event(down, MotionEvent.ACTION_CANCEL, x, y);
      throw error;
    }
  }

  public static void main(String[] args) throws Exception {
    TalkBackInput input = new TalkBackInput();
    float x = Float.parseFloat(args[0]);
    float y = Float.parseFloat(args[1]);
    input.tap(x, y, 100);
    SystemClock.sleep(600);
    input.tap(x, y, 60);
    SystemClock.sleep(80);
    input.tap(x, y, Boolean.parseBoolean(args[2]) ? 800 : 60);
    System.out.println("talkback-gesture-released");
    System.exit(0);
  }
}
