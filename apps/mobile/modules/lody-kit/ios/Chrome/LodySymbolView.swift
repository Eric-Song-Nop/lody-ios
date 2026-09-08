import ExpoModulesCore
import UIKit

final class LodySymbolView: ExpoView {
  private let imageView = UIImageView()
  private var symbol = "circle"
  private var pointSize: CGFloat = 17

  required init(appContext: AppContext? = nil) {
    super.init(appContext: appContext)
    imageView.contentMode = .scaleAspectFit
    imageView.isAccessibilityElement = false
    addSubview(imageView)
    apply()
  }

  override func layoutSubviews() {
    super.layoutSubviews()
    imageView.frame = bounds
  }

  func setSymbol(_ value: String) {
    symbol = value
    apply()
  }

  func setPointSize(_ value: Double) {
    pointSize = CGFloat(value)
    apply()
  }

  func setTint(_ value: String) {
    imageView.tintColor = lodyTint(value)
  }

  private func apply() {
    imageView.image = UIImage(systemName: symbol)?.withConfiguration(
      UIImage.SymbolConfiguration(pointSize: pointSize, weight: .medium)
    )
  }
}
