import UIKit

// A partially offscreen text view must retain every line when scrolling exposes it.
let window = UIWindow(frame: CGRect(x: 0, y: 0, width: 390, height: 400))
let view = ChatTextView(frame: CGRect(x: 0, y: 350, width: 350, height: 600))
window.addSubview(view)
view.setText(NSAttributedString(string: (1...20).map { "Line \($0): scrolling keeps this content" }.joined(separator: "\n"), attributes: [.font: UIFont.systemFont(ofSize: 17), .foregroundColor: UIColor.black]))
func draw() -> Data {
  UIGraphicsImageRenderer(size: view.bounds.size).image { context in
    UIColor.white.setFill()
    context.fill(view.bounds)
    view.draw(view.bounds)
  }.pngData()!
}
let initiallyClipped = draw()
view.frame.origin.y = 0
let exposedByScrolling = draw()
precondition(initiallyClipped == exposedByScrolling, "Text drawing must not depend on the current scroll position")
print("Chat render: offscreen lines remain drawn across scrolling")

let shineView = ChatTextView(frame: CGRect(x: 0, y: 0, width: 200, height: 20))
window.addSubview(shineView)
shineView.setText(NSAttributedString(string: "正在处理", attributes: [
  .font: UIFont.systemFont(ofSize: 13),
  .foregroundColor: UIColor.systemBlue,
]))
func shineSnapshot() -> Data {
  UIGraphicsImageRenderer(size: shineView.bounds.size).image { context in
    UIColor.white.setFill()
    context.fill(shineView.bounds)
    shineView.draw(shineView.bounds)
  }.pngData()!
}
shineView.setShine(false)
let rest = shineSnapshot()
shineView.setShine(true)
// Sample a full cycle: its offscreen phase can legitimately match resting text.
let frames = (0..<10).map { _ in
  Thread.sleep(forTimeInterval: 0.16)
  return shineSnapshot()
}
if !UIAccessibility.isReduceMotionEnabled {
  precondition(frames.contains { $0 != rest }, "Shine must change glyph brightness")
  precondition(Set(frames).count > 1, "Shine must travel across glyphs")
}
shineView.setShine(false)
let still = shineSnapshot()
Thread.sleep(forTimeInterval: 0.4)
precondition(still == shineSnapshot(), "Completed process text must stay still")
print("Chat render: process shine travels across running glyphs")

let durationRow = ChatRow(
  id: "turn:duration",
  entryID: "reply",
  kind: "duration",
  text: "Working for 3s",
  running: true,
  workDurationMs: 3_000
)
let durationCell = ChatCell(frame: CGRect(x: 0, y: 0, width: 320, height: 44))
window.addSubview(durationCell)
durationCell.configure(durationRow, text: NSAttributedString(string: durationRow.text))
durationCell.layoutIfNeeded()
precondition(!durationCell.spinner.isAnimating, "The duration label must not show a loading indicator")
precondition(ChatCell.leading(durationRow) == 0, "The duration label must align to the full row's leading edge")
precondition(ChatCell.textWidth(durationRow, width: 320) == 320,
  "The duration label must not reserve a trailing indicator slot")
print("Chat render: duration label is static and uses the full row width")

let separatorColor = UIColor.separator.resolvedColor(with: durationCell.traitCollection).cgColor
let durationSeparator = durationCell.contentView.subviews.first {
  $0.backgroundColor?.resolvedColor(with: durationCell.traitCollection).cgColor == separatorColor
}
precondition(durationSeparator?.frame.minX == 0 && durationSeparator?.frame.maxX == 320,
  "The duration separator must span the full row width")
precondition(durationSeparator?.frame.maxY == durationCell.contentView.bounds.maxY,
  "The duration separator must sit directly below the label row")
print("Chat render: duration separator spans the row below the label")
