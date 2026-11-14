import { VoiceCall } from "./voice.js";
const $ = (id) => document.getElementById(id),
  page = document.body.dataset.page;
const operator =
  page === "console" &&
  new URLSearchParams(location.search).get("mode") !== "viewer";
const producer = page === "test-caller",
  role = producer
    ? "app"
    : operator
      ? "operator"
      : page === "caller"
        ? "caller"
        : "viewer";
let ws,
  state = { phase: "idle" },
  imageURL,
  clockOffset = 0,
  ending = false,
  audioContext,
  beatTimer,
  reminderTimer,
  recognition,
  listenEnabled = false,
  speaking = false,
  frameBusy = false,
  media;
const error = (message) => {
  if ($("error")) {
    $("error").hidden = false;
    $("error").textContent = message;
  }
};
function send(data) {
  if (ws?.readyState === WebSocket.OPEN)
    ws.send(JSON.stringify({ ...data, ts: Date.now() }));
  else error("Server disconnected. Reconnecting…");
}
const elapsed = () =>
  state.started_at
    ? Math.max(
        0,
        ((state.ended_at || Date.now() + clockOffset) - state.started_at) /
          1000,
      )
    : 0;
const voice = new VoiceCall({
  onCaption: (text) => send({ type: "dispatcher_said", text, final: true }),
  onError: error,
  getElapsed: elapsed,
  onStatus: (s) => {
    const el = $("voice");
    if (!el) return;
    el.hidden = !s;
    if (!s) return;
    if (s.state !== "connected") {
      el.textContent = "Audio reconnecting…";
      el.dataset.level = "warn";
      return;
    }
    el.textContent = `${
      {
        absent: "Glasses wearer not on audio yet",
        "no-audio": "Glasses wearer joined · no sound received",
        silent: "Glasses wearer · silent",
        speaking: "Glasses wearer · speaking",
      }[s.other]
    }   ·   Your mic · ${s.me}`;
    el.dataset.level = ["silent", "speaking"].includes(s.other) ? s.other : "warn";
  },
});
function text(id, value) {
  if ($(id)) $(id).textContent = value;
}
function audio() {
  audioContext ??= new AudioContext();
  audioContext.resume();
  return audioContext;
}
function beep(freq = 850, duration = 0.055) {
  const ac = audio(),
    o = ac.createOscillator(),
    gain = ac.createGain();
  o.frequency.value = freq;
  gain.gain.setValueAtTime(0.09, ac.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + duration);
  o.connect(gain).connect(ac.destination);
  o.start();
  o.stop(ac.currentTime + duration);
}
function stopGuide() {
  speechSynthesis.cancel();
  speaking = false;
  clearInterval(beatTimer);
  clearInterval(reminderTimer);
  beatTimer = null;
  reminderTimer = null;
  recognition?.abort();
}
function speak(message) {
  if (!producer) return;
  recognition?.abort();
  speechSynthesis.cancel();
  speaking = true;
  const u = new SpeechSynthesisUtterance(message);
  u.lang = "en-US";
  u.onend = u.onerror = () => {
    speaking = false;
    if (listenEnabled && state.phase === "ai_guide") startListening();
  };
  speechSynthesis.speak(u);
}
function startBeat() {
  if (beatTimer || !producer) return;
  beatTimer = setInterval(() => beep(), 60000 / 110);
  reminderTimer = setInterval(
    () => speak("Keep pushing hard and fast, follow the beat."),
    20000,
  );
}
function connect() {
  ws = new WebSocket(
    `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}${producer ? "/ws/app" : `/ws/ui?role=${role}`}`,
  );
  ws.binaryType = "blob";
  ws.onopen = () => {
    text("connection", "● Server connected");
    $("connection")?.classList.remove("offline");
  };
  ws.onclose = () => {
    text("connection", "● Reconnecting");
    $("connection")?.classList.add("offline");
    stopGuide();
    // Keep the independent LiveKit call and recordings alive during WS reconnection.
    setTimeout(connect, 2000);
  };
  ws.onmessage = (event) => {
    if (event.data instanceof Blob) {
      if ($("frame")) {
        if (imageURL) URL.revokeObjectURL(imageURL);
        imageURL = URL.createObjectURL(event.data);
        $("frame").src = imageURL;
        $("frame").hidden = false;
      }
      return;
    }
    const m = JSON.parse(event.data);
    if (m.type === "state") render(m);
    if (m.type === "error") error(m.message);
    if (m.type === "messenger") card(m.card);
    if (m.type === "caller_heard") {
      text("caption", m.text);
      text(
        "source",
        m.source === "ai_guide"
          ? "Guide (fixed script)"
          : "Dispatcher",
      );
      if (m.source === "ai_guide" && state.phase === "ai_guide") {
        speak(m.text);
        if (m.step_id === "cpr") startBeat();
      }
      if (m.source === "dispatcher" && $("speakCaptions")?.checked) {
        speechSynthesis.cancel();
        speechSynthesis.speak(new SpeechSynthesisUtterance(m.text));
      }
    }
    if (m.type === "pickup") {
      stopGuide();
      if (producer) join();
    }
    if (m.type === "end" || (m.type === "override" && m.action === "reset")) {
      stopGuide();
      voice.disconnect();
    }
    if (m.type === "report_progress" && m.session_id === state.session_id)
      text("progress", `Report: ${m.step}…`);
    if (m.type === "report_ready" && m.session_id === state.session_id)
      showReport(m.url);
  };
}
function card(c = {}) {
  text("situation", c.situation || "No active incident.");
  text(
    "scene",
    c.scene || "—",
  );
  text(
    "location",
    c.location?.lat !== undefined
      ? `${c.location.lat.toFixed(4)}, ${c.location.lon.toFixed(4)}`
      : "Not provided",
  );
  if ($("facts")) {
    $("facts").replaceChildren();
    for (const f of c.facts || []) {
      const li = document.createElement("li"),
        t = document.createElement("time");
      t.textContent = `+${f.t.toFixed(1)}s`;
      li.append(t, document.createTextNode(f.text));
      $("facts").append(li);
    }
  }
}
// Guide protocol strip: what the witness reported, step by step.
function protocol() {
  const list = $("protocol");
  if (!list) return;
  const labels = (state.timeline || []).map((e) => e.label);
  const reported = (yes, no) =>
    labels.includes(yes) ? "Yes" : labels.includes(no) ? "No" : "";
  const responsive = reported("Responding (reported)", "Not responding (reported)");
  const breathing = reported(
    "Breathing normally (reported)",
    "Not breathing normally (reported)",
  );
  const live = ["ai_guide", "connected"].includes(state.phase);
  const rows = [
    [responsive, state.step === "responsive"],
    [breathing, state.step === "breathing"],
    [state.step === "cpr" ? (live ? "Guiding" : "Done") : "", state.step === "cpr"],
  ];
  const stopped = state.step === "stay";
  [...list.children].forEach((li, i) => {
    const [value, current] = rows[i];
    li.dataset.state =
      state.phase === "idle"
        ? "todo"
        : current && live
          ? "current"
          : value
            ? "done"
            : stopped
              ? "skipped"
              : "todo";
    li.querySelector("em").textContent =
      li.dataset.state === "skipped" ? "Not needed" : value;
  });
}
function render(next) {
  const previous = state;
  state = next;
  clockOffset = (next.server_now || Date.now()) - Date.now();
  if (previous.session_id !== next.session_id) {
    voice.reset();
    text("caption", "—");
    text("progress", "");
    if ($("reportLink")) $("reportLink").hidden = true;
    if ($("reportFrame")) {
      $("reportFrame").hidden = true;
      $("reportFrame").removeAttribute("src");
    }
    if ($("frame")) $("frame").hidden = true;
  }
  text(
    "phase",
    {
      idle: "Waiting for a call",
      ai_guide: "Incoming emergency",
      connected: "On call",
      ended: "Call ended",
    }[state.phase],
  );
  document.body.dataset.phase = state.phase;
  $("phase").className =
    state.phase === "ai_guide"
      ? "incoming"
      : state.phase === "connected"
        ? "connected"
        : "";
  if (
    state.phase === "ai_guide" &&
    previous.phase !== "ai_guide" &&
    operator &&
    audioContext
  )
    beep(600, 0.4);
  if (state.phase !== "ai_guide" && previous.phase !== state.phase) stopGuide();
  if ($("beat"))
    $("beat").hidden = !(state.step === "cpr" && state.phase === "ai_guide");
  if (state.phase === "idle" || state.phase === "ended") voice.disconnect();
  card(state.card);
  protocol();
  text(
    "device",
    state.device?.glasses
      ? `Glasses ${state.device.glasses} · ${state.device.stream || "unknown"}${state.device.battery != null ? " · " + state.device.battery + "%" : ""}`
      : producer
        ? "Browser simulator"
        : "Camera status unavailable",
  );
  if ($("timeline")) {
    $("timeline").replaceChildren();
    for (const e of state.timeline || []) {
      const li = document.createElement("li"),
        t = document.createElement("time");
      t.textContent = `+${e.t.toFixed(1)}s`;
      li.append(t, document.createTextNode(e.label));
      $("timeline").append(li);
    }
  }
  if ($("answer")) {
    $("answer").disabled = !["ai_guide", "connected"].includes(state.phase);
    $("answer").textContent =
      state.phase === "connected" ? "Reconnect audio" : "Answer call";
  }
  if ($("end")) $("end").disabled = state.phase !== "connected" || ending;
  if ($("yes")) {
    $("yes").disabled = $("no").disabled =
      state.phase !== "ai_guide" ||
      !["responsive", "breathing"].includes(state.step);
  }
  if (state.subtitles?.length) {
    text("caption", state.subtitles.at(-1).text);
    text("source", "Dispatcher");
  }
  if (
    producer &&
    state.phase === "connected" &&
    previous.session_id !== state.session_id
  )
    join();
  if (state.report_status === "done") showReport(`/report/${state.session_id}`);
}
function showReport(url) {
  text("progress", "Report ready");
  if ($("reportLink")) {
    $("reportLink").href = url;
    $("reportLink").hidden = false;
  }
  if ($("reportFrame")) {
    $("reportFrame").src = url;
    $("reportFrame").hidden = false;
  }
}
async function join() {
  try {
    await voice.join(producer ? "caller" : "dispatcher");
  } catch (e) {
    error(`${e.message} Live voice unavailable; captions still work.`);
  }
}
if (operator) {
  for (const id of ["operatorControls", "captionControls", "tools", "enableSound"])
    if ($(id)) $(id).hidden = false;
  $("answer").onclick = async () => {
    audio();
    if (state.phase !== "connected") {
      send({ type: "pickup" });
      await new Promise((resolve) => {
        const poll = setInterval(() => {
          if (state.phase === "connected") {
            clearInterval(poll);
            resolve();
          }
        }, 50);
        setTimeout(() => {
          clearInterval(poll);
          resolve();
        }, 3000);
      });
    }
    await join();
  };
  $("end").onclick = async () => {
    ending = true;
    $("end").disabled = true;
    try {
      await voice.finish();
      send({ type: "end" });
    } catch (e) {
      error(e.message);
    } finally {
      ending = false;
      $("end").disabled = false;
    }
  };
  $("enableSound").onclick = () => {
    beep();
    $("enableSound").textContent = "Alert sound on";
  };
  if ($("sendCaption")) $("sendCaption").onclick = () => {
    const input = $("manualCaption");
    if (input.value.trim()) {
      send({ type: "dispatcher_said", text: input.value, final: true });
      input.value = "";
    }
  };
  for (const b of document.querySelectorAll("[data-action]"))
    b.onclick = () => send({ type: "override", action: b.dataset.action });
  document.addEventListener("keydown", (e) => {
    if (
      /INPUT|TEXTAREA/.test(e.target.tagName) ||
      e.ctrlKey ||
      e.metaKey ||
      e.altKey
    )
      return;
    const action = {
      1: "trigger",
      2: "answer_yes",
      3: "answer_no",
      4: "next_step",
      0: "reset",
    }[e.key];
    if (action) send({ type: "override", action });
  });
} else if ($("viewerControls")) $("viewerControls").hidden = false;
function startListening() {
  if (speaking || !listenEnabled || !["idle", "ai_guide"].includes(state.phase))
    return;
  const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Speech) {
    error("Voice commands unavailable. Use Yes / No.");
    return;
  }
  recognition?.abort();
  const rec = new Speech();
  recognition = rec;
  rec.lang = "en-US";
  rec.continuous = false;
  rec.interimResults = false;
  rec.onresult = (e) => {
    const words = e.results[0][0].transcript
      .toLowerCase()
      .replace(/[^a-z ]/g, "")
      .trim();
    const said = (re) => new RegExp(`\\b(${re})\\b`).test(words);
    if (said("emergency|urgence") && state.phase === "idle")
      send({ type: "alert", trigger: "voice" });
    else if (said("yes|yeah|yep|yup|oui|ouais|no|nope|nah|non|nan") && state.phase === "ai_guide")
      send({
        type: "answer",
        step_id: state.step,
        value: said("yes|yeah|yep|yup|oui|ouais") ? "yes" : "no",
      });
  };
  rec.onerror = (e) => {
    if (e.error === "not-allowed") listenEnabled = false;
  };
  rec.onend = () => {
    if (
      listenEnabled &&
      !speaking &&
      ["idle", "ai_guide"].includes(state.phase)
    )
      setTimeout(startListening, 500);
  };
  try {
    rec.start();
  } catch {}
}
if (producer) {
  $("emergency").onclick = () => {
    audio();
    send({ type: "alert", trigger: "button" });
  };
  for (const value of ["yes", "no"])
    $(value).onclick = () =>
      send({ type: "answer", step_id: state.step, value });
  $("joinCall").onclick = join;
  $("listen").onclick = () => {
    listenEnabled = !listenEnabled;
    $("listen").textContent = listenEnabled
      ? "Disable voice commands"
      : "Enable voice commands";
    if (listenEnabled) startListening();
    else recognition?.abort();
  };
  $("camera").onclick = async () => {
    try {
      media = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false,
      });
      $("localVideo").srcObject = media;
      $("localVideo").hidden = false;
    } catch (e) {
      error(`Camera unavailable: ${e.message}. Synthetic frames retained.`);
    }
  };
  setInterval(() => {
    if (
      !["ai_guide", "connected"].includes(state.phase) ||
      ws?.readyState !== WebSocket.OPEN ||
      ws.bufferedAmount > 1e6 ||
      frameBusy
    )
      return;
    const canvas = $("synthetic"),
      ctx = canvas.getContext("2d");
    if (media && $("localVideo").readyState >= 2)
      ctx.drawImage($("localVideo"), 0, 0, canvas.width, canvas.height);
    else {
      ctx.fillStyle = "#142a33";
      ctx.fillRect(0, 0, 960, 540);
      ctx.fillStyle = "#9aefbd";
      ctx.font = "32px sans-serif";
      ctx.fillText("FIRSTFIVE / SYNTHETIC DEMO", 55, 80);
      ctx.fillStyle = "#b5c7ca";
      ctx.font = "24px sans-serif";
      ctx.fillText(`+${elapsed().toFixed(1)}s · ${state.phase}`, 55, 130);
      ctx.fillText("No patient image · no glasses connected", 55, 180);
      ctx.strokeStyle = "#69858c";
      ctx.lineWidth = 18;
      ctx.beginPath();
      ctx.arc(270, 330, 35, 0, Math.PI * 2);
      ctx.moveTo(310, 330);
      ctx.lineTo(560, 330);
      ctx.lineTo(680, 410);
      ctx.moveTo(560, 330);
      ctx.lineTo(700, 300);
      ctx.stroke();
    }
    frameBusy = true;
    canvas.toBlob(
      (blob) => {
        frameBusy = false;
        if (blob && ws.readyState === WebSocket.OPEN) ws.send(blob);
      },
      "image/jpeg",
      0.5,
    );
  }, 350);
}
setInterval(() => {
  const t = Math.floor(elapsed());
  text(
    "timer",
    `${String(Math.floor(t / 60)).padStart(2, "0")}:${String(t % 60).padStart(2, "0")}`,
  );
}, 200);
connect();
