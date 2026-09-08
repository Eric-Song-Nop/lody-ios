import UIKit

enum LodyShakeMonitor {
  static var onUnlock: (() -> Void)?
  private static var unlock = LodyShakeUnlock()
  private static var installed = false

  static func install() {
    guard !installed else { return }
    let selector = #selector(UIWindow.motionEnded(_:with:))
    guard let method = class_getInstanceMethod(UIWindow.self, selector) else { return }
    typealias MotionEnded = @convention(c) (UIWindow, Selector, UIEvent.EventSubtype, UIEvent?) -> Void
    let original = unsafeBitCast(method_getImplementation(method), to: MotionEnded.self)
    let replacement: @convention(block) (UIWindow, UIEvent.EventSubtype, UIEvent?) -> Void = { window, motion, event in
      // UIResponder forwards using _cmd; an alias selector crashes the next responder.
      original(window, selector, motion, event)
      if motion == .motionShake { note() }
    }
    // Replace only UIWindow's entry, even when its original method is inherited.
    class_replaceMethod(UIWindow.self, selector, imp_implementationWithBlock(replacement), method_getTypeEncoding(method))
    installed = true
  }

  static func note(_ now: TimeInterval = ProcessInfo.processInfo.systemUptime) {
    if unlock.record(now) { onUnlock?() }
  }
}
