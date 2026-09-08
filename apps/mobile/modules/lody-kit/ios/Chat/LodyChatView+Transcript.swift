import UIKit

extension LodyChatView {
  func setProcessStartID(_ id: String) {
    guard processStartID != id else { return }
    processStartID = id
    applyRows()
  }

  func setProcessEntryID(_ id: String) {
    guard processEntryID != id else { return }
    processEntryID = id
    composer.isHidden = !id.isEmpty
    setNeedsLayout()
    applyRows()
  }

  func setEntries(_ json: String) {
    pendingEntries = json
    scheduleUpdate()
  }

  func scheduleUpdate() {
    guard update == nil, !decoding else { return }
    let work = DispatchWorkItem { [weak self] in
      guard let self else { return }
      self.update = nil
      guard let json = self.pendingEntries else { return }
      self.pendingEntries = nil
      self.decoding = true
      self.preparation.async { [weak self] in
        let decoded = Result { () -> [ChatEntry] in
          let entries = try JSONDecoder().decode([ChatEntry].self, from: Data(json.utf8))
          guard Set(entries.map(\.id)).count == entries.count,
                entries.allSatisfy({ Set($0.items.map(\.itemId)).count == $0.items.count }) else {
            throw NSError(domain: "LodyChat", code: 1)
          }
          return entries
        }
        DispatchQueue.main.async { [weak self] in
          guard let self else { return }
          self.decoding = false
          switch decoded {
          case .success(let entries):
            #if DEBUG
            self.streamPerformanceProbe?.receive(entries)
            #endif
            self.displayError = nil
            let userID = entries.last { $0.role == "user" && !$0.isQueued }?.id
            if self.processEntryID.isEmpty, let userID, userID != self.lastUserID,
               self.awaitingUserAnchor {
              self.liveEntryID = nil
              self.anchoredUserID = userID + ":user"
              self.awaitingUserAnchor = false
              self.trackingPausedByGesture = false
              self.followsBottom = true
            }
            self.lastUserID = userID
            self.stream.receive(entries, animate: self.window != nil && !UIAccessibility.isReduceMotionEnabled)
            self.startFrameTimer()
          case .failure:
            self.displayError = LodyStrings.text("native.chat.error.transcript")
          }
          if self.pendingEntries != nil { self.scheduleUpdate() }
        }
      }
    }
    update = work
    DispatchQueue.main.asyncAfter(deadline: .now() + 0.05, execute: work)
  }

  func startFrameTimer() {
    guard frameTimer == nil else { return }
    guard !rendering else { framePending = true; return }
    guard window != nil else { stream.finish(); return }
    let interval = ChatStream.commitInterval(tailLength: renderTailLength)
    let delay = max(0.001, lastRenderTime + interval - CACurrentMediaTime())
    let timer = Timer(timeInterval: delay, repeats: false) { [weak self] _ in
      guard let self else { return }
      self.frameTimer = nil
      if UIAccessibility.isReduceMotionEnabled { self.stream.finish() }
      self.renderFrame()
    }
    frameTimer = timer
    RunLoop.main.add(timer, forMode: .common)
  }

  func renderFrame() {
    guard !rendering else { framePending = true; return }
    rendering = true
    lastRenderTime = CACurrentMediaTime()
    stream.advance()
    let entries = stream.presentation
    let parser = store.parser
    preparation.async { [weak self] in
      for entry in entries.suffix(2) {
        for item in entry.items where item.type == "text" || item.type == "thought" {
          _ = parser.parse(item.text ?? "")
        }
      }
      DispatchQueue.main.async { [weak self] in
        guard let self else { return }
        self.transcript.entries = entries
        self.applyRows()
        self.rendering = false
        if self.framePending || self.stream.hasPending {
          self.framePending = false
          self.startFrameTimer()
        }
      }
    }
  }

  func text(for row: ChatRow) -> NSAttributedString {
    let scale = UIFont.dynamicScale(compatibleWith: traitCollection)
    let paragraph = NSMutableParagraphStyle()
    let lineHeight = (row.kind == "user" ? 25 : 18) * scale
    paragraph.minimumLineHeight = lineHeight
    paragraph.maximumLineHeight = lineHeight
    let font = UIFont.dynamic(of: row.kind == "user" ? 17 : 13, compatibleWith: traitCollection)
    return NSAttributedString(string: row.text, attributes: [
      .font: font,
      .foregroundColor: textColor(for: row),
      .paragraphStyle: paragraph,
      .baselineOffset: (lineHeight - font.lineHeight) / 2,
    ])
  }

  func applyRows() {
    guard !applying else { needsApply = true; return }
    applying = true
    #if DEBUG
    let commitStart = CACurrentMediaTime()
    #endif
    let previousOffset = collection.contentOffset.y
    if composerHasAcknowledgedSend, let pendingSend,
       transcript.entries.contains(where: { $0.id == pendingSend.id }),
       pendingSend.rows(entries: transcript.entries).isEmpty {
      self.pendingSend = nil
    }
    var queue = transcript.entries.filter(\.isQueued).map { entry in
      ChatQueuedDraft(
        id: entry.id,
        text: entry.items.compactMap { $0.type == "image" ? nil : $0.text }.joined(separator: "\n"),
        canSteer: entry.canSteer != false,
        attachments: entry.items.compactMap { $0.type == "image" ? $0.image?.fileName : nil }
      )
    }
    if let pendingSend, pendingSend.queue == true, pendingSend.failed != true,
       !transcript.entries.contains(where: { $0.id == pendingSend.id }) {
      queue.append(ChatQueuedDraft(
        id: pendingSend.id,
        text: pendingSend.text,
        canSteer: false,
        attachments: pendingSend.attachments.map(\.name)
      ))
    }
    composer.setQueue(queue)
    let now = Date().timeIntervalSince1970 * 1000
    var projected = transcript.rows(
      processEntryID: processEntryID,
      processStartID: processStartID,
      now: now,
      turnStartedAt: turnStartedAt
    )
    if processEntryID.isEmpty, let pendingSend { projected += pendingSend.rows(entries: transcript.entries) }
    updateWorkDurationTimer(rows: projected)
    let liveEntryID = transcript.entries.last { $0.isRunning && (processEntryID.isEmpty || $0.id == processEntryID) }?.id
    let previousLive = self.liveEntryID
    let starting = previousLive == nil && liveEntryID != nil
    let nearTail = collection.contentSize.height - collection.bounds.height + collection.adjustedContentInset.bottom - previousOffset < CGFloat(ChatScroll.resumeDistance)
    let following = followsBottom || (starting && nearTail && !trackingPausedByGesture)
    followsBottom = following
    let completing = previousLive != nil && liveEntryID == nil
    // A stale running reply can complete together with an entire newer history.
    // Only fold in place when it is still the tail; bulk sync keeps the viewport anchor.
    let folding = completing && processEntryID.isEmpty && window != nil && projected.last?.entryID == previousLive
    let anchorID = folding && following
      ? projected.last(where: { $0.entryID == previousLive && $0.kind == "text" })?.id
      : collection.indexPathsForVisibleItems.sorted().compactMap { dataSource.itemIdentifier(for: $0) }.first(where: { id in projected.contains { $0.id == id } })
    let anchor = anchorID.flatMap { id -> (String, CGFloat)? in
      guard let index = dataSource.indexPath(for: id), let frame = collection.layoutAttributesForItem(at: index)?.frame else { return nil }
      return (id, frame.minY - previousOffset)
    }
    guard Set(projected.map(\.id)).count == projected.count else {
      applying = false
      displayError = LodyStrings.text("native.chat.error.transcript")
      return
    }
    if ChatHaptics.shouldNotifyTurnCompletion(
      previousLive: previousLive,
      nextLive: liveEntryID,
      processEntryID: processEntryID,
      inWindow: window != nil
    ) {
      turnFeedback.notificationOccurred(.success)
    }
    if liveEntryID != nil && processEntryID.isEmpty && window != nil && previousLive != liveEntryID {
      turnFeedback.prepare()
    }
    self.liveEntryID = liveEntryID
    let previous = rows
    prepareRowHeights(projected, previous: previous, animate: !folding)
    rows = Dictionary(projected.map { ($0.id, $0) }, uniquingKeysWith: { _, last in last })
    measurements = measurements.filter { rows[$0.key] != nil }
    store.retain(Set(rows.keys))
    var snapshot = NSDiffableDataSourceSnapshot<String, String>()
    let grouped = Dictionary(grouping: projected, by: \.entryID)
    var entryIDs = transcript.entries.map(\.id)
    if let pendingSend, !entryIDs.contains(pendingSend.id) { entryIDs.append(pendingSend.id) }
    for id in entryIDs {
      guard let entryRows = grouped[id], !entryRows.isEmpty else { continue }
      snapshot.appendSections([id])
      snapshot.appendItems(entryRows.map(\.id), toSection: id)
    }
    snapshot.reconfigureItems(projected.filter { previous[$0.id] != nil && previous[$0.id] != $0 }.map(\.id))
    empty.isHidden = !projected.isEmpty
    let updateLayout = { [self] in
      self.collection.collectionViewLayout.invalidateLayout()
      self.collection.layoutIfNeeded()
      self.updateBottomInset()
      if !folding || !self.followsBottom, let (id, offset) = anchor, let index = self.dataSource.indexPath(for: id), let frame = self.collection.layoutAttributesForItem(at: index)?.frame {
        self.collection.contentOffset.y = max(-self.collection.adjustedContentInset.top, frame.minY - offset)
      }
      if self.followsBottom { self.scrollToBottom() }
      if !projected.isEmpty { self.hasPositionedContent = true }
      if !self.rowHeights.isEmpty { self.startMotion() }
      self.updateBottomButton()
      self.deliverPendingContent()
    }
    let finish = { [weak self] in
      guard let self else { return }
      #if DEBUG
      self.streamPerformanceProbe?.commit(milliseconds: (CACurrentMediaTime() - commitStart) * 1000)
      #endif
      self.applying = false
      if let tail = projected.last(where: { $0.streaming }) {
        self.renderTailLength = self.store.tailLength(id: tail.id)
      }
      if self.needsApply { self.needsApply = false; self.applyRows() }
    }
    if folding && !UIAccessibility.isReduceMotionEnabled {
      UIView.animate(withDuration: 0.22, delay: 0, options: [.curveEaseInOut]) {
        self.dataSource.apply(snapshot, animatingDifferences: true, completion: finish)
        updateLayout()
      }
    } else if folding {
      UIView.transition(with: collection, duration: 0.12, options: [.transitionCrossDissolve]) {
        self.dataSource.apply(snapshot, animatingDifferences: false)
        updateLayout()
      } completion: { _ in finish() }
    } else {
      dataSource.apply(snapshot, animatingDifferences: false) {
        updateLayout()
        finish()
      }
    }
  }

  private func updateWorkDurationTimer(rows: [ChatRow]) {
    let needsTimer = window != nil && ChatWorkDuration.needsTimer(rows)
    guard needsTimer else {
      workDurationTimer?.invalidate()
      workDurationTimer = nil
      return
    }
    guard workDurationTimer == nil else { return }
    let timer = Timer(timeInterval: 1, repeats: true) { [weak self] _ in
      self?.applyRows()
    }
    workDurationTimer = timer
    RunLoop.main.add(timer, forMode: .common)
  }
}

private func textColor(for row: ChatRow) -> UIColor {
  if row.attention { return .systemOrange }
  if row.kind == "changes" || (row.kind == "summary" && row.running) { return .systemBlue }
  if row.kind == "user" { return .label }
  return .secondaryLabel
}
