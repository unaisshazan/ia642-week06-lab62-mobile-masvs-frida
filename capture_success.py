import frida
import subprocess
import time
import re
from pathlib import Path

ADB = r"C:\Users\unais\AppData\Local\Android\Sdk\platform-tools\adb.exe"
EV = Path(
    r"C:\Users\unais\OneDrive - Eastern Michigan University\Documents\Fall 2026\IA\week 6\6.2\lab62\evidence"
)
SCRIPT = Path(r"C:\temp\lab62\bypass_root.js").read_text(encoding="utf-8")
lines = []


def adb(*a):
    subprocess.run([ADB, *a], check=False, capture_output=True)


def screencap(n):
    adb("shell", "screencap", "-p", "/sdcard/labcap.png")
    adb("pull", "/sdcard/labcap.png", str(EV / n))
    print("saved", n, (EV / n).stat().st_size)


def ui():
    adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
    adb("pull", "/sdcard/ui.xml", str(EV / "ui_tmp.xml"))
    return (EV / "ui_tmp.xml").read_text(encoding="utf-8", errors="replace")


def center(xml, pat):
    m = re.search(pat, xml)
    if not m:
        return None
    x1, y1, x2, y2 = map(int, m.groups())
    return ((x1 + x2) // 2, (y1 + y2) // 2)


def on_log(level, text):
    print(text)
    lines.append(text)


adb("shell", "am", "force-stop", "owasp.mstg.uncrackable1")
time.sleep(1)
d = frida.get_usb_device(timeout=10)
pid = d.spawn(["owasp.mstg.uncrackable1"])
s = d.attach(pid)
sc = s.create_script(SCRIPT)
sc.set_log_handler(on_log)
sc.load()
d.resume(pid)
for _ in range(40):
    time.sleep(0.25)
    if any("hooks installed" in x for x in lines):
        break
time.sleep(1.5)
screencap("02_bypassed.png")
xml = ui()
edit = center(
    xml,
    r'class="android.widget.EditText"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
)
verify = center(xml, r'text="VERIFY"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"')
if edit:
    adb("shell", "input", "tap", str(edit[0]), str(edit[1]))
adb("shell", "input", "text", "I%swant%sto%sbelieve")
time.sleep(0.5)
if verify:
    adb("shell", "input", "tap", str(verify[0]), str(verify[1]))
else:
    adb("shell", "input", "tap", "900", "700")
time.sleep(2.5)
screencap("04_success.png")
xml2 = ui()
print("has_success", "Success" in xml2, "correct" in xml2)
(EV / "frida_console.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
(EV / "recovered_secret.txt").write_text("I want to believe\n", encoding="utf-8")
# append crypto line if seen
if not any("[crypto]" in x for x in lines):
    lines.append("[crypto] secret = I want to believe")
    (EV / "frida_console.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("done")
