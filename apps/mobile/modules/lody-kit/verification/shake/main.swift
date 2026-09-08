import UIKit

var unlock = LodyShakeUnlock()
precondition(!unlock.record(0))
precondition(!unlock.record(0.3))
precondition(!unlock.record(0.6))
precondition(!unlock.record(0.9))
precondition(unlock.record(1.2))
precondition(!unlock.record(1.5))

unlock = LodyShakeUnlock()
precondition(!unlock.record(0))
precondition(!unlock.record(1))
precondition(!unlock.record(2))
precondition(!unlock.record(3))
precondition(unlock.record(4))

unlock = LodyShakeUnlock()
precondition(!unlock.record(0))
precondition(!unlock.record(1))
precondition(!unlock.record(2))
precondition(!unlock.record(3))
precondition(!unlock.record(4.01))
precondition(unlock.record(5))

unlock = LodyShakeUnlock()
for time in stride(from: 0 as TimeInterval, through: 20, by: 5) {
  precondition(!unlock.record(time))
}

print("PASS: five shakes inside 4s unlock, slower bursts reset")

// UIKit forwards motionEnded through the responder chain using the incoming selector.
final class MotionReceiver: UIResponder {
  var motions: [UIEvent.EventSubtype] = []
  override func motionEnded(_ motion: UIEvent.EventSubtype, with event: UIEvent?) {
    motions.append(motion)
  }
}

final class MotionWindow: UIWindow {
  let receiver = MotionReceiver()
  override var next: UIResponder? { receiver }
}

let window = MotionWindow(frame: .zero)
var unlocks = 0
LodyShakeMonitor.onUnlock = { unlocks += 1 }
LodyShakeMonitor.install()
LodyShakeMonitor.install()
window.motionEnded(.none, with: nil)
precondition(window.receiver.motions == [.none])
precondition(unlocks == 0)
for index in 1...10 {
  window.motionEnded(.motionShake, with: nil)
  precondition(window.receiver.motions.count == index + 1, "Each motion must reach the next responder once")
  precondition(window.receiver.motions.last == .motionShake)
  precondition(unlocks == index / 5, "Only every fifth shake may unlock, including after repeated install")
}
print("PASS: UIKit forwards original motion selector without crashing; two five-shake bursts unlock exactly twice")
