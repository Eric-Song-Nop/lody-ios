import Foundation

/// Presentation-only pacing. Small tails keep a short character reveal; long
/// replies and bursts are committed together and animated by the block view.
/// Network history remains authoritative, including corrections and completion.
struct ChatStream {
  static let blockAnimationLength = 1024
  static let blockAnimationBatch = 48
  private struct Reveal {
    var source = ""
    var shown = ""
    var pending: [Character] = []
    var offset = 0
    var batch = 1
    var hasPending: Bool { offset < pending.count }

    mutating func receive(_ text: String, animate: Bool) {
      guard text != source else {
        if !animate { finish() }
        return
      }
      guard animate, text.hasPrefix(source) else {
        source = text
        finish()
        return
      }
      pending = Array(pending.dropFirst(offset)) + Array(text.dropFirst(source.count))
      offset = 0
      source = text
      if text.utf16.count > ChatStream.blockAnimationLength || pending.count >= ChatStream.blockAnimationBatch {
        batch = pending.count
      } else {
        batch = max(1, Int(ceil(Double(pending.count) / 8)))
      }
    }
    mutating func advance() {
      guard hasPending else { return }
      let end = min(pending.count, offset + batch)
      shown += String(pending[offset..<end])
      offset = end
      if !hasPending { finish() }
    }
    mutating func finish() {
      shown = source
      pending.removeAll(keepingCapacity: false)
      offset = 0
    }
  }

  private struct ID: Hashable { let entry: String; let item: String }
  private var reveals: [ID: Reveal] = [:]
  private var targets: [ChatEntry] = []
  private var initialized = false
  var hasPending: Bool { reveals.values.contains { $0.hasPending } }

  static func commitInterval(tailLength: Int) -> Double {
    min(0.096, 0.048 * (1 + Double(tailLength) / 256))
  }

  mutating func receive(_ entries: [ChatEntry], animate: Bool) {
    let wasRunning = Set(targets.filter(\.isRunning).map(\.id))
    var retained: Set<ID> = []
    for entry in entries where entry.role != "user" {
      for item in entry.items where item.type == "text" || item.type == "thought" {
        let id = ID(entry: entry.id, item: item.itemId)
        retained.insert(id)
        var reveal = reveals[id] ?? Reveal()
        let shouldAnimate = initialized && animate && entry.role == "assistant" && (entry.isRunning || wasRunning.contains(entry.id) || reveal.hasPending)
        reveal.receive(item.text ?? "", animate: shouldAnimate)
        reveals[id] = reveal
      }
    }
    reveals = reveals.filter { retained.contains($0.key) }
    targets = entries
    initialized = true
  }

  mutating func advance() {
    for id in reveals.keys { reveals[id]?.advance() }
  }

  mutating func finish() {
    for id in reveals.keys { reveals[id]?.finish() }
  }

  var presentation: [ChatEntry] {
    targets.map { target in
      var entry = target
      for index in entry.items.indices {
        guard let reveal = reveals[ID(entry: entry.id, item: entry.items[index].itemId)] else { continue }
        entry.items[index].text = reveal.shown
        // Completion folding waits for the visible tail, never the network ACK.
        if reveal.hasPending { entry.finished = false }
      }
      return entry
    }
  }
}

enum ChatScroll {
  static let resumeDistance: Double = 80

  // Time-based convergence keeps a moving destination continuous across updates
  // and behaves the same at 60 and 120 Hz. Snap only a subpixel remainder.
  static func advance(_ current: Double, toward target: Double, elapsed: Double, response: Double, minimumStep: Double = 0) -> Double {
    let next = current + (target - current) * (1 - exp(-max(0, elapsed) / response))
    // UIScrollView rounds offsets to its pixel grid. A step smaller than one
    // pixel can otherwise round back forever while the display link keeps firing.
    if elapsed > 0 && abs(next - current) < minimumStep { return target }
    return abs(target - next) <= 0.5 ? target : next
  }

  static func bottom(contentHeight: Double, viewportHeight: Double, topInset: Double, bottomInset: Double) -> Double {
    max(-topInset, contentHeight - viewportHeight + bottomInset)
  }
}
