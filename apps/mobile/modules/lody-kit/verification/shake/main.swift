import Foundation

var unlock = LodyShakeUnlock()
assert(!unlock.record(0))
assert(!unlock.record(0.3))
assert(!unlock.record(0.6))
assert(!unlock.record(0.9))
assert(unlock.record(1.2))
assert(!unlock.record(1.5))

unlock = LodyShakeUnlock()
assert(!unlock.record(0))
assert(!unlock.record(1))
assert(!unlock.record(2))
assert(!unlock.record(3))
assert(unlock.record(4))

unlock = LodyShakeUnlock()
assert(!unlock.record(0))
assert(!unlock.record(1))
assert(!unlock.record(2))
assert(!unlock.record(3))
assert(!unlock.record(4.01))
assert(unlock.record(5))

unlock = LodyShakeUnlock()
for time in stride(from: 0 as TimeInterval, through: 20, by: 5) {
  assert(!unlock.record(time))
}

print("PASS: five shakes inside 4s unlock, slower bursts reset")
