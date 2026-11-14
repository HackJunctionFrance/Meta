#!/usr/bin/env python3
"""Materialize a pinned official CameraAccess sample with a narrow, reviewable FirstFive overlay."""

import argparse
import pathlib
import plistlib
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
META_REV = "bbae597cd1c748cd29b9375a1624a8d75b1c9e14"
LIVEKIT_REV = "1693a9e2edfca5a94fbb89d5dbfe3390e026b30b"
parser = argparse.ArgumentParser()
parser.add_argument("--sdk-source", type=pathlib.Path)
parser.add_argument("--destination", type=pathlib.Path)
args = parser.parse_args()
dest = args.destination or ROOT / "CameraAccess"
if dest.exists():
    raise SystemExit("ios/CameraAccess already exists; preserve your changes before regenerating.")
with tempfile.TemporaryDirectory() as temp:
    source = args.sdk_source
    if not source:
        source = pathlib.Path(temp) / "sdk"
        subprocess.run(
            [
                "git",
                "clone",
                "https://github.com/facebook/meta-wearables-dat-ios.git",
                str(source),
            ],
            check=True,
        )
        subprocess.run(["git", "-C", str(source), "checkout", META_REV], check=True)
    rev = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    if rev != META_REV:
        raise SystemExit("SDK source revision differs from the reviewed version")
    shutil.copytree(source / "samples/CameraAccess", dest)
    shutil.copy2(source / "LICENSE", dest / "META-LICENSE")

app = dest / "CameraAccess"
for f in (ROOT / "Sources").glob("*.swift"):
    shutil.copy2(f, app / f.name)


def patch(path, old, new):
    text = path.read_text()
    if text.count(old) != 1:
        raise RuntimeError(f"Expected one patch anchor in {path}: {old}")
    path.write_text(text.replace(old, new))


patch(
    app / "CameraAccessApp.swift",
    "MainAppView(wearables: Wearables.shared, viewModel: wearablesViewModel)",
    "MainAppView(wearables: Wearables.shared, viewModel: wearablesViewModel)\n        .safeAreaInset(edge: .bottom) { FirstFivePanel() }",
)
vm = app / "ViewModels/CameraViewModel.swift"
patch(
    vm,
    "    guard camera == nil else { return }\n\n    do {",
    "    guard camera == nil else { return }\n\n    do {\n      try FirstFiveClient.shared.prepareAudio()",
)
patch(
    vm,
    "          self.currentVideoFrame = image",
    "          self.currentVideoFrame = image\n          FirstFiveClient.shared.frame(image)",
)
patch(
    vm,
    "    sessionState = state\n",
    '    sessionState = state\n    FirstFiveClient.shared.deviceStatus(connected: state == .started, stream: "stopped")\n',
)
patch(
    vm,
    "    streamState = state\n",
    '    streamState = state\n    FirstFiveClient.shared.deviceStatus(connected: hasSession, stream: state == .streaming ? "streaming" : "stopped")\n',
)
# Expose the SDK navigation action for required DAT app updates on glasses.
patch(
    app / "Views/CameraView.swift",
    '          CustomButton(\n            title: "Disconnect",\n            style: .destructive,\n            isDisabled: wearablesVM.registrationState != .registered\n          ) {\n            wearablesVM.disconnectGlasses()\n            withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) { showSettingsMenu = false }\n          }\n          .frame(width: 120)',
    '          VStack(spacing: 8) {\n            CustomButton(\n              title: "Update app on glasses",\n              style: .primary,\n              isDisabled: isLaunchingUpdate || wearablesVM.registrationState != .registered\n            ) {\n              showSettingsMenu = false\n              isLaunchingUpdate = true\n              Task {\n                await wearablesVM.openDATGlassesAppUpdate()\n                isLaunchingUpdate = false\n              }\n            }\n            .accessibilityIdentifier("update_glasses_app_button")\n            CustomButton(\n              title: "Disconnect",\n              style: .destructive,\n              isDisabled: wearablesVM.registrationState != .registered\n            ) {\n              wearablesVM.disconnectGlasses()\n              withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) { showSettingsMenu = false }\n            }\n          }\n          .frame(width: 250)',
)
plist = app / "Info.plist"
info = plistlib.loads(plist.read_bytes())
info["NSMicrophoneUsageDescription"] = (
    "Speak to the simulated dispatcher and answer the fixed guide."
)
info["NSSpeechRecognitionUsageDescription"] = (
    "Recognize emergency, yes and no during a consenting demo."
)
info["NSLocalNetworkUsageDescription"] = (
    "Connect to the FirstFive server and Meta glasses on your local network."
)
info["NSAppTransportSecurity"] = {"NSAllowsLocalNetworking": True}
info["UIBackgroundModes"] = list(
    dict.fromkeys(info.get("UIBackgroundModes", []) + ["external-accessory"])
)
plist.write_bytes(plistlib.dumps(info))
pbx = dest / "CameraAccess.xcodeproj/project.pbxproj"
text = pbx.read_text()
# Existing sample has explicit source lists, so register both overlay files.
for index, name in enumerate(["FirstFiveClient.swift", "FirstFivePanel.swift"]):
    ref = f"F1F1000000000000000000{index:02X}"
    build = f"F1F2000000000000000000{index:02X}"
    text = text.replace(
        "/* End PBXFileReference section */",
        f'{ref} = {{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = {name}; sourceTree = "<group>"; }};\n/* End PBXFileReference section */',
    )
    text = text.replace(
        "/* End PBXBuildFile section */",
        f"{build} = {{isa = PBXBuildFile; fileRef = {ref}; }};\n/* End PBXBuildFile section */",
    )
    text = text.replace(
        "8FD96B792E6F0A9800F56AB1 /* CameraAccessApp.swift */,",
        f"8FD96B792E6F0A9800F56AB1 /* CameraAccessApp.swift */,\n{ref},",
    )
    text = text.replace(
        "8FD96B7F2E6F0A9800F56AB1 /* CameraAccessApp.swift in Sources */,",
        f"8FD96B7F2E6F0A9800F56AB1 /* CameraAccessApp.swift in Sources */,\n{build},",
    )
text = text.replace(
    "/* End XCRemoteSwiftPackageReference section */",
    f'F1F300000000000000000001 = {{isa = XCRemoteSwiftPackageReference; repositoryURL = "https://github.com/livekit/client-sdk-swift"; requirement = {{kind = revision; revision = {LIVEKIT_REV}; }}; }};\n/* End XCRemoteSwiftPackageReference section */',
)
text = text.replace("packageReferences = (", "packageReferences = (\nF1F300000000000000000001,")
text = text.replace(
    "/* End XCSwiftPackageProductDependency section */",
    "F1F300000000000000000002 = {isa = XCSwiftPackageProductDependency; package = F1F300000000000000000001; productName = LiveKit; };\n/* End XCSwiftPackageProductDependency section */",
)
text = text.replace(
    "/* End PBXBuildFile section */",
    "F1F300000000000000000003 = {isa = PBXBuildFile; productRef = F1F300000000000000000002; };\n/* End PBXBuildFile section */",
)
text = text.replace(
    "8FD96B952E6F0F7D00F56AB1 /* MWDATCore in Frameworks */,",
    "8FD96B952E6F0F7D00F56AB1 /* MWDATCore in Frameworks */,\nF1F300000000000000000003,",
)
pbx.write_text(text)
print("Prepared", dest / "CameraAccess.xcodeproj")
print(
    "Open in Xcode 26.4+, select signing team, then build. This script does not validate an iOS build."
)
