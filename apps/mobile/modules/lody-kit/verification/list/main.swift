import UIKit

let menuButton = UIButton(type: .system)
var menuConfiguration = UIButton.Configuration.plain()
menuConfiguration.attributedTitle = AttributedString("我的超长工作区名称不能折行")
LodyMenuButtonStyle.apply(menuConfiguration, to: menuButton)
assert(menuButton.titleLabel?.numberOfLines == 1, "Workspace menu title must stay on one line")
assert(menuButton.titleLabel?.lineBreakMode == .byTruncatingTail, "Long workspace names must truncate at the tail")
assert(menuButton.configuration?.titleLineBreakMode == .byTruncatingTail, "The button configuration must not restore wrapping")

var swipedState = UICellConfigurationState(traitCollection: UITraitCollection())
swipedState.isSwiped = true
swipedState.isSelected = true
swipedState.isHighlighted = true
let swipedBackgroundState = LodyListCellBackground.visualState(for: swipedState)
assert(!swipedBackgroundState.isSwiped, "Swipe actions must use the resting row background")
assert(!swipedBackgroundState.isSelected, "Swipe actions must not render the selected background")
assert(!swipedBackgroundState.isHighlighted, "Swipe actions must not render the highlighted background")

var tappedState = UICellConfigurationState(traitCollection: UITraitCollection())
tappedState.isSelected = true
tappedState.isHighlighted = true
let tappedBackgroundState = LodyListCellBackground.visualState(for: tappedState)
assert(tappedBackgroundState.isSelected, "Normal row selection must stay visible")
assert(tappedBackgroundState.isHighlighted, "Normal tap highlighting must stay visible")

assert(LodyListPhoto.url("person.crop.circle") == nil)
assert(LodyListPhoto.url("https://avatars.githubusercontent.com/u/1")?.scheme == "https")
assert(LodyListPhoto.url("http://avatars.githubusercontent.com/u/1") == nil)
assert(LodyListPhoto.url("javascript:alert(1)") == nil)
assert(LodyListPhoto.url("https://user:pass@example.com/a.png") == nil)
assert(LodyListPhoto.url("data:image/png;base64,aa")?.scheme == "data")
assert(LodyListPhoto.url("file:///tmp/a.png")?.isFileURL == true)

let source = UIGraphicsImageRenderer(size: CGSize(width: 80, height: 40)).image { _ in
  UIColor.red.setFill()
  UIRectFill(CGRect(x: 0, y: 0, width: 80, height: 40))
}
let photo = LodyListPhoto.circular(source)
assert(photo.size == LodyListPhoto.size)
assert(photo.renderingMode == .alwaysOriginal)

func alpha(_ image: UIImage, x: CGFloat, y: CGFloat) -> CGFloat {
  var pixel: [UInt8] = [0, 0, 0, 0]
  let space = CGColorSpaceCreateDeviceRGB()
  let context = CGContext(
    data: &pixel,
    width: 1,
    height: 1,
    bitsPerComponent: 8,
    bytesPerRow: 4,
    space: space,
    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
  )!
  context.translateBy(x: -x, y: -y)
  context.draw(image.cgImage!, in: CGRect(origin: .zero, size: image.size))
  return CGFloat(pixel[3]) / 255
}

assert(alpha(photo, x: 0, y: 0) < 0.05, "Photo corners must be transparent")
assert(alpha(photo, x: photo.size.width - 1, y: 0) < 0.05, "Photo corners must be transparent")
assert(alpha(photo, x: photo.size.width / 2, y: photo.size.height / 2) > 0.9, "Photo center must stay opaque")

let disk = FileManager.default.temporaryDirectory.appendingPathComponent("lody-list-photo.png")
try! source.pngData()!.write(to: disk)
let fromFile = LodyListPhoto.image(for: disk, ready: { _ in })
assert(fromFile != nil, "file URLs must decode a circular photo")
assert(fromFile!.renderingMode == .alwaysOriginal)
assert(alpha(fromFile!, x: 0, y: 0) < 0.05)

let dataURL = URL(string: "data:image/png;base64," + source.pngData()!.base64EncodedString())!
let fromData = LodyListPhoto.image(for: dataURL, ready: { _ in })
assert(fromData != nil, "data image URLs must decode a circular photo")

print("PASS: workspace title stays single-line, swiped rows stay unselected, and list photos are safely cropped")

let restingState = UICellConfigurationState(traitCollection: UITraitCollection())
assert(LodyListCellBackground.outlineConfiguration(for: restingState).backgroundColor == .clear, "Outline rows at rest must show the section card, not their own background")
assert(LodyListCellBackground.outlineConfiguration(for: tappedState).backgroundColor != .clear, "Outline rows must still paint their highlight")
assert(LodyListCellBackground.outlineConfiguration(for: swipedState).backgroundColor != .clear, "A swiped outline row must carry an opaque background with it")
assert(LodySectionCardView(frame: .zero).layer.cornerRadius > 0, "The section card must be rounded")
