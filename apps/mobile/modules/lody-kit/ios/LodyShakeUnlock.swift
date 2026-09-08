import Foundation

struct LodyShakeUnlock {
  var stamps: [TimeInterval] = []

  mutating func record(
    _ now: TimeInterval,
    window: TimeInterval = 4,
    needed: Int = 5
  ) -> Bool {
    stamps.append(now)
    stamps.removeAll { now - $0 > window }
    guard stamps.count >= needed else { return false }
    stamps.removeAll()
    return true
  }
}
