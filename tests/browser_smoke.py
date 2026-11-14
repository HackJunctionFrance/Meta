"""Real Chromium smoke test against a running server. No external service calls."""

import os

from playwright.sync_api import expect, sync_playwright

BASE = os.getenv("FIRSTFIVE_TEST_URL", "http://127.0.0.1:8000")
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=os.getenv("CHROMIUM_PATH", "/usr/bin/chromium"),
        headless=True,
        args=[
            "--no-sandbox",
            "--use-fake-ui-for-media-stream",
            "--use-fake-device-for-media-stream",
        ],
    )
    context = browser.new_context(
        viewport={"width": 1440, "height": 1000}, permissions=["camera", "microphone"]
    )
    errors = []
    op = context.new_page()
    caller = context.new_page()
    viewer = context.new_page()
    for page in (op, caller, viewer):
        page.on("pageerror", lambda e: errors.append(str(e)))
    op.goto(BASE + "/console?mode=operator")
    caller.goto(BASE + "/test-caller")
    viewer.goto(BASE + "/console?mode=viewer")
    expect(op.locator("#connection")).to_contain_text("Server connected")
    op.locator("#tools summary").click()
    op.locator('[data-action="reset"]').click()
    expect(caller.locator("#phase")).to_have_text("Waiting for a call")
    caller.locator("#emergency").click()
    expect(op.locator("#phase")).to_have_text("Incoming emergency")
    expect(caller.locator("#caption")).to_contain_text("Is he responding")
    caller.locator("#no").click()
    expect(caller.locator("#caption")).to_contain_text("breathing normally")
    caller.locator("#no").click()
    expect(op.locator("#situation")).to_contain_text("Suspected cardiac arrest")
    expect(viewer.locator("#frame")).to_be_visible()
    assert viewer.locator("#frame").evaluate("(e)=>e.naturalWidth") > 0
    assert not viewer.locator("#operatorControls").is_visible()
    op.screenshot(path="/tmp/firstfive-console.png", full_page=True)
    op.locator("#answer").click()
    expect(caller.locator("#phase")).to_have_text("Dispatcher connected")
    expect(caller.locator("#beat")).to_be_hidden()
    expect(op.locator("#error")).to_contain_text("LiveKit not configured")
    op.locator("#manualCaption").fill("Keep following my instructions.")
    op.locator("#sendCaption").click()
    expect(caller.locator("#caption")).to_have_text("Keep following my instructions.")
    viewer.reload()
    expect(viewer.locator("#phase")).to_have_text("Dispatcher connected")
    expect(viewer.locator("#frame")).to_be_visible()
    op.locator("#end").click()
    expect(op.locator("#reportLink")).to_be_visible(timeout=30000)
    report = context.new_page()
    report.goto(BASE + op.locator("#reportLink").get_attribute("href"))
    expect(report.locator("body")).to_contain_text("Keep following my instructions.")
    expect(report.locator("body")).to_contain_text("Handover · MIST")
    report.screenshot(path="/tmp/firstfive-report.png", full_page=True)
    op.locator('[data-action="reset"]').click()
    expect(viewer.locator("#phase")).to_have_text("Waiting for a call")
    expect(viewer.locator("#frame")).to_be_hidden()
    assert not errors, errors
    print(
        "PASS: three pages, synthetic JPEG video, both no answers, handoff, missing-provider fallback, captions, reconnect, report, reset; zero browser exceptions."
    )
    browser.close()
