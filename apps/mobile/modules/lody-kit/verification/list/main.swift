import UIKit

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

print("PASS: list photos are https/data/file URLs cropped to a circle, not SF Symbols")
