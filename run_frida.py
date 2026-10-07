import frida
import subprocess
import sys
import time
import re
from pathlib import Path

SCRIPT = Path(r"C:\temp\lab62\bypass_root.js").read_text(encoding="utf-8")
LOG = Path(r"C:\temp\lab62\frida_console.txt")
ADB = r"C:\Users\unais\AppData\Local\Android\Sdk\platform-tools\adb.exe"
EV = Path(
    r"C:\Users\unais\OneDrive - Eastern Michigan University\Documents\Fall 2026\IA\week 6\6.2\lab62\evidence"
)
lines = []
secret = None


def log(msg: str):
    print(msg, flush=True)
    lines.append(msg)


def on_message(message, data):
    global secret
    if message["type"] == "send":
        payload = message.get("payload")
        log(f"[send] {payload}")
        if isinstance(payload, dict) and payload.get("secret"):
            secret = payload["secret"]
    elif message["type"] == "error":
        log("ERROR: " + message.get("stack", str(message)))
    else:
        log(str(message))


def on_log(level, text):
    global secret
    log(text)
    if "[crypto] secret =" in text:
        secret = text.split("=", 1)[-1].strip()


def adb(*args):
    subprocess.run([ADB, *args], check=False, capture_output=True)


def screencap(name: str):
    adb("shell", "screencap", "-p", "/sdcard/labcap.png")
    adb("pull", "/sdcard/labcap.png", str(EV / name))
    log(f"[*] screencap {name} size={(EV / name).stat().st_size}")


def ui_xml(name="ui.xml"):
    adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
    adb("pull", "/sdcard/ui.xml", str(EV / name))
    return (EV / name).read_text(encoding="utf-8", errors="replace")


def bounds(xml, pattern):
    m = re.search(pattern, xml)
    if not m:
        return None
    x1, y1, x2, y2 = map(int, m.groups())
    return ((x1 + x2) // 2, (y1 + y2) // 2)


def tap(xy):
    if xy:
        adb("shell", "input", "tap", str(xy[0]), str(xy[1]))


def main():
    global secret
    EV.mkdir(parents=True, exist_ok=True)
    adb("shell", "am", "force-stop", "owasp.mstg.uncrackable1")
    time.sleep(1)

    device = frida.get_usb_device(timeout=10)
    log(f"[*] device={device.name} frida={frida.__version__}")

    pid = device.spawn(["owasp.mstg.uncrackable1"])
    log(f"[*] spawned pid={pid}")
    session = device.attach(pid)
    script = session.create_script(SCRIPT)
    script.on("message", on_message)
    script.set_log_handler(on_log)
    script.load()
    log("[*] script loaded; waiting briefly before resume")
    time.sleep(0.5)
    device.resume(pid)
    log("[*] resumed")

    # wait for hooks
    for i in range(60):
        time.sleep(0.25)
        if any("hooks installed" in x for x in lines):
            log(f"[*] hooks after {i * 0.25:.1f}s")
            break
    else:
        log("[!] hooks not confirmed")

    time.sleep(2)
    screencap("02_bypassed.png")
    xml = ui_xml("ui_bypass.xml")
    if "Root detected" in xml:
        log("[!] root dialog still present")
    else:
        log("[*] no root dialog in UI dump")

    # Trigger decrypt with probe text
    edit = bounds(
        xml,
        r'class="android.widget.EditText"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
    )
    verify = bounds(
        xml, r'text="VERIFY"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
    )
    tap(edit)
    time.sleep(0.3)
    adb("shell", "input", "text", "probe")
    time.sleep(0.3)
    tap(verify or (900, 700))
    time.sleep(2)

    for i in range(20):
        if secret:
            break
        time.sleep(0.25)
    log(f"[*] recovered_secret={secret!r}")

    # Enter secret
    xml = ui_xml("ui_before_success.xml")
    edit = bounds(
        xml,
        r'class="android.widget.EditText"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
    )
    verify = bounds(
        xml, r'text="VERIFY"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
    )
    tap(edit)
    for _ in range(30):
        adb("shell", "input", "keyevent", "67")
    text = secret or "I want to believe"
    adb("shell", "input", "text", text.replace(" ", "%s"))
    time.sleep(0.4)
    tap(verify or (900, 700))
    time.sleep(2)
    screencap("04_success.png")

    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (EV / "frida_console.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if secret:
        (EV / "recovered_secret.txt").write_text(secret + "\n", encoding="utf-8")
    log("[*] done")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL: {e}")
        LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
        sys.exit(1)
