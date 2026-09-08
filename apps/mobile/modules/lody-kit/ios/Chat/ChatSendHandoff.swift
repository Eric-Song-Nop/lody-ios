import UIKit

/// The flying copy and collection content keep independent layer lifecycles.
final class ChatMessageContent: UIView {
  let label = ChatTextView()
  let bubble = UIView()
  override init(frame: CGRect) {
    super.init(frame: frame)
    clipsToBounds = true
    bubble.backgroundColor = .lodyUserBubble
    bubble.layer.cornerRadius = 19
    bubble.layer.cornerCurve = .continuous
    addSubview(bubble)
    addSubview(label)
  }
  required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
  override func layoutSubviews() {
    super.layoutSubviews()
    bubble.frame = bounds
    bubble.backgroundColor = .lodyUserBubble
    // Process rows own the label frame so the chevron keeps its 8pt gap.
    // Bubble insets are only for the user send handoff.
    guard !bubble.isHidden else { return }
    UIView.performWithoutAnimation {
      label.frame = bounds.insetBy(dx: 13, dy: 10)
      label.layer.displayIfNeeded()
    }
  }
}

final class ChatSendHandoff {
  private static var active: [String: ChatSendHandoff] = [:]
  let content = ChatMessageContent(frame: .zero)
  private var expiry: DispatchWorkItem?
  private var photo: UIImageView?
  private var sourceSnapshot: UIView?
  private var sourceBackground = UIColor.secondarySystemBackground
  #if DEBUG
  private var probe: ChatThrowProbe?
  #endif
  private var delivering = false
  private var straight = false
  private weak var target: UIView?

  static func isWaiting(id: String) -> Bool {
    guard let handoff = active[id] else { return false }
    return !handoff.delivering
  }

  static func hold(id: String, target: UIView) {
    guard let handoff = active[id] else { target.isHidden = false; return }
    handoff.target = target
    target.isHidden = true
  }

  static func begin(id: String, text: String, source: UIView, background: UIView? = nil, straight: Bool = false) {
    guard let window = source.window, active[id] == nil else { return }
    let handoff = ChatSendHandoff()
    handoff.straight = straight
    handoff.sourceBackground = sampledBackground(background ?? source, in: window)
    handoff.content.backgroundColor = handoff.sourceBackground
    handoff.content.layer.cornerRadius = 19
    let paragraph = NSMutableParagraphStyle()
    paragraph.minimumLineHeight = 25 * UIFont.dynamicScale(compatibleWith: source.traitCollection)
    paragraph.maximumLineHeight = paragraph.minimumLineHeight
    let font = UIFont.dynamic(of: 17, compatibleWith: source.traitCollection)
    handoff.content.label.setText(NSAttributedString(string: text, attributes: [
      .paragraphStyle: paragraph,
      .font: font,
      .foregroundColor: UIColor.label,
      .baselineOffset: (paragraph.minimumLineHeight - font.lineHeight) / 2,
    ]))
    handoff.content.frame = source.convert(source.bounds, to: window)
    handoff.content.isUserInteractionEnabled = false
    handoff.content.accessibilityElementsHidden = true
    handoff.content.layoutIfNeeded()
    handoff.content.bubble.isHidden = true
    if let snapshot = source.snapshotView(afterScreenUpdates: false) {
      snapshot.frame = handoff.content.frame
      snapshot.isUserInteractionEnabled = false
      snapshot.accessibilityElementsHidden = true
      handoff.sourceSnapshot = snapshot
      handoff.content.isHidden = true
      window.addSubview(snapshot)
    }
    window.addSubview(handoff.content)
    active[id] = handoff
    let expiry = DispatchWorkItem { cancel(id: id) }
    handoff.expiry = expiry
    DispatchQueue.main.asyncAfter(deadline: .now() + 5, execute: expiry)
  }

  private static func sampledBackground(_ surface: UIView, in window: UIWindow) -> UIColor {
    let point = surface.convert(CGPoint(x: 8, y: surface.bounds.midY), to: window)
    let format = UIGraphicsImageRendererFormat()
    format.scale = 1
    format.opaque = true
    format.preferredRange = .standard
    let image = UIGraphicsImageRenderer(bounds: CGRect(origin: point, size: CGSize(width: 1, height: 1)), format: format).image { _ in
      window.drawHierarchy(in: window.bounds, afterScreenUpdates: false)
    }
    guard let cgImage = image.cgImage else { return .secondarySystemBackground }
    var pixel = [UInt8](repeating: 0, count: 4)
    return pixel.withUnsafeMutableBytes { bytes in
      guard let context = CGContext(data: bytes.baseAddress, width: 1, height: 1,
        bitsPerComponent: 8, bytesPerRow: 4, space: CGColorSpaceCreateDeviceRGB(),
        bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else {
        return .secondarySystemBackground
      }
      context.draw(cgImage, in: CGRect(x: 0, y: 0, width: 1, height: 1))
      return UIColor(red: CGFloat(bytes[0]) / 255, green: CGFloat(bytes[1]) / 255,
        blue: CGFloat(bytes[2]) / 255, alpha: 1)
    }
  }

  static func beginImages(id: String, attachments: [ChatAttachment], source: ChatAttachmentBar) {
    guard let window = source.window else { return }
    for attachment in attachments where attachment.isImage {
      guard let image = ChatAttachment.thumbnail(attachment.url) else { continue }
      let handoff = ChatSendHandoff()
      let photo = UIImageView(image: image)
      photo.contentMode = .scaleAspectFit
      photo.clipsToBounds = true
      photo.layer.cornerRadius = 16
      let sourceFrame = source.convert(source.attachmentFrame(id: attachment.id) ?? source.bounds, to: window)
      let side = min(42, sourceFrame.height)
      photo.frame = CGRect(x: sourceFrame.minX + 11, y: sourceFrame.minY, width: side, height: side)
      photo.isUserInteractionEnabled = false
      photo.accessibilityElementsHidden = true
      handoff.photo = photo
      window.addSubview(photo)
      let key = id + ":image:" + attachment.id
      active[key] = handoff
      let expiry = DispatchWorkItem { cancel(id: key) }
      handoff.expiry = expiry
      DispatchQueue.main.asyncAfter(deadline: .now() + 5, execute: expiry)
    }
  }

  static func deliverImage(id: String, attachmentID: String, to target: UIImageView, adopt: @escaping (UIImageView) -> Void) {
    let key = id + ":image:" + attachmentID
    guard let window = target.window, let handoff = active[key], !handoff.delivering, let photo = handoff.photo else { return }
    handoff.delivering = true
    handoff.target = target
    handoff.expiry?.cancel()
    let destination = target.convert(target.bounds, to: window)
    target.isHidden = true
    let finish = {
      target.isHidden = false
      guard active[key] === handoff else { photo.removeFromSuperview(); return }
      active.removeValue(forKey: key)
      adopt(photo)
    }
    if UIAccessibility.isReduceMotionEnabled { finish(); return }
    UIView.animate(withDuration: 0.35, delay: 0, options: [.curveEaseInOut, .beginFromCurrentState]) {
      photo.frame = destination
    } completion: { _ in finish() }
  }

  static func cancel(id: String) {
    for key in active.keys.filter({ $0.hasPrefix(id + ":image:") }) { cancel(id: key) }
    guard let handoff = active.removeValue(forKey: id) else { return }
    handoff.expiry?.cancel()
    #if DEBUG
    handoff.probe?.stop(cancelled: true)
    #endif
    handoff.target?.isHidden = false
    handoff.photo?.layer.removeAllAnimations()
    handoff.content.layer.removeAllAnimations()
    handoff.content.removeFromSuperview()
    handoff.sourceSnapshot?.removeFromSuperview()
    handoff.photo?.removeFromSuperview()
  }

  static func deliver(id: String, to target: ChatMessageContent, scrollDistance: CGFloat = 0) {
    guard let window = target.window, let handoff = active[id], !handoff.delivering else { return }
    handoff.delivering = true
    handoff.target = target
    handoff.expiry?.cancel()
    let destination = target.convert(target.bounds, to: window).offsetBy(dx: 0, dy: -scrollDistance)
    let sourceFrame = handoff.content.frame
    let destinationBackground = UIColor.lodyUserBubble.resolvedColor(with: target.traitCollection)
    handoff.content.label.setText(target.label.attributedTextValue)
    target.isHidden = true
    let finish = {
      handoff.sourceSnapshot?.removeFromSuperview()
      guard active[id] === handoff else { handoff.content.removeFromSuperview(); return }
      active.removeValue(forKey: id)
      // Match the demo: reveal the cell's existing content. Reparenting a layer
      // from UIWindow to a cell leaves one presentation frame in window coordinates.
      UIView.performWithoutAnimation {
        handoff.target?.isHidden = false
        handoff.content.removeFromSuperview()
      }
      #if DEBUG
      handoff.probe?.didLand(on: handoff.target ?? target)
      #endif
    }
    if UIAccessibility.isReduceMotionEnabled { finish(); return }
    // Independent position, compression, bounds and text tracks.
    let duration = ChatThrowCurve.duration
    let start = CGPoint(x: sourceFrame.midX, y: sourceFrame.midY)
    let end = CGPoint(x: destination.midX, y: destination.midY)
    let track = handoff.straight
      ? ChatThrowCurve.straightTrack(from: start, to: end)
      : ChatThrowCurve.positionTrack(from: start, to: end)
    let content = handoff.content
    // Sheet dismissal can carry an enclosing UIView animation into this callback.
    // Only the explicit throw tracks may animate the window-space content.
    UIView.performWithoutAnimation {
      content.isHidden = false
      content.frame = destination
      // The flying view hides its bubble layer, but still needs user-text insets.
      content.bubble.isHidden = false
      content.setNeedsLayout()
      content.layoutIfNeeded()
      content.backgroundColor = destinationBackground
      content.layer.cornerRadius = 19
      content.layer.cornerCurve = .continuous
      content.bubble.isHidden = true
    }
    if let snapshot = handoff.sourceSnapshot { window.bringSubviewToFront(snapshot) }

    CATransaction.begin()
    CATransaction.setDisableActions(true)
    CATransaction.setCompletionBlock(finish)
    let background = CABasicAnimation(keyPath: "backgroundColor")
    background.fromValue = handoff.sourceBackground.cgColor
    background.toValue = destinationBackground.cgColor
    background.duration = duration
    background.timingFunction = ChatThrowCurve.timingFunction
    content.layer.add(background, forKey: "throw.background")
    for view in [content, handoff.sourceSnapshot].compactMap({ $0 }) {
      view.layer.position = CGPoint(x: destination.midX, y: destination.midY)
      view.layer.add(ChatThrowCurve.positionAnimation(track), forKey: "throw.position")
      if !handoff.straight { view.layer.add(ChatThrowCurve.scaleAnimation(), forKey: "throw.scale") }
    }
    let size = CABasicAnimation(keyPath: "bounds.size")
    size.fromValue = NSValue(cgSize: sourceFrame.size)
    size.toValue = NSValue(cgSize: destination.size)
    size.duration = duration
    size.speed = ChatThrowCurve.boundsSpeed
    size.timingFunction = CAMediaTimingFunction(controlPoints: 0.54195118, 0, 0.58, 1)
    content.layer.add(size, forKey: "throw.bounds")
    if let snapshot = handoff.sourceSnapshot {
      for (layer, from, to) in [(snapshot.layer, Float(1), Float(0)), (content.label.layer, Float(0), Float(1))] {
        layer.opacity = to
        let fade = CABasicAnimation(keyPath: "opacity")
        fade.fromValue = from
        fade.toValue = to
        fade.duration = duration * 0.3
        fade.timingFunction = CAMediaTimingFunction(controlPoints: 0.5, 0, 0.5, 1)
        layer.add(fade, forKey: "throw.opacity")
      }
    }
    CATransaction.commit()
    #if DEBUG
    if ProcessInfo.processInfo.arguments.contains("--ui-verify-throw"),
       ProcessInfo.processInfo.arguments.contains("--ui-verify") {
      handoff.probe = ChatThrowProbe(content: content, target: target, source: sourceFrame, destination: destination, track: track, sourceBackground: handoff.sourceBackground, destinationBackground: destinationBackground)
    }
    #endif
  }
}

#if DEBUG
// Offline-only presentation-layer samples. Records geometry, never message text.
private final class ChatThrowProbe: NSObject {
  private weak var content: UIView?
  private weak var target: UIView?
  private weak var window: UIWindow?
  private var link: CADisplayLink?
  private let started = CACurrentMediaTime()
  private let duration: Double
  private let track: ChatThrowCurve.PositionTrack
  private let source: CGRect
  private let destination: CGRect
  private let sourceBackground: UIColor
  private let destinationBackground: UIColor
  private var adoptedAt: Double?
  private var samples: [[String: Any]] = []

  init(content: UIView, target: UIView, source: CGRect, destination: CGRect, track: ChatThrowCurve.PositionTrack, sourceBackground: UIColor, destinationBackground: UIColor) {
    self.content = content; self.target = target; self.window = content.window
    self.source = source; self.destination = destination; self.track = track; self.duration = track.duration
    self.sourceBackground = sourceBackground; self.destinationBackground = destinationBackground
    super.init()
    let link = CADisplayLink(target: self, selector: #selector(tick(_:)))
    let fps = Float(content.window?.screen.maximumFramesPerSecond ?? 60)
    link.preferredFrameRateRange = CAFrameRateRange(minimum: fps, maximum: fps, preferred: fps)
    self.link = link
    link.add(to: .main, forMode: .common)
  }

  private func rgba(_ color: UIColor) -> [Double] {
    var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
    color.getRed(&r, green: &g, blue: &b, alpha: &a)
    return [Double(r), Double(g), Double(b), Double(a)]
  }

  private func rect(_ rect: CGRect) -> [Double] {
    [Double(rect.minX), Double(rect.minY), Double(rect.width), Double(rect.height)]
  }

  private func frame(_ view: UIView, presentation: Bool) -> CGRect {
    let layer = presentation ? (view.layer.presentation() ?? view.layer) : view.layer
    let root = presentation ? (window?.layer.presentation() ?? window?.layer) : window?.layer
    return layer.convert(layer.bounds, to: root)
  }

  func didLand(on target: UIView) {
    content = target
    adoptedAt = CACurrentMediaTime() - started
    sample(event: "adopt", timestamp: CACurrentMediaTime(), budget: 0)
  }

  @objc private func tick(_ link: CADisplayLink) {
    sample(event: "frame", timestamp: link.timestamp, budget: link.targetTimestamp - link.timestamp)
    let elapsed = CACurrentMediaTime() - started
    if elapsed > duration + 0.35 { stop(cancelled: false) }
  }

  private func sample(event: String, timestamp: Double, budget: Double) {
    guard let content, let window, content.window === window else { return }
    let layer = content.layer.presentation() ?? content.layer
    var sample: [String: Any] = [
      "event": event, "t": timestamp - started, "sampleTime": CACurrentMediaTime() - started,
      "budget": budget, "adopted": adoptedAt != nil,
      "frame": rect(frame(content, presentation: true)),
      "modelFrame": rect(frame(content, presentation: false)),
      "scale": layer.value(forKeyPath: "transform.scale.x") as? Double ?? 1,
      "bounds": [Double(layer.bounds.width), Double(layer.bounds.height)],
      "background": rgba(layer.backgroundColor.map { UIColor(cgColor: $0) } ?? destinationBackground),
    ]
    if let label = (content as? ChatMessageContent)?.label {
      let textLayer = label.layer.presentation() ?? label.layer
      sample["textBounds"] = [Double(textLayer.bounds.width), Double(textLayer.bounds.height)]
      sample["textOpacity"] = label.isHidden ? 0 : Double(textLayer.opacity)
    }
    if let target, target.window === window { sample["targetFrame"] = rect(frame(target, presentation: true)) }
    samples.append(sample)
  }

  func stop(cancelled: Bool) {
    guard link != nil else { return }
    link?.invalidate(); link = nil
    let report: [String: Any] = [
      "metric": "CADisplayLink + Core Animation presentation geometry; not GPU-presented FPS",
      "maximumFPS": window?.screen.maximumFramesPerSecond ?? 0,
      "source": rect(source), "destination": rect(destination), "duration": duration,
      "flight": ChatThrowCurve.duration, "path": track.points.map { [Double($0.x), Double($0.y)] }, "pathTimes": track.times,
      "sourceBackground": rgba(sourceBackground), "destinationBackground": rgba(destinationBackground),
      "cancelled": cancelled, "samples": samples,
    ]
    if let data = try? JSONSerialization.data(withJSONObject: report, options: [.sortedKeys]) {
      try? data.write(to: FileManager.default.temporaryDirectory
        .appendingPathComponent("lody-throw-\(UUID().uuidString).json"), options: .atomic)
    }
  }
}
#endif
