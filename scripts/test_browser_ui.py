"""
Automated Playwright Browser Test for KisanRadar Dashboard & Replays.
Launches a headless Chromium browser, opens the dashboard, interacts with controls,
verifies live rendering, captures screenshots, and checks console logs for errors.
"""
import sys
import os
import time
import subprocess
import requests

from playwright.sync_api import sync_playwright

def run_browser_test():
    server_port = 8088
    server_url = f"http://127.0.0.1:{server_port}"
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    python_exe = sys.executable

    print(f"[1/5] Starting KisanRadar test server on {server_url}...")
    server_proc = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "app.main:app", "--port", str(server_port), "--host", "127.0.0.1"],
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server to become healthy
    ready = False
    for _ in range(30):
        try:
            r = requests.get(f"{server_url}/api/health", timeout=2)
            if r.status_code == 200:
                ready = True
                print("  -> KisanRadar server is up and healthy!")
                break
        except Exception:
            time.sleep(1)

    if not ready:
        server_proc.kill()
        raise RuntimeError("Server failed to start within 30 seconds.")

    console_logs = []
    page_errors = []

    try:
        print("[2/5] Launching Playwright headless Chromium...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1400, "height": 900})

            # Track console messages and uncaught exceptions
            page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
            page.on("pageerror", lambda err: page_errors.append(str(err)))

            print(f"[3/5] Navigating to {server_url}...")
            page.goto(server_url, wait_until="networkidle")

            title = page.title()
            print(f"  -> Page title: '{title}'")
            assert "KisanRadar" in title, f"Unexpected page title: {title}"

            # Check that map and header are present
            assert page.locator("#map").is_visible(), "Leaflet map container not visible!"
            assert page.locator("#crop").is_visible(), "Crop select dropdown not visible!"

            print("[4/5] Testing Thanjavur Benchmark Hotspot click & live analysis...")
            # Click the Thanjavur preset button
            thanjavur_btn = page.locator("button:has-text('Thanjavur')")
            assert thanjavur_btn.is_visible(), "Thanjavur preset button not found!"
            thanjavur_btn.click()

            # Wait for analysis results to appear in the side panel (up to 45s for live query)
            page.wait_for_selector("#out .gauges", timeout=60000)
            print("  -> Live analysis rendered successfully with multi-hazard gauges!")

            # Verify risk gauges rendered
            overall_gauge = page.locator(".gauges .g").first
            assert overall_gauge.is_visible(), "Risk gauge missing!"

            # Save full dashboard screenshot (full page to capture charts and provenance below fold)
            screenshot_dash = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "screenshots", "kisanradar_dashboard.png"))
            page.screenshot(path=screenshot_dash, full_page=True)
            print(f"  -> Saved full-page dashboard screenshot to: {screenshot_dash}")

            print("[4b/5] Testing Ludhiana Benchmark Hotspot click & live analysis...")
            ludhiana_btn = page.locator("button:has-text('Ludhiana')")
            assert ludhiana_btn.is_visible(), "Ludhiana preset button not found!"
            ludhiana_btn.click()
            page.wait_for_selector("#out .gauges", timeout=60000)
            time.sleep(2)
            screenshot_ludhiana = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "screenshots", "kisanradar_ludhiana.png"))
            page.screenshot(path=screenshot_ludhiana, full_page=True)
            print(f"  -> Saved Ludhiana screenshot to: {screenshot_ludhiana}")

            print("[5/5] Testing Historical Replay click (Punjab March 2022 Heat Shock)...")
            replay_btn = page.locator("button:has-text('Punjab 2022 Heat Shock')")
            assert replay_btn.is_visible(), "Punjab 2022 Heat Shock button not found!"
            replay_btn.click()

            # Wait for replay telemetry and yield loss card to appear
            page.wait_for_selector(".badge-replay", timeout=60000)
            page.wait_for_selector("text=Replayed Yield Impact", timeout=30000)
            time.sleep(2)
            print("  -> Historical replay loaded and rendered with archived telemetry!")

            # Save replay screenshot (full page)
            screenshot_replay = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "screenshots", "kisanradar_replay.png"))
            page.screenshot(path=screenshot_replay, full_page=True)
            print(f"  -> Saved full-page replay screenshot to: {screenshot_replay}")

            browser.close()

        print("\n=== Playwright Browser Test Completed Successfully ===")
        print(f"Total Console logs captured: {len(console_logs)}")
        for l in console_logs:
            if "error" in l.lower() or "warn" in l.lower():
                print("  Console warning/error:", l)

        print(f"Total Page JS errors: {len(page_errors)}")
        if page_errors:
            for err in page_errors:
                print("  JS Error:", err)
            raise AssertionError(f"Encountered {len(page_errors)} uncaught JavaScript errors!")

        print("Zero JavaScript errors encountered. UI verified.")

    finally:
        print("Terminating test server...")
        server_proc.kill()
        server_proc.wait()

if __name__ == "__main__":
    run_browser_test()
