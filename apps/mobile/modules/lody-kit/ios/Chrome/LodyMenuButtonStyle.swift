import UIKit

@MainActor
enum LodyMenuButtonStyle {
  static func apply(_ value: UIButton.Configuration, to button: UIButton) {
    var configuration = value
    configuration.titleLineBreakMode = .byTruncatingTail
    button.configuration = configuration
    button.titleLabel?.numberOfLines = 1
    button.titleLabel?.lineBreakMode = .byTruncatingTail
  }
}
