import SwiftUI

struct FirstFivePanel: View {
  @State private var client = FirstFiveClient.shared
  var body: some View {
    DisclosureGroup("FirstFive · \(client.status) · \(client.phase)") {
      VStack(alignment: .leading, spacing: 8) {
        Text("SIMULATION · no real emergency call").font(.caption).foregroundStyle(.orange)
        TextField("Server URL", text: $client.serverURL).textInputAutocapitalization(.never).autocorrectionDisabled()
        SecureField("Access key (optional)", text: $client.accessKey)
        HStack {
          Button("Connect") { client.connect() }
          Button("Enable voice") { client.enableListening() }
          Button("Reset") { client.send(["type": "reset"]) }
          Button("Retry call") { Task { await client.joinVoice() } }
        }
        HStack {
          Button("EMERGENCY") { client.emergency() }.tint(.red)
          Button("Yes") { client.answer("yes") }
          Button("No") { client.answer("no") }
        }.buttonStyle(.borderedProminent)
        Text(client.caption).font(.headline)
        Text(client.callStatus).font(.caption)
        if !client.audioRoute.isEmpty { Text(client.audioRoute).font(.caption) }
        HStack {
          Button("Audio → glasses") { client.useGlasses() }
          Button("Audio → iPhone speaker") { client.useSpeaker() }
        }.font(.caption)
        Text(client.speechStatus).font(.caption)
        if !client.lastHeard.isEmpty { Text("Heard: \(client.lastHeard)").font(.caption) }
        if !client.failure.isEmpty { Text(client.failure).font(.caption).foregroundStyle(.orange) }
        Text("Connect, then enable voice before starting CameraAccess Preview.").font(.caption)
      }.textFieldStyle(.roundedBorder)
    }.padding().background(.regularMaterial).foregroundStyle(.primary)
  }
}
