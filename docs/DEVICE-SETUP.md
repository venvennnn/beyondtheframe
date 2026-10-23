# Fire OS, Android TV, and Vega validation

## Actual status

This Windows workstation initially had no JDK, Android SDK, ADB, emulator or Vega SDK. Build-only JDK/SDK tools were downloaded locally. A signed APK was built and its v2/v3 signatures verified. No actual Fire TV, Android TV emulator, or official Vega Virtual Device was run. The browser is a preview, and does not complete the Fire TV demonstration requirement.

The application deliberately targets **Fire OS** with an Android activity and WebView. Amazon documents HTML5 hybrid and WebView application paths. The self-contained Android host lets the full-screen sports interface and media run locally without a server or cloud credentials. It uses Java for the thin platform host rather than adding Kotlin/Media3 build dependencies; playback is HTML5 video. Fire TV WebView compatibility and hardware media playback still need testing.

## Recommended without hardware: Amazon cloud-hosted Fire TV virtual devices

Amazon now offers an official browser-accessible Fire TV virtual device farm through Appstore Quality Central. This is separate from the local Vega Virtual Device, and supports sideloading Fire OS APKs. It is the first option to try on this Windows workstation. Availability and device choices must be checked in the signed-in console; no cloud session has been run for this project yet.

1. Sign in to the [Amazon Developer Console](https://developer.amazon.com/dashboard).
2. Select Tools & Services → Appstore Quality Central.
3. On the **Live Device Interaction — Virtual Devices** card select Get Started. Use that specific card, because the physical-device farm is a separate offering with restricted access.
4. Review the Developer Agreement and Device Handling Guidelines yourself before accepting. Observe any confidentiality restrictions for prototypes and recordings.
5. Choose an available compatible Fire OS device, select Use, and sign into the device if prompted. This package requires Android API 26 or later; select a Fire OS 7-or-newer environment with a modern WebView. Do not choose a Vega-only target.
6. On Dashboard → App Upload, upload `artifacts/Beyond-The-Frame-debug.apk`, then install/launch Beyond The Frame through the session controls.
7. If necessary, use Dashboard → Shell to launch with `am start -n com.beyondtheframe.tv/.MainActivity`. The web shell is already on the device; do not prefix that command with `adb shell` unless using a separate local ADB connection.
8. Use the Remote tab's D-pad, Select, Back and Play/Pause controls. Test original playback, Read this play, Field view, and the full detective story before Check this statement. The videos and authored evidence are bundled; no local HTTP server is needed.
9. Download diagnostic logs before closing the session. Save permitted screenshots/recordings through Screen, subject to the agreement.

Official instructions: [Live Device Interaction — Virtual Devices](https://developer.amazon.com/docs/app-testing/live-device-interaction-virtual.html). This cloud testing route was omitted from the initial setup guide; the Windows limitation below applies specifically to the local Vega SDK/VVD.

## Install on a Fire OS TV

1. Install Android Platform Tools from [Android's official SDK Platform Tools page](https://developer.android.com/tools/releases/platform-tools). Add its directory to the current terminal PATH or use the full executable path.
2. On the Fire TV open Settings → My Fire TV (or Device & Software) → About. If Developer Options is hidden, select the device name seven times. Return to Developer Options and enable ADB Debugging. Put the TV and workstation on the same network; find the TV IP in About → Network.
3. Run from the repository root, substituting the real TV address:

```powershell
adb connect 192.168.1.100:5555
adb devices
adb install -r artifacts/Beyond-The-Frame-debug.apk
adb shell am start -n com.beyondtheframe.tv/.MainActivity
```

Approve the debugging prompt on the TV. There are no API keys or backend URLs to configure.

Test every primary action with the physical remote: D-pad, Select, Back, Play/Pause, seeking, playback, captions, the sports decision and follow experiences, and background/foreground transitions. File importing additionally depends on a document picker being installed on the TV; the bundled demos do not require it.

Official references: [connect with ADB](https://developer.amazon.com/docs/fire-tv/connecting-adb-to-device.html), [install and run](https://developer.amazon.com/docs/fire-tv/installing-and-running-your-app.html), [Fire TV FAQs](https://developer.amazon.com/docs/fire-tv/faq-general.html), [hybrid apps](https://developer.amazon.com/docs/fire-tv/hybrid-apps.html).

## Optional Android TV emulator on Windows

This provides useful Android compatibility testing, **not official Fire TV verification**.

1. Install Android Studio from [Android Developers](https://developer.android.com/studio), including SDK Platform Tools and Android Emulator.
2. Enable hardware virtualization in firmware if necessary, then enable Windows Hypervisor Platform in Windows Features and restart if prompted.
3. Open Android Studio → Device Manager → Create Virtual Device → TV. Choose a 1080p Android TV profile and an x86_64 Android TV system image API 30 or later. Finish and start the AVD.
4. Use `adb devices`, then `adb -s emulator-5554 install -r artifacts/Beyond-The-Frame-debug.apk` (replace the serial with the actual result).
5. Run `adb -s emulator-5554 shell am start -n com.beyondtheframe.tv/.MainActivity`. Use the Extended Controls remote/D-pad or ADB key events `19` up, `20` down, `21` left, `22` right, `23` select, `4` back, `85` play/pause.

Record AVD profile, system-image revision, Android API, WebView version and actual observations. An AVD is not an Amazon Fire OS system image and cannot validate Amazon-specific behavior.

## Official Vega Virtual Device

Amazon's [current Vega setup guide](https://developer.amazon.com/apps-and-games/blogs/2026/07/guide-to-building-for-fire-tv-on-vega-os) explicitly requires **Mac or Linux**; Windows and WSL are unsupported. Its official VVD runs Vega applications. **This Fire OS APK cannot be installed into VVD. A separate Vega React Native port is required if VVD is the mandatory demonstration target.**

To establish the supported tooling on a Mac/Linux machine, follow the linked official prerequisites, install VS Code, then run the guide's installer:

```bash
curl -fsSL https://sdk-installer.vega.labcollab.net/get_vvm.sh | bash
source ~/vega/env
vega --version
```

In VS Code open the Vega Studio extension; under Devices launch Vega Virtual Device. Build a Vega project through Vega Studio, install and launch it on VVD. Do not rename or sideload the APK as a Vega package. Porting the player, local assets and focus interactions to Vega, then demonstrating both experiences inside VVD, is outstanding work.

The Fire OS route can be tested using Amazon's cloud-hosted Fire TV virtual devices or a compatible physical Fire TV. No cloud session has been run yet. No claim of Fire TV verification is made for the local browser preview or an Android TV AVD.
