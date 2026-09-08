import UIKit

final class ChatMarkdownCell: UICollectionViewCell {
  private var markdown: ChatMarkdownView?
  private let icon = UIImageView()
  private let spinner = UIActivityIndicatorView(style: .medium)
  private(set) var row: ChatRow?
  var onLink: ((String) -> Void)?

  override init(frame: CGRect) {
    super.init(frame: frame)
    icon.contentMode = .center
    contentView.addSubview(icon)
    contentView.addSubview(spinner)
    contentView.clipsToBounds = true
    isAccessibilityElement = true
  }
  required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

  func configure(_ row: ChatRow, markdown: ChatMarkdownView) {
    self.row = row
    if self.markdown !== markdown {
      if self.markdown?.superview === contentView { self.markdown?.removeFromSuperview() }
      self.markdown = markdown
      contentView.addSubview(markdown)
    }
    markdown.onLink = { [weak self] in self?.onLink?($0) }
    icon.image = row.symbol.isEmpty ? nil : UIImage(systemName: row.symbol, withConfiguration: ChatCell.iconSymbolConfiguration(for: row))
    icon.tintColor = row.attention ? .systemOrange : .secondaryLabel
    row.running ? spinner.startAnimating() : spinner.stopAnimating()
    accessibilityIdentifier = row.id
    accessibilityLabel = row.text
    accessibilityCustomActions = markdown.fileActions
    accessibilityTraits = row.actionable ? .button : .staticText
    setNeedsLayout()
  }

  override func prepareForReuse() {
    super.prepareForReuse()
    row = nil
    if markdown?.superview === contentView {
      markdown?.onLink = nil
      markdown?.removeFromSuperview()
    }
    markdown = nil
  }

  override func layoutSubviews() {
    super.layoutSubviews()
    guard let row, let markdown else { return }
    let width = contentView.bounds.width
    let inset = ChatCell.leading(row)
    let textWidth = ChatCell.textWidth(row, width: width)
    markdown.measure(width: textWidth)
    let height = markdown.measuredHeight
    markdown.frame = CGRect(x: inset, y: 6, width: textWidth, height: height)
    icon.frame = ChatCell.iconFrame(for: row, textY: 6, textHeight: height)
    spinner.frame = CGRect(x: width - 24, y: (bounds.height - 20) / 2, width: 20, height: 20)
    var view: UIView? = superview
    while let current = view, !(current is UIScrollView) { view = current.superview }
    markdown.trackedScrollView = view as? UIScrollView
  }
}
