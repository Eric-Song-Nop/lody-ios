import android.accessibilityservice.AccessibilityServiceInfo;
import android.app.UiAutomation;
import android.graphics.Rect;
import android.os.HandlerThread;
import android.os.Looper;
import android.os.SystemClock;
import android.util.Xml;
import android.view.accessibility.AccessibilityNodeInfo;
import java.io.FileOutputStream;
import org.xmlpull.v1.XmlSerializer;

/** API 36 shell-only observer. Never suppress the screen reader being tested. */
public final class AccessibilityDump {
  private static int count;

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
      automation.setServiceInfo(info);
      AccessibilityNodeInfo root = null;
      long deadline = SystemClock.uptimeMillis() + 5000;
      while (root == null && SystemClock.uptimeMillis() < deadline) {
        root = automation.getRootInActiveWindow();
        if (root == null) SystemClock.sleep(100);
      }
      if (root == null) throw new IllegalStateException("No active accessibility root");
      try (FileOutputStream output = new FileOutputStream(args[0])) {
        XmlSerializer xml = Xml.newSerializer();
        xml.setOutput(output, "UTF-8");
        xml.startDocument("UTF-8", true);
        xml.startTag(null, "hierarchy");
        xml.attribute(null, "observer", "dont-suppress-accessibility-services");
        node(xml, root, 0);
        xml.endTag(null, "hierarchy");
        xml.endDocument();
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
