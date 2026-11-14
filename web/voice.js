export class VoiceCall {
  constructor({ onCaption, onError, getElapsed, onStatus }) {
    Object.assign(this, { onCaption, onError, getElapsed, onStatus });
    this.recorders = new Map();
    this.audioElements = [];
    this.generation = 0;
    this.activeRecorders = new Map();
  }
  async join(role) {
    if (this.room) {
      for (const el of this.audioElements) await el.play();
      return;
    }
    if (this.joining) return;
    this.joining = true;
    const generation = this.generation;
    try {
      if (!window.isSecureContext)
        throw Error("Voice needs HTTPS (or localhost).");
      if (!window.LivekitClient)
        throw Error("LiveKit browser library unavailable.");
      const response = await fetch(`/livekit/token?role=${role}`);
      const data = await response.json();
      if (!response.ok) throw Error(data.detail);
      if (generation !== this.generation) return;
      const L = window.LivekitClient;
      const room = new L.Room();
      this.room = room;
      this.sid = data.session_id;
      room.on(
        L.RoomEvent.TrackSubscribed,
        (track, publication, participant) => {
          if (track.kind !== L.Track.Kind.Audio) return;
          const el = track.attach();
          el.autoplay = true;
          document.body.append(el);
          this.audioElements.push(el);
          el.play().catch(() =>
            this.onError("Click Reconnect audio to allow audio playback."),
          );
          if (role === "dispatcher" && participant.identity === "caller")
            this.record("caller", track.mediaStreamTrack);
        },
      );
      room.on(L.RoomEvent.TrackUnsubscribed, (track) => {
        for (const item of this.activeRecorders.values()) {
          if (item.track === track.mediaStreamTrack) this.stopRecording(item);
        }
        track.detach().forEach((el) => el.remove());
        this.audioElements = this.audioElements.filter((el) => el.isConnected);
      });
      room.on(L.RoomEvent.Disconnected, () => {
        if (this.room !== room) return;
        this.disconnect();
        this.onError(
          "Voice disconnected. Recordings retained; press Reconnect audio.",
        );
      });
      try {
        await room.connect(data.url, data.token);
        if (generation !== this.generation) {
          await room.disconnect();
          return;
        }
        await room.localParticipant.setMicrophoneEnabled(true);
        clearInterval(this.statusTimer);
        this.statusTimer = setInterval(() => this.reportStatus(), 500);
        if (role === "dispatcher") {
          const pub = room.localParticipant.getTrackPublication(
            L.Track.Source.Microphone,
          );
          if (pub?.track) this.record("dispatcher", pub.track.mediaStreamTrack);
          this.captions();
        }
      } catch (e) {
        await this.disconnect();
        throw e;
      }
    } finally {
      this.joining = false;
    }
  }
  record(speaker, track) {
    const previous = this.activeRecorders.get(speaker);
    if (previous?.track === track && previous.recorder.state !== "inactive")
      return;
    if (previous) this.stopRecording(previous);
    const segment = [...this.recorders.values()].filter(
      (item) => item.speaker === speaker,
    ).length;
    if (segment >= 32) {
      this.onError("Recording segment limit reached. End this rehearsal.");
      return;
    }
    if (!window.MediaRecorder) {
      this.onError("Recording not supported by this browser.");
      return;
    }
    const mime = ["audio/webm;codecs=opus", "audio/mp4"].find((x) =>
      MediaRecorder.isTypeSupported(x),
    );
    const recorder = new MediaRecorder(
      new MediaStream([track]),
      mime ? { mimeType: mime } : {},
    );
    const item = {
      recorder,
      chunks: [],
      offset: this.getElapsed(),
      bytes: 0,
      speaker,
      segment,
      track,
      uploaded: false,
      duration: null,
    };
    item.stopped = new Promise((resolve) =>
      recorder.addEventListener(
        "stop",
        () => {
          item.duration ??= Math.max(0, this.getElapsed() - item.offset);
          resolve();
        },
        { once: true },
      ),
    );
    track.addEventListener("ended", () => this.stopRecording(item), {
      once: true,
    });
    recorder.ondataavailable = (e) => {
      if (e.data.size) {
        item.bytes += e.data.size;
        const total = [...this.recorders.values()]
          .filter((r) => r.speaker === speaker)
          .reduce((n, r) => n + r.bytes, 0);
        if (total < 24 * 1024 * 1024) item.chunks.push(e.data);
        else {
          this.onError("Recording limit reached (24 MB).");
          this.stopRecording(item);
        }
      }
    };
    this.recorders.set(`${speaker}-${segment}`, item);
    this.activeRecorders.set(speaker, item);
    recorder.start(1000);
  }
  stopRecording(item) {
    if (item.recorder.state !== "inactive") {
      item.duration = Math.max(0, this.getElapsed() - item.offset);
      item.recorder.stop();
    }
  }
  captions() {
    const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Speech) {
      this.onError("Live captions unavailable; use manual captions.");
      return;
    }
    this.captioning = true;
    const rec = new Speech();
    this.rec = rec;
    rec.lang = "en-US";
    rec.continuous = true;
    rec.interimResults = false;
    rec.onresult = (e) => {
      for (let i = e.resultIndex; i < e.results.length; i++)
        if (e.results[i].isFinal) this.onCaption(e.results[i][0].transcript);
    };
    rec.onerror = (e) => {
      if (["not-allowed", "service-not-allowed"].includes(e.error))
        this.captioning = false;
      this.onError(`Caption recognition: ${e.error}`);
    };
    rec.onend = () => {
      if (this.captioning)
        setTimeout(() => {
          if (this.captioning)
            try {
              rec.start();
            } catch {}
        }, 500);
    };
    rec.start();
  }
  async finish() {
    this.captioning = false;
    this.rec?.stop();
    const recordings = [...this.recorders.values()];
    recordings.forEach((item) => this.stopRecording(item));
    await Promise.all(recordings.map((item) => item.stopped));
    const failures = [];
    for (const item of recordings) {
      const speaker = item.speaker;
      if (item.uploaded) continue;
      const blob = new Blob(item.chunks, { type: item.recorder.mimeType });
      if (!blob.size) continue;
      try {
        const r = await fetch(
          `/session/${this.sid}/audio?track=${speaker}&offset=${item.offset}&segment=${item.segment}&duration=${item.duration}`,
          {
            method: "POST",
            headers: { "Content-Type": blob.type },
            body: blob,
            signal: AbortSignal.timeout(60000),
          },
        );
        if (!r.ok) throw Error(await r.text());
        item.uploaded = true;
      } catch {
        failures.push(speaker);
      }
    }
    // Keep failed chunks for a retry before the operator ends the session.
    if (failures.length)
      throw Error(
        `Recording upload failed (${failures.join(", ")}). Press End again to retry, or reset to cancel.`,
      );
    this.recorders.clear();
    this.activeRecorders.clear();
    await this.disconnect();
  }
  async reset() {
    await this.disconnect();
    this.recorders.clear();
    this.activeRecorders.clear();
    this.sid = null;
  }
  /** Who can hear whom, for the operator: other party present, sending audio, speaking. */
  reportStatus() {
    const room = this.room;
    if (!room || !this.onStatus) return;
    const other = [...room.remoteParticipants.values()][0];
    const sending =
      !!other &&
      [...other.audioTrackPublications.values()].some((p) => p.track);
    const me = room.localParticipant;
    this.onStatus({
      state: room.state,
      other: !other
        ? "absent"
        : !sending
          ? "no-audio"
          : other.isSpeaking
            ? "speaking"
            : "silent",
      me: !me.isMicrophoneEnabled ? "off" : me.isSpeaking ? "speaking" : "on",
    });
  }
  async disconnect() {
    this.generation += 1;
    clearInterval(this.statusTimer);
    this.onStatus?.(null);
    this.captioning = false;
    this.rec?.abort();
    for (const item of this.recorders.values()) this.stopRecording(item);
    if (this.room) {
      const room = this.room;
      this.room = null;
      room.removeAllListeners();
      await room.disconnect();
    }
    this.audioElements.forEach((e) => e.remove());
    this.audioElements = [];
  }
}
