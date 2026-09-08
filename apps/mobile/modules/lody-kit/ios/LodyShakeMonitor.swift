import UIKit

enum LodyShakeMonitor {
  static var onUnlock: (() -> Void)?
  private static var unlock = LodyShakeUnlock()
  private static var installed = false

  static func install() {
    guard !installed else { return }
    installed = true
    let selector = #selector(UIWindow.motionEnded(_:with:))
    let swizzled = #selector(UIWindow.lody_motionEnded(_:with:))
    guard
      let original = class_getInstanceMethod(UIWindow.self, selector),
      let added = class_getInstanceMethod(UIWindow.self, swizzled)
    else { return }
    if class_addMethod(
      UIWindow.self,
      selector,
      method_getImplementation(added),
      method_getTypeEncoding(added)
    ) {
      class_replaceMethod(
        UIWindow.self,
        swizzled,
        method_getImplementation(original),
        method_getTypeEncoding(original)
      )
    } else {
      method_exchangeImplementations(original, added)
    }
  }

  static func note(_ now: TimeInterval = ProcessInfo.processInfo.systemUptime) {
    if unlock.record(now) { onUnlock?() }
  }
}

extension UIWindow {
  @objc fileprivate func lody_motionEnded(
    _ motion: UIEvent.EventSubtype,
    with event: UIEvent?
  ) {
    lody_motionEnded(motion, with: event)
    if motion == .motionShake { LodyShakeMonitor.note() }
  }
}
