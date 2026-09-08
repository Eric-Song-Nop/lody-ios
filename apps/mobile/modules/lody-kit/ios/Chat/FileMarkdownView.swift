import Litext
import MarkdownParser
import MarkdownView
import UIKit

// Decorate parsed links, never regex-rewrite Markdown source (code fences and
// escaped text must remain literal). Sizing and visible views use this together.
final class FileMarkdownView: MarkdownTextView {
  private static let marker = "\u{F0000}lody-file:"

  static func content(_ source: MarkdownContent) -> MarkdownContent {
    let blocks = source.blocks.rewrite { (node: MarkdownInlineNode) -> [MarkdownInlineNode] in
      guard case let .link(destination, children) = node,
        ChatFileLink(destination) != nil else { return [node] }
      return [.link(destination: destination, children: [.text(marker + destination)] + children)]
    }
    return MarkdownContent(blocks: blocks, rendered: source.rendered, highlightMaps: source.highlightMaps, locale: source.locale)
  }

  override func decorate(inlineText text: NSAttributedString, theme: MarkdownTheme) -> NSAttributedString {
    guard text.string.hasPrefix(Self.marker) else { return text }
    let href = String(text.string.dropFirst(Self.marker.count))
    guard let target = ChatFileLink(href) else { return text }
    let icon = FileLinkButton(type: .system)
    icon.setImage(MaterialFileIcon.image(for: target.path), for: .normal)
    icon.imageView?.contentMode = .scaleAspectFit
    icon.tintColor = .systemBlue
    icon.accessibilityLabel = (target.path as NSString).lastPathComponent
    icon.addAction(UIAction { [weak self] _ in
      self?.linkHandler?(.string(href), NSRange(location: 0, length: 0), .zero)
    }, for: .touchUpInside)
    let attachment = TextLabel.Attachment()
    attachment.size = CGSize(width: theme.fonts.body.pointSize + 5, height: theme.fonts.body.pointSize)
    attachment.view = icon
    let result = NSMutableAttributedString(attributedString: attachment.attributedString(attributes: text.attributes(at: 0, effectiveRange: nil)))
    // The run delegate supplies the icon's width; no placeholder glyph is drawn.
    result.replaceCharacters(in: NSRange(location: 0, length: result.length), with: "\u{200B}")
    return result
  }

  func fileActions(_ content: MarkdownContent) -> [UIAccessibilityCustomAction] {
    func inlineNodes(_ blocks: [MarkdownBlockNode]) -> [MarkdownInlineNode] {
      blocks.flatMap { block in
        switch block {
        case .paragraph(let content), .heading(_, let content): return content
        case .table(_, let rows): return rows.flatMap { $0.cells.flatMap(\.content) }
        default: return inlineNodes(block.children)
        }
      }
    }
    // Read the parsed content, including tables and the latest streamed links,
    // rather than the label's previous frame while throttled rendering catches up.
    return inlineNodes(content.blocks).collect { node -> [UIAccessibilityCustomAction] in
      guard case let .link(href, children) = node, let target = ChatFileLink(href) else { return [] }
      let label = children.collect { child -> [String] in
        switch child {
        case .text(let text) where !text.hasPrefix(Self.marker): return [text]
        case .code(let text): return [text]
        default: return []
        }
      }.joined()
      return [UIAccessibilityCustomAction(name: label.isEmpty ? (target.path as NSString).lastPathComponent : label) { [weak self] _ in
        self?.linkHandler?(.string(href), NSRange(location: 0, length: 0), .zero)
        return true
      }]
    }
  }

}

private final class FileLinkButton: UIButton {
  override func point(inside point: CGPoint, with event: UIEvent?) -> Bool {
    bounds.insetBy(dx: min(0, (bounds.width - 44) / 2), dy: min(0, (bounds.height - 44) / 2)).contains(point)
  }
}

enum MaterialFileIcon {
  static func image(for path: String) -> UIImage? {
    let name = "material-\(ChatFileLink.iconName(for: path))"
    let image = UIImage(named: name, in: Bundle(for: LodyKitModule.self), compatibleWith: nil)
      ?? UIImage(named: name, in: .main, compatibleWith: nil)
    return image?.withRenderingMode(.alwaysOriginal)
  }
}
