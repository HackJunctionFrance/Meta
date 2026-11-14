import AVFoundation
import AudioToolbox
import Foundation
import LiveKit
import Observation
import Speech
import SwiftUI

/// Transport and speech layer attached to the official CameraAccess sample.
/// The server owns the fixed guide state, shared by iPhone and browser simulator.
@MainActor @Observable
final class FirstFiveClient: NSObject, AVSpeechSynthesizerDelegate {
  static let shared = FirstFiveClient()
  var serverURL = UserDefaults.standard.string(forKey: "FirstFive.server") ?? "http://127.0.0.1:8000"
  var accessKey = "" // memory only; never persist secrets in UserDefaults
  var status = "Disconnected"
  var phase = "idle"
  var step = "responsive"
  var caption = ""
  var failure = ""
  var voiceCommands = false
  var speechStatus = "Voice disabled"
  var lastHeard = ""
  var callStatus = "Call: off"
  var audioRoute = ""
  private var requestingVoicePermission = false
  private var socket: URLSessionWebSocketTask?
  private var connectionTask: Task<Void, Never>?
  private var room: Room?
  private var joining = false
  private var sessionID: String?
  private var voiceGeneration = 0
  private var connectionGeneration = 0
  private var speechGeneration = 0
  private var frameBusy = false
  private var lastFrame = Date.distantPast
  private let synthesizer = AVSpeechSynthesizer()
  // Recreated for each listening session: a cached engine keeps the old mic format
  // after a switch to the glasses (16 kHz Bluetooth) and installTap then crashes.
  @ObservationIgnored private var engine = AVAudioEngine()
  private var speechTask: SFSpeechRecognitionTask?
  private var request: SFSpeechAudioBufferRecognitionRequest?
  private var microphoneTapped = false
  private var speechRestart: Task<Void, Never>?
  private var beatTask: Task<Void, Never>?
  private var reminderTask: Task<Void, Never>?
  private var callMonitor: Task<Void, Never>?
  @ObservationIgnored private var routeObserver: NSObjectProtocol?
  private let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))

  override init() {
    super.init(); synthesizer.delegate = self
    // Delivered on the main queue; shows where iOS actually sends call audio.
    routeObserver = NotificationCenter.default.addObserver(
      forName: AVAudioSession.routeChangeNotification, object: nil, queue: .main
    ) { _ in Task { @MainActor in FirstFiveClient.shared.refreshRoute() } }
  }

  /// Displays the microphone and speaker iOS is using right now.
  func refreshRoute() {
    let route = AVAudioSession.sharedInstance().currentRoute
    let mic = route.inputs.map(\.portName).joined(separator: ", ")
    let sound = route.outputs.map(\.portName).joined(separator: ", ")
    audioRoute = "Mic: \(mic.isEmpty ? "none" : mic) · Sound: \(sound.isEmpty ? "none" : sound)"
  }

  /// Sends call audio to the glasses (Bluetooth HFP) for both microphone and sound.
  func useGlasses() {
    let audio = AVAudioSession.sharedInstance()
    do {
      try audio.overrideOutputAudioPort(.none)
      if let glasses = audio.availableInputs?.first(where: { $0.portType == .bluetoothHFP }) {
        try audio.setPreferredInput(glasses)
        failure = ""
      } else {
        failure = "Glasses audio not offered by iOS. During the call, check iPhone Bluetooth: glasses connected."
      }
    } catch { failure = "Audio route: \(error.localizedDescription)" }
    refreshRoute()
  }

  /// Fallback: iPhone loudspeaker, audible even when glasses audio is unavailable.
  func useSpeaker() {
    do { try AVAudioSession.sharedInstance().overrideOutputAudioPort(.speaker) }
    catch { failure = "Audio route: \(error.localizedDescription)" }
    refreshRoute()
  }

  private func describeCall(_ call: Room) -> String {
    let state = call.connectionState
    var parts = ["Call: " + (state == .connected ? "connected" : state == .reconnecting ? "reconnecting" : "connecting")]
    if let dispatcher = call.remoteParticipants.values.first {
      let receiving = dispatcher.audioTracks.contains { $0.isSubscribed }
      parts.append("Operator: " + (!receiving ? "joined, no audio yet" : dispatcher.isSpeaking ? "speaking" : "silent"))
    } else {
      parts.append("Operator: not in call")
    }
    let me = call.localParticipant
    parts.append("My mic: " + (!me.isMicrophoneEnabled() ? "off" : me.isSpeaking ? "speaking" : "on"))
    return parts.joined(separator: " · ")
  }

  func prepareAudio() throws {
    let audio = AVAudioSession.sharedInstance()
    try audio.setCategory(.playAndRecord, mode: .voiceChat, options: [.allowBluetooth])
    try audio.setActive(true)
    if let bluetooth = audio.availableInputs?.first(where: { $0.portType == .bluetoothHFP }) {
      try audio.setPreferredInput(bluetooth)
    }
    UIApplication.shared.isIdleTimerDisabled = true
  }

  func connect() {
    guard var url = URLComponents(string: serverURL), ["http", "https"].contains(url.scheme ?? ""), url.host != nil else {
      failure = "Enter an http:// or https:// server address"; return
    }
    UserDefaults.standard.set(serverURL, forKey: "FirstFive.server")
    connectionGeneration += 1
    let generation = connectionGeneration
    stopGuide(); stopVoice()
    connectionTask?.cancel(); socket?.cancel(with: .goingAway, reason: nil)
    url.scheme = url.scheme == "https" ? "wss" : "ws"; url.path = "/ws/app"; url.query = nil
    guard let endpoint = url.url else { return }
    connectionTask = Task { [weak self] in
      while !Task.isCancelled {
        guard let self, generation == self.connectionGeneration else { return }
        var req = URLRequest(url: endpoint)
        req.setValue(self.accessKey, forHTTPHeaderField: "X-FirstFive-Key")
        let task = URLSession.shared.webSocketTask(with: req); self.socket = task; task.resume()
        do {
          self.status = "Connecting…"
          while !Task.isCancelled {
            let message = try await task.receive()
            guard !Task.isCancelled, generation == self.connectionGeneration else { return }
            if case let .string(text) = message, let data = text.data(using: .utf8),
              let object = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
              self.status = "Connected"; self.receive(object)
            }
          }
        } catch {
          guard !Task.isCancelled, generation == self.connectionGeneration else { return }
          self.status = "Reconnecting…"; self.stopGuide(); self.stopVoice()
        }
        try? await Task.sleep(for: .seconds(2))
      }
    }
  }

  func send(_ payload: [String: Any]) {
    guard status == "Connected", let socket else { failure = "Connect to the server first"; return }
    var message = payload; message["ts"] = Date().timeIntervalSince1970 * 1000
    guard let data = try? JSONSerialization.data(withJSONObject: message), let text = String(data: data, encoding: .utf8) else { return }
    Task { do { try await socket.send(.string(text)) } catch { failure = "Send failed; check server connection" } }
  }

  func emergency() { send(["type": "alert", "trigger": "button"]) }
  func answer(_ value: String) { send(["type": "answer", "step_id": step, "value": value, "heard": value]) }

  /// Called from the sample's decoded frame callback. Never stores video outside an active alert.
  func frame(_ image: UIImage) {
    guard ["ai_guide", "connected"].contains(phase), status == "Connected",
      !frameBusy, Date().timeIntervalSince(lastFrame) >= 1.0 / 3.0, let socket else { return }
    lastFrame = Date(); frameBusy = true
    let capturedSessionID = sessionID
    let generation = connectionGeneration
    Task {
      // Resize and JPEG compression are isolated from the main actor.
      let data = await Task.detached(priority: .utility) {
        let ratio = min(1, 960 / image.size.width)
        let size = CGSize(width: image.size.width * ratio, height: image.size.height * ratio)
        let resized = UIGraphicsImageRenderer(size: size).image { _ in image.draw(in: CGRect(origin: .zero, size: size)) }
        return resized.jpegData(compressionQuality: 0.5)
      }.value
      defer { frameBusy = false }
      if let data, capturedSessionID == sessionID, generation == connectionGeneration,
        ["ai_guide", "connected"].contains(phase) { try? await socket.send(.data(data)) }
    }
  }

  func deviceStatus(connected: Bool, stream: String) {
    guard ["ai_guide", "connected"].contains(phase) else { return }
    send(["type":"status", "glasses":connected ? "connected" : "disconnected", "stream":stream])
  }

  private func receive(_ message: [String: Any]) {
    switch message["type"] as? String {
    case "state":
      let nextSessionID = message["session_id"] as? String
      if nextSessionID != sessionID { stopGuide(); stopVoice() }
      sessionID = nextSessionID
      phase = message["phase"] as? String ?? "idle"
      step = message["step"] as? String ?? "responsive"
      if phase != "ai_guide" { stopGuide() }
      if phase == "connected" { Task { await joinVoice() } }
      if phase == "idle" || phase == "ended" { stopVoice() }
    case "caller_heard":
      caption = message["text"] as? String ?? ""
      if message["source"] as? String == "ai_guide", phase == "ai_guide" {
        speak(caption)
        if message["step_id"] as? String == "cpr" { metronome() }
      }
    case "pickup": stopGuide(); Task { await joinVoice() }
    case "end": stopGuide(); stopVoice()
    case "override": if message["action"] as? String == "reset" { stopGuide(); stopVoice() }
    case "error": failure = message["message"] as? String ?? "Server error"
    default: break
    }
  }

  func joinVoice() async {
    guard phase == "connected", status == "Connected", room == nil, !joining, let sessionID else { return }
    joining = true
    let generation = voiceGeneration
    defer { joining = false }
    stopGuide()
    do {
      try prepareAudio()
      guard var components = URLComponents(string: serverURL) else { return }
      components.path = "/livekit/token"
      components.queryItems = [URLQueryItem(name: "role", value: "caller")]
      guard let url = components.url else { return }
      var req = URLRequest(url: url); req.timeoutInterval = 10
      req.setValue(accessKey, forHTTPHeaderField: "X-FirstFive-Key")
      let (data,response) = try await URLSession.shared.data(for: req)
      guard generation == voiceGeneration, sessionID == self.sessionID, phase == "connected" else { return }
      guard (response as? HTTPURLResponse)?.statusCode == 200,
        let token = try JSONSerialization.jsonObject(with: data) as? [String: String],
        let endpoint = token["url"], let jwt = token["token"] else {
        failure = "LiveKit unavailable. Dispatcher captions remain visible."; return
      }
      guard token["session_id"] == sessionID else { return }
      let call = Room(); room = call
      try await call.connect(url: endpoint, token: jwt)
      guard generation == voiceGeneration, sessionID == self.sessionID, phase == "connected" else {
        await call.disconnect(); return
      }
      try await call.localParticipant.setMicrophone(enabled: true)
      // LiveKit reconfigures the audio session when the mic starts: route to the glasses again.
      useGlasses()
      callMonitor?.cancel()
      callMonitor = Task { [weak self] in
        while !Task.isCancelled {
          guard let self, let active = self.room else { return }
          self.callStatus = self.describeCall(active)
          try? await Task.sleep(for: .seconds(1))
        }
      }
    } catch {
      if generation == voiceGeneration {
        failure = "Voice connection failed: \(error.localizedDescription)"
        stopVoice()
      }
    }
  }

  private func stopVoice() {
    voiceGeneration += 1
    callMonitor?.cancel(); callMonitor = nil; callStatus = "Call: off"
    if let call = room { room = nil; Task { await call.disconnect() } }
  }

  private func speak(_ text: String) {
    stopListening(); synthesizer.stopSpeaking(at: .immediate)
    let utterance = AVSpeechUtterance(string: text); utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
    synthesizer.speak(utterance)
  }
  nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
    Task { @MainActor in if self.voiceCommands && self.phase == "ai_guide" { self.startListening() } }
  }
  func enableListening() {
    guard !requestingVoicePermission else { return }
    requestingVoicePermission = true
    speechStatus = "Requesting voice permissions…"
    Task { @MainActor in
      defer { requestingVoicePermission = false }
      guard await Self.requestSpeechPermission() else {
        voiceCommands = false; stopListening()
        failure = "Speech permission denied. Use Yes / No buttons."
        return
      }
      guard await Self.requestMicrophonePermission() else {
        voiceCommands = false; stopListening()
        failure = "Microphone permission denied. Use Yes / No buttons."
        return
      }
      voiceCommands = true
      failure = ""
      startListening()
    }
  }

  // Apple invokes these legacy callbacks on its own queues. Construct them in
  // explicitly nonisolated functions: a MainActor-inherited callback traps under
  // Swift 6 before even reaching a Task { @MainActor ... } in its body.
  private nonisolated static func requestSpeechPermission() async -> Bool {
    await withCheckedContinuation { continuation in
      SFSpeechRecognizer.requestAuthorization { result in
        continuation.resume(returning: result == .authorized)
      }
    }
  }

  private nonisolated static func requestMicrophonePermission() async -> Bool {
    await withCheckedContinuation { continuation in
      AVAudioApplication.requestRecordPermission { allowed in
        continuation.resume(returning: allowed)
      }
    }
  }

  private nonisolated static func audioTap(
    for request: SFSpeechAudioBufferRecognitionRequest
  ) -> AVAudioNodeTapBlock {
    // Runs on the audio queue. Never access UI or MainActor state here.
    { buffer, _ in request.append(buffer) }
  }

  private nonisolated static func recognize(
    using recognizer: SFSpeechRecognizer,
    request: SFSpeechAudioBufferRecognitionRequest,
    onResult: @escaping @Sendable (String?, Bool, String?) -> Void
  ) -> SFSpeechRecognitionTask {
    recognizer.recognitionTask(with: request) { result, error in
      // Only immutable Sendable values cross back to the main actor.
      onResult(result?.bestTranscription.formattedString, result?.isFinal ?? false,
               error?.localizedDescription)
    }
  }
  private func startListening() {
    stopListening()
    guard voiceCommands, ["idle", "ai_guide"].contains(phase), !synthesizer.isSpeaking else { return }
    do {
      try prepareAudio()
      let request = SFSpeechAudioBufferRecognitionRequest(); request.shouldReportPartialResults = false; self.request = request
      guard let recognizer, recognizer.isAvailable else {
        failure = "Speech recognition unavailable. Use Yes / No buttons."; stopListening(); return
      }
      let generation = speechGeneration
      engine = AVAudioEngine()
      let input = engine.inputNode
      let format = input.outputFormat(forBus: 0)
      let hardware = input.inputFormat(forBus: 0)
      guard format.sampleRate > 0, format.channelCount > 0, format.sampleRate == hardware.sampleRate else {
        failure = "Microphone not ready. Check Bluetooth and retry Enable voice."; stopListening(); return
      }
      input.installTap(onBus: 0, bufferSize: 1024, format: format, block: Self.audioTap(for: request))
      microphoneTapped = true; engine.prepare(); try engine.start()
      speechStatus = "Listening — say Yes or No after the question"
      speechTask = Self.recognize(using: recognizer, request: request) { @Sendable [weak self] text, isFinal, error in
        Task { @MainActor in
          guard let self, generation == self.speechGeneration else { return }
          if let text, isFinal {
            self.lastHeard = text
            let words = text.lowercased().trimmingCharacters(in: .punctuationCharacters.union(.whitespaces))
            if words == "emergency", self.phase == "idle" { self.emergency() }
            else if ["yes","yeah","yep","no","nope"].contains(words), self.phase == "ai_guide" {
              self.answer(["yes","yeah","yep"].contains(words) ? "yes" : "no")
            }
          }
          if let error { self.failure = "Speech recognition: \(error)" }
          if isFinal || error != nil {
            self.stopListening()
            self.speechRestart = Task { try? await Task.sleep(for: .seconds(1)); if !Task.isCancelled { self.startListening() } }
          }
        }
      }
      speechRestart = Task { try? await Task.sleep(for: .seconds(50)); if !Task.isCancelled { startListening() } }
    } catch { failure = "Speech unavailable: \(error.localizedDescription)"; stopListening() }
  }
  private func stopListening() {
    // Cancellation callbacks from an older recognizer must not stop its replacement.
    speechGeneration += 1
    speechRestart?.cancel(); speechRestart = nil
    speechTask?.cancel(); speechTask = nil
    engine.stop(); if microphoneTapped { engine.inputNode.removeTap(onBus: 0); microphoneTapped = false }
    request?.endAudio(); request = nil
    speechStatus = voiceCommands ? "Voice enabled — listening paused" : "Voice disabled"
  }
  private func metronome() {
    guard beatTask == nil else { return }
    beatTask = Task { while !Task.isCancelled { AudioServicesPlaySystemSound(1104); try? await Task.sleep(for: .milliseconds(545)) } }
    reminderTask = Task { while !Task.isCancelled { try? await Task.sleep(for: .seconds(20)); if !Task.isCancelled { speak("Keep pushing hard and fast, follow the beat.") } } }
  }
  private func stopGuide() {
    beatTask?.cancel(); beatTask = nil; reminderTask?.cancel(); reminderTask = nil
    stopListening(); synthesizer.stopSpeaking(at: .immediate)
  }
}
