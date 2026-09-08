enum ChatHaptics {
  static func shouldNotifyTurnCompletion(
    previousLive: String?,
    nextLive: String?,
    processEntryID: String,
    inWindow: Bool
  ) -> Bool {
    inWindow && processEntryID.isEmpty && previousLive != nil && previousLive != nextLive
  }
}
