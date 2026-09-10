import android.accessibilityservice.AccessibilityServiceInfo;
import android.app.UiAutomation;
import android.graphics.Rect;
import android.os.HandlerThread;
import android.os.Looper;
import android.os.SystemClock;
import android.util.Xml;
import android.util.Base64;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.InputStreamReader;
import java.io.FileOutputStream;
import java.util.ArrayDeque;
import org.json.JSONArray;
import org.json.JSONObject;
import org.xmlpull.v1.XmlSerializer;

/** API 36 shell-only observer. Never suppress the screen reader being tested. */
public final class AccessibilityDump {
  private static int count;
  private static final ArrayDeque<JSONObject> events = new ArrayDeque<>();
  private static int droppedEvents;

  private static byte[] snapshot(UiAutomation automation) throws Exception {
    automation.clearCache();
    AccessibilityNodeInfo root = null;
    long deadline = SystemClock.uptimeMillis() + 5000;
    while (root == null && SystemClock.uptimeMillis() < deadline) {
      root = automation.getRootInActiveWindow();
      if (root == null) SystemClock.sleep(100);
    }
    if (root == null) throw new IllegalStateException("No active accessibility root");
    count = 0;
    ByteArrayOutputStream output = new ByteArrayOutputStream();
    XmlSerializer xml = Xml.newSerializer();
    xml.setOutput(output, "UTF-8");
    xml.startDocument("UTF-8", true);
    xml.startTag(null, "hierarchy");
    xml.attribute(null, "observer", "dont-suppress-accessibility-services");
    node(xml, root, 0);
    xml.endTag(null, "hierarchy");
    xml.endDocument();
    return output.toByteArray();
  }

  private static void recordEvent(AccessibilityEvent event) {
    int observedTypes = AccessibilityEvent.TYPE_VIEW_HOVER_ENTER
        | AccessibilityEvent.TYPE_VIEW_HOVER_EXIT
        | AccessibilityEvent.TYPE_VIEW_ACCESSIBILITY_FOCUSED
        | AccessibilityEvent.TYPE_VIEW_ACCESSIBILITY_FOCUS_CLEARED
        | AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED
        | AccessibilityEvent.TYPE_WINDOWS_CHANGED
        | AccessibilityEvent.TYPE_TOUCH_INTERACTION_START
        | AccessibilityEvent.TYPE_TOUCH_INTERACTION_END;
    if ((event.getEventType() & observedTypes) == 0) return;
    try {
      JSONObject item = new JSONObject();
      item.put("type", AccessibilityEvent.eventTypeToString(event.getEventType()));
      item.put("eventTimeMs", event.getEventTime());
      item.put("observedUptimeMs", SystemClock.uptimeMillis());
      item.put("package", text(event.getPackageName()));
      item.put("class", text(event.getClassName()));
      item.put("description", text(event.getContentDescription()));
      item.put("text", event.getText().toString());
      synchronized (events) {
        if (events.size() == 512) { events.removeFirst(); droppedEvents++; }
        events.addLast(item);
      }
    } catch (Exception error) { throw new IllegalStateException(error); }
  }

  private static String text(CharSequence value) {
    return value == null ? "" : value.toString();
  }

  private static void node(XmlSerializer xml, AccessibilityNodeInfo node, int depth)
      throws Exception {
    if (++count > 5000 || depth > 100) {
      throw new IllegalStateException("Accessibility tree exceeds verification bounds");
    }
    Rect bounds = new Rect();
    node.getBoundsInScreen(bounds);
    xml.startTag(null, "node");
    xml.attribute(null, "text", text(node.getText()));
    xml.attribute(null, "content-desc", text(node.getContentDescription()));
    xml.attribute(null, "resource-id", text(node.getViewIdResourceName()));
    xml.attribute(null, "class", text(node.getClassName()));
    xml.attribute(null, "package", text(node.getPackageName()));
    xml.attribute(null, "bounds", bounds.toShortString());
    xml.attribute(null, "enabled", String.valueOf(node.isEnabled()));
    xml.attribute(null, "clickable", String.valueOf(node.isClickable()));
    xml.attribute(null, "long-clickable", String.valueOf(node.isLongClickable()));
    xml.attribute(null, "focusable", String.valueOf(node.isFocusable()));
    xml.attribute(null, "focused", String.valueOf(node.isFocused()));
    xml.attribute(null, "accessibility-focused", String.valueOf(node.isAccessibilityFocused()));
    xml.attribute(null, "scrollable", String.valueOf(node.isScrollable()));
    xml.attribute(null, "checked", String.valueOf(node.isChecked()));
    xml.attribute(null, "checkable", String.valueOf(node.isCheckable()));
    for (int i = 0; i < node.getChildCount(); i++) {
      AccessibilityNodeInfo child = node.getChild(i);
      if (child != null && child.isVisibleToUser()) {
        node(xml, child, depth + 1);
      }
    }
    xml.endTag(null, "node");
  }

  public static void main(String[] args) {
    // AccessibilityInteractionClient creates a Handler on the main looper even
    // though UiAutomation callbacks run on the separate thread below.
    Looper.prepareMainLooper();
    HandlerThread thread = new HandlerThread("lody-a11y-observer");
    thread.start();
    UiAutomation automation = null;
    int status = 0;
    try {
      Class<?> connectionType = Class.forName("android.app.IUiAutomationConnection");
      Object connection = Class.forName("android.app.UiAutomationConnection")
          .getConstructor().newInstance();
      automation = (UiAutomation) UiAutomation.class
          .getConstructor(Looper.class, connectionType)
          .newInstance(thread.getLooper(), connection);
      UiAutomation.class.getMethod("connect", int.class)
          .invoke(automation, UiAutomation.FLAG_DONT_SUPPRESS_ACCESSIBILITY_SERVICES);
      AccessibilityServiceInfo info = automation.getServiceInfo();
      info.flags |= AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
          | AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS;
      // Keep normal content-change delivery for the accessibility client cache;
      // only the retained diagnostic log is filtered to focus/hover/window events.
      info.eventTypes = AccessibilityEvent.TYPES_ALL_MASK;
      automation.setServiceInfo(info);
      automation.setOnAccessibilityEventListener(AccessibilityDump::recordEvent);
      if (args.length == 1 && args[0].equals("--serve")) {
        System.out.println("observer-ready");
        System.out.flush();
        BufferedReader input = new BufferedReader(new InputStreamReader(System.in, "UTF-8"));
        String request;
        while ((request = input.readLine()) != null) {
          if (request.equals("stop")) break;
          if (request.equals("snapshot")) {
            System.out.println(Base64.encodeToString(snapshot(automation), Base64.NO_WRAP));
          } else if (request.equals("events")) {
            synchronized (events) {
              JSONObject log = new JSONObject();
              log.put("dropped", droppedEvents);
              log.put("events", new JSONArray(events));
              System.out.println(log.toString());
            }
          } else throw new IllegalArgumentException("Unknown observer request");
          System.out.flush();
        }
      } else {
        try (FileOutputStream output = new FileOutputStream(args[0])) {
          output.write(snapshot(automation));
        }
      }
    } catch (Throwable error) {
      error.printStackTrace();
      status = 1;
    } finally {
      if (automation != null) {
        try {
          UiAutomation.class.getMethod("disconnect").invoke(automation);
        } catch (Throwable error) {
          error.printStackTrace();
          status = 1;
        }
      }
      thread.quitSafely();
    }
    System.exit(status);
  }
}
