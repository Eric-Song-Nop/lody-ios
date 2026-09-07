import ImageIO
import PhotosUI
import QuickLook
import UIKit
import UniformTypeIdentifiers

struct ChatAttachment: Equatable {
  let id: String
  let name: String
  let url: URL
  let isImage: Bool

  static func thumbnail(_ url: URL) -> UIImage? {
    guard url.isFileURL, let source = CGImageSourceCreateWithURL(url as CFURL, nil),
      let image = CGImageSourceCreateThumbnailAtIndex(source, 0, [
        kCGImageSourceCreateThumbnailFromImageAlways: true,
        kCGImageSourceCreateThumbnailWithTransform: true,
        kCGImageSourceThumbnailMaxPixelSize: 768,
      ] as CFDictionary) else { return nil }
    return UIImage(cgImage: image)
  }

  static func store(_ url: URL) -> URL? {
    let access = url.startAccessingSecurityScopedResource()
    defer { if access { url.stopAccessingSecurityScopedResource() } }
    var directory: ObjCBool = false
    guard FileManager.default.fileExists(atPath: url.path, isDirectory: &directory), !directory.boolValue else { return nil }
    let destination = FileManager.default.temporaryDirectory
      .appendingPathComponent(UUID().uuidString + "-" + url.lastPathComponent)
    return (try? FileManager.default.copyItem(at: url, to: destination)) == nil ? nil : destination
  }

  static func store(_ data: Data, name: String) -> URL? {
    let destination = FileManager.default.temporaryDirectory
      .appendingPathComponent(UUID().uuidString + "-" + name)
    return (try? data.write(to: destination)) == nil ? nil : destination
  }

  private static func pastedType(for provider: NSItemProvider) -> UTType? {
    if provider.hasItemConformingToTypeIdentifier(UTType.fileURL.identifier) { return .fileURL }
    if provider.hasItemConformingToTypeIdentifier(UTType.url.identifier) { return nil }
    return provider.registeredContentTypes.first { type in
      !type.conforms(to: .directory)
        && !type.conforms(to: .url)
        && !type.conforms(to: .text)
    }
  }

  static func canPaste(_ providers: [NSItemProvider]) -> Bool {
    providers.contains { pastedType(for: $0) != nil }
  }

  @discardableResult
  static func paste(_ providers: [NSItemProvider], completion: @escaping ([ChatAttachment]) -> Void) -> Bool {
    let items = providers.enumerated().compactMap { index, provider in
      pastedType(for: provider).map { (index, provider, $0) }
    }
    guard !items.isEmpty else { return false }
    let group = DispatchGroup()
    let lock = NSLock()
    var pasted: [(Int, ChatAttachment)] = []
    func append(_ index: Int, _ provider: NSItemProvider, _ type: UTType, _ source: URL) {
      guard source.isFileURL, let copy = store(source) else { return }
      var name = provider.suggestedName?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
      if name.isEmpty { name = source.lastPathComponent }
      if URL(fileURLWithPath: name).pathExtension.isEmpty, let suffix = type.preferredFilenameExtension {
        name += "." + suffix
      }
      let isImage = type.conforms(to: .image) || UTType(filenameExtension: URL(fileURLWithPath: name).pathExtension)?.conforms(to: .image) == true
      lock.lock()
      pasted.append((index, ChatAttachment(id: UUID().uuidString, name: name, url: copy, isImage: isImage)))
      lock.unlock()
    }
    for (index, provider, type) in items {
      group.enter()
      if type == .fileURL {
        provider.loadObject(ofClass: NSURL.self) { object, _ in
          defer { group.leave() }
          guard let source = object as? URL, source.isFileURL else { return }
          append(index, provider, UTType(filenameExtension: source.pathExtension) ?? .item, source)
        }
      } else {
        provider.loadFileRepresentation(forTypeIdentifier: type.identifier) { source, _ in
          defer { group.leave() }
          guard let source else { return }
          append(index, provider, type, source)
        }
      }
    }
    group.notify(queue: .main) {
      let ordered = pasted.sorted { $0.0 < $1.0 }.map(\.1)
      if !ordered.isEmpty { completion(ordered) }
    }
    return true
  }
}

final class ChatAttachmentPicker: NSObject, UIDocumentPickerDelegate {
  var onPick: (([ChatAttachment]) -> Void)?

  func files(from controller: UIViewController) {
    let picker = UIDocumentPickerViewController(forOpeningContentTypes: [.item], asCopy: true)
    picker.allowsMultipleSelection = true
    picker.delegate = self
    controller.present(picker, animated: true)
  }

  func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) {
    let picked = urls.compactMap { url -> ChatAttachment? in
      guard let copy = ChatAttachment.store(url) else { return nil }
      return ChatAttachment(id: UUID().uuidString, name: url.lastPathComponent, url: copy, isImage: false)
    }
    guard !picked.isEmpty else { return }
    onPick?(picked)
  }
}

final class ChatPhotoLibraryPicker: NSObject, PHPickerViewControllerDelegate {
  var onPick: (([ChatAttachment]) -> Void)?

  func present(from controller: UIViewController) {
    var config = PHPickerConfiguration(photoLibrary: .shared())
    config.filter = .images
    config.selectionLimit = 10
    config.selection = .ordered
    let picker = PHPickerViewController(configuration: config)
    picker.delegate = self
    controller.present(picker, animated: true)
  }

  func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
    guard !results.isEmpty else { picker.dismiss(animated: true); return }
    let group = DispatchGroup()
    let lock = NSLock()
    var picked: [(Int, ChatAttachment)] = []
    for (index, result) in results.enumerated() {
      group.enter()
      result.itemProvider.loadFileRepresentation(forTypeIdentifier: UTType.image.identifier) { url, _ in
        defer { group.leave() }
        guard let url, let copy = ChatAttachment.store(url) else { return }
        let id = result.assetIdentifier ?? UUID().uuidString
        lock.lock()
        picked.append((index, ChatAttachment(id: id, name: url.lastPathComponent, url: copy, isImage: true)))
        lock.unlock()
      }
    }
    group.notify(queue: .main) { [weak self] in
      let ordered = picked.sorted { $0.0 < $1.0 }.map(\.1)
      picker.dismiss(animated: true) { [weak self] in
        guard !ordered.isEmpty else { return }
        self?.onPick?(ordered)
      }
    }
  }
}

final class ChatAttachmentPreview: QLPreviewController, QLPreviewControllerDataSource {
  private let urls: [URL]

  init(_ items: [ChatAttachment], index: Int) {
    urls = items.map(\.url)
    super.init(nibName: nil, bundle: nil)
    dataSource = self
    currentPreviewItemIndex = index
  }
  required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

  func numberOfPreviewItems(in controller: QLPreviewController) -> Int { urls.count }
  func previewController(_ controller: QLPreviewController, previewItemAt index: Int) -> QLPreviewItem { urls[index] as NSURL }
}

final class ChatAttachmentBar: UIScrollView {
  var onRemove: ((String) -> Void)?
  var onPreview: ((String) -> Void)?
  private let stack = UIStackView()
  private var rendered: [ChatAttachment] = []

  init() {
    super.init(frame: .zero)
    showsHorizontalScrollIndicator = false
    alwaysBounceHorizontal = false
    stack.axis = .horizontal
    stack.spacing = 8
    stack.translatesAutoresizingMaskIntoConstraints = false
    addSubview(stack)
    NSLayoutConstraint.activate([
      stack.topAnchor.constraint(equalTo: contentLayoutGuide.topAnchor),
      stack.bottomAnchor.constraint(equalTo: contentLayoutGuide.bottomAnchor),
      stack.leadingAnchor.constraint(equalTo: contentLayoutGuide.leadingAnchor),
      stack.trailingAnchor.constraint(equalTo: contentLayoutGuide.trailingAnchor),
      stack.heightAnchor.constraint(equalTo: frameLayoutGuide.heightAnchor),
    ])
  }
  required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

  func render(_ items: [ChatAttachment]) {
    guard items != rendered else { return }
    rendered = items
    stack.arrangedSubviews.forEach { $0.removeFromSuperview() }
    for item in items { stack.addArrangedSubview(pill(item)) }
  }

  func attachmentFrame(id: String) -> CGRect? {
    guard let index = rendered.firstIndex(where: { $0.id == id }), index < stack.arrangedSubviews.count else { return nil }
    let view = stack.arrangedSubviews[index]
    return view.convert(view.bounds, to: self)
  }

  private func pill(_ item: ChatAttachment) -> UIView {
    var config = UIButton.Configuration.plain()
    config.image = UIImage(systemName: item.isImage ? "photo" : "doc")
    config.imagePadding = 5
    config.baseForegroundColor = .label
    config.preferredSymbolConfigurationForImage = UIImage.SymbolConfiguration(pointSize: 12)
    config.contentInsets = NSDirectionalEdgeInsets(top: 0, leading: 11, bottom: 0, trailing: 32)
    config.attributedTitle = AttributedString(item.name, attributes: AttributeContainer([
      .font: UIFont.systemFont(ofSize: 13),
    ]))
    config.titleLineBreakMode = .byTruncatingMiddle
    let button = UIButton(configuration: config)
    button.accessibilityLabel = LodyStrings.text("native.chat.attachment.preview", ["name": item.name])
    button.addAction(UIAction { [weak self] _ in self?.onPreview?(item.id) }, for: .touchUpInside)
    let remove = UIButton(type: .system)
    remove.setImage(UIImage(systemName: "xmark.circle.fill"), for: .normal)
    remove.setPreferredSymbolConfiguration(UIImage.SymbolConfiguration(pointSize: 13), forImageIn: .normal)
    remove.tintColor = .tertiaryLabel
    remove.accessibilityLabel = LodyStrings.text("native.chat.attachment.remove", ["name": item.name])
    remove.addAction(UIAction { [weak self] _ in self?.onRemove?(item.id) }, for: .touchUpInside)
    let surface = UIVisualEffectView(effect: nil)
    if #available(iOS 26.0, *) {
      let glass = UIGlassEffect(style: .regular)
      glass.isInteractive = true
      surface.effect = glass
      surface.cornerConfiguration = .capsule()
    } else {
      surface.backgroundColor = .secondarySystemBackground
      surface.layer.cornerRadius = 17
      surface.layer.cornerCurve = .continuous
      surface.clipsToBounds = true
    }
    surface.contentView.addSubview(button)
    surface.contentView.addSubview(remove)
    button.translatesAutoresizingMaskIntoConstraints = false
    remove.translatesAutoresizingMaskIntoConstraints = false
    NSLayoutConstraint.activate([
      button.topAnchor.constraint(equalTo: surface.contentView.topAnchor), button.bottomAnchor.constraint(equalTo: surface.contentView.bottomAnchor),
      button.leadingAnchor.constraint(equalTo: surface.contentView.leadingAnchor), button.trailingAnchor.constraint(equalTo: surface.contentView.trailingAnchor),
      remove.topAnchor.constraint(equalTo: surface.contentView.topAnchor), remove.bottomAnchor.constraint(equalTo: surface.contentView.bottomAnchor),
      remove.trailingAnchor.constraint(equalTo: surface.contentView.trailingAnchor, constant: -4),
      remove.widthAnchor.constraint(equalToConstant: 30),
      surface.widthAnchor.constraint(lessThanOrEqualToConstant: 200),
      surface.heightAnchor.constraint(equalToConstant: 34),
    ])
    return surface
  }
}
