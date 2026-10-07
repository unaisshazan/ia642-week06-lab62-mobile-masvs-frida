#!/usr/bin/env python3
"""IA642 Lab 6.2 report: midterm-style LaTeX, then pdflatex."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
LAB_DIR = SCRIPT_DIR.parent
EV = SCRIPT_DIR / "evidence"
TEX_DIR = SCRIPT_DIR / "latex_build"
FIG_DIR = TEX_DIR / "figures"
TEX_PATH = TEX_DIR / "lab62.tex"
PDF_OUT = LAB_DIR / "Ali_Usama_IA642_Week06_Lab6.2_Mobile_MASVS_Frida.pdf"
SUBMIT = LAB_DIR / "SUBMIT_Lab62"
SUBMIT_PDF = SUBMIT / PDF_OUT.name


def read(name: str) -> str:
    p = EV / name
    if not p.is_file():
        return f"[missing: {name}]"
    raw = p.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    text = raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(ch if (ch in "\n\t" or 32 <= ord(ch) <= 126) else " " for ch in text)
    return text.strip()


def verb(s: str) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", s.replace("\x00", ""))


def listing(title: str, body: str) -> str:
    return "\n".join(
        [
            rf"\noindent\textbf{{{title}}}",
            r"\begin{lstlisting}",
            verb(body.strip()),
            r"\end{lstlisting}",
            "",
        ]
    )


def fig(name: str, caption: str) -> str:
    return "\n".join(
        [
            r"\begin{figure}[H]",
            r"\centering",
            rf"\includegraphics[width=0.55\textwidth]{{figures/{name}}}",
            rf"\caption{{{caption}}}",
            r"\end{figure}",
            "",
        ]
    )


def build_tex() -> str:
    sha = read("00_apk_sha256.txt")
    install = read("00_install.txt")
    tags = read("00_build_tags.txt")
    su = read("00_su_path.txt")
    c_java = read("c.java")
    console = read("frida_console.txt")
    secret = read("recovered_secret.txt")
    bypass = read("bypass_root.js")
    crypto = read("crypto_a.java")
    check = read("secret_check_a.java")

    preamble = r"""
\documentclass[11pt,letterpaper]{article}
\usepackage[margin=1in]{geometry}
\sloppy\emergencystretch=4em
\usepackage{array,booktabs,tabularx,enumitem,parskip,ragged2e,titlesec,microtype,xcolor,colortbl,listings,needspace,xurl,fancyhdr,graphicx,float,seqsplit}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[colorlinks=true,linkcolor=blue,urlcolor=blue]{hyperref}
\hypersetup{pdfauthor={Unais Ali and Hafiz Usama}, pdftitle={IA 642 Lab 6.2 Mobile MASVS Frida}}
\definecolor{tblhead}{HTML}{1F4E79}
\definecolor{codebg}{HTML}{F7FAFC}
\setlength{\parindent}{0pt}
\renewcommand{\arraystretch}{1.28}
\setlist[itemize]{leftmargin=1.2em,itemsep=0.25em,topsep=0.3em}
\setlist[enumerate]{leftmargin=1.3em,itemsep=0.3em,topsep=0.3em}
\newcolumntype{Y}{>{\RaggedRight\arraybackslash}X}
\newcolumntype{P}[1]{>{\RaggedRight\arraybackslash}p{#1}}
\titleformat{name=\section,numberless}{\large\bfseries\color{tblhead}}{}{0em}{}
\titleformat{name=\subsection,numberless}{\normalsize\bfseries\color{tblhead}}{}{0em}{}
\lstset{
  basicstyle=\ttfamily\footnotesize,
  backgroundcolor=\color{codebg},
  frame=single,
  rulecolor=\color{tblhead},
  breaklines=true,
  breakatwhitespace=false,
  columns=fullflexible,
  keepspaces=true,
  showstringspaces=false,
  aboveskip=0.45em,
  belowskip=0.45em,
  xleftmargin=2pt,
  xrightmargin=2pt
}
\pagestyle{fancy}
\fancyhf{}
\fancyfoot[L]{\footnotesize Ali \& Usama | IA 642 Lab 6.2}
\fancyfoot[R]{\footnotesize Page \thepage}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0.4pt}
\begin{document}
\begin{center}
{\LARGE\bfseries IA 642 Defensive Security}\\[0.25em]
{\Large Week 06, Module 01 --- Lab 6.2}\\[0.15em]
{\large Instrumenting a Mobile App: MASVS, Frida \& Root Bypass}\\[0.15em]
{\normalsize OWASP MAS UnCrackable-Level1 on Android Emulator}\\[0.3em]
\end{center}

\begin{tabularx}{\textwidth}{@{}l Y l Y@{}}
\toprule
\textbf{Group members} & Unais Ali & \textbf{EID} & E02805019 \\
 & Hafiz Usama &  & E02574092 \\
\textbf{Course} & IA 642 Defensive Security & \textbf{Lab} & 6.2 (Week 06) \\
\textbf{Date} & October 7, 2026 & \textbf{Target} & UnCrackable-Level1 \\
\textbf{Host tools} & jadx 1.5.1, Frida 16.5.9 & \textbf{Device} & AVD IA642\_API30 (Google APIs x86\_64) \\
\textbf{GitHub} & \multicolumn{3}{Y@{}}{\url{https://github.com/unaisshazan/ia642-week06-lab62-mobile-masvs-frida}} \\
\bottomrule
\end{tabularx}

\vspace{0.55em}
\section*{Lab overview}
Meridian's patient mobile app treats root/jailbreak detection as if it made the client trustworthy.
This lab proves the opposite on the authorized OWASP MAS UnCrackable-Level1 crackme: we observe
MASVS-RESILIENCE-1 root detection, read the check in jadx, defeat it at runtime with Frida
(showing the absence of RESILIENCE-4), recover a hard-coded AES secret from memory
(MASVS-CRYPTO-2 / STORAGE), and write the defender redesign that belongs with Lab~6.1's
server-side authorization.

\section*{Environment}
\begin{itemize}
  \item Android emulator: \texttt{IA642\_API30} (Google APIs x86\_64, not Play Store) so \texttt{adb root} works.
  \item Install: \texttt{adb install -r} succeeded.
  \item Build tags: \texttt{dev-keys}; \texttt{su} path: \path{/system/xbin/su}.
  \item Frida client/server 16.5.9; hook script \texttt{bypass\_root.js}; jadx output in \texttt{decomp/}.
  \item Public evidence repo (APK, decompiled sources, screenshots; no report PDF):
        \url{https://github.com/unaisshazan/ia642-week06-lab62-mobile-masvs-frida}
\end{itemize}
"""

    body: list[str] = []
    # Keep long hash in listing so it does not stretch/break in texttt
    body.append(
        listing(
            "Install / integrity evidence",
            f"{install}\n"
            f"SHA-256={sha.strip()}\n"
            f"ro.build.tags={tags.strip()}\n"
            f"su={su.strip()}",
        )
    )

    body.append(r"\section*{Part A --- Observe the control}")
    body.append(
        r"With \texttt{adb root} active, launching \texttt{owasp.mstg.uncrackable1} fires the "
        r"MASVS-RESILIENCE-1 platform-integrity gate. The dialog states the device is unacceptable "
        r"and OK calls \texttt{System.exit(0)}."
    )
    body.append(fig("01_root_detected.png", "Screenshot \#1: Root detected dialog on rooted Google APIs emulator."))

    body.append(r"\section*{Part B --- Static analysis (jadx)}")
    body.append(
        r"\texttt{jadx -d decomp UnCrackable-Level1.apk} yields readable Java with no meaningful "
        r"obfuscation. \texttt{MainActivity.onCreate} gates on "
        r"\texttt{c.a() || c.b() || c.c()}. Class \texttt{sg.vantagepoint.a.c} implements three "
        r"ordinary filesystem/property checks:"
    )
    body.append(listing("sg.vantagepoint.a.c (root checks)", c_java))
    body.append(
        r"Secret verification lives in \texttt{sg.vantagepoint.uncrackable1.a}: hard-coded AES key "
        r"\texttt{8d127684cbc37c17616d806cf50473cc} and Base64 ciphertext decrypt via "
        r"\texttt{sg.vantagepoint.a.a} (AES/ECB)."
    )
    body.append(listing("Secret check (uncrackable1.a)", check))
    body.append(listing("AES helper (sg.vantagepoint.a.a)", crypto))

    body.append(r"\subsection*{Critical thinking \#1}")
    body.append(
        r"The missing MASVS group is \textbf{MASVS-RESILIENCE-3 / RESILIENCE-4} anti-analysis "
        r"(and the app's RESILIENCE-1 control is present but hollow). There is no obfuscation, "
        r"no integrity attestation beyond naive file checks, and no anti-Frida / anti-debug. "
        r"That absence makes Part~C trivial: jadx shows exact class/method names, and Frida can "
        r"\texttt{Java.use} them without fighting packing or native traps. To move from "
        r"``easily bypassed'' to ``expensive,'' the app would need at least: "
        r"(1)~\textbf{RESILIENCE-3} control-flow obfuscation / string encryption / native-wrapped checks so "
        r"symbols are not obvious in jadx; "
        r"(2)~\textbf{RESILIENCE-4} Frida/debugger detection, emulator heuristics, and runtime integrity "
        r"(e.g., Play Integrity / key attestation) so instrumentation is noticed and sensitive paths refuse "
        r"to run. Even then MASVS treats resilience as cost-raising defense-in-depth, not primary security."
    )

    body.append(r"\section*{Part C --- Frida bypass and secret recovery}")
    body.append(
        r"Spawn under Frida with hooks installed before \texttt{onCreate}: "
        r"\texttt{frida -U -f owasp.mstg.uncrackable1 -l bypass\_root.js} "
        r"(automated via Python Frida API; client/server 16.5.9). Each root method is forced to "
        r"\texttt{false}; the AES helper prints plaintext on VERIFY."
    )
    body.append(listing("bypass\_root.js", bypass))
    body.append(listing("Frida console (own capture)", console))
    body.append(fig("02_bypassed.png", "Screenshot \#2: App runs after Frida bypass; root dialog gone."))
    body.append(
        rf"Recovered secret: \texttt{{{secret}}}. Entering it yields the Success dialog "
        r"(MASVS-CRYPTO-2 failure: key shipped in the APK is a published key)."
    )
    body.append(fig("04_success.png", "Screenshot \#3: Success dialog after entering the recovered secret."))

    body.append(r"\subsection*{Critical thinking \#2}")
    body.append(
        r"``The client can always reach its own secrets'' means anything decrypted, compared, or "
        r"stored in the app process is available to an instrumented or reverse-engineered client. "
        r"Lab~6.1's account API must therefore \textbf{never} trust the mobile app to enforce "
        r"authorization: object-level checks (who may read which account) and field-level allow-lists "
        r"must run on the server after authenticating the user, exactly as ASVS 8.2.2 / 8.2.3 required. "
        r"The matching MASVS control objective is \textbf{MASVS-AUTH-1} (the app uses secure "
        r"authentication and authorization that the endpoint enforces), not a local root gate. "
        r"A rooted phone that still holds a valid Cognito token must receive the same server-side "
        r"deny for Bob's account that Lab~6.1 demonstrated."
    )

    body.append(r"\section*{Part D --- Defender analysis}")
    body.append(r"\subsection*{1. What root detection is actually good for}")
    body.append(
        r"Legitimate uses: (a)~a \textbf{risk signal} for step-up auth, reduced functionality, or "
        r"SOC alerting when the device looks compromised; (b)~a \textbf{compliance / policy }hint "
        r"for enterprise MDM or high-risk workflows, raising attacker cost. It must \textbf{never} "
        r"be the sole control that protects secrets, tokens, or authorization decisions. "
        r"Verizon DBIR-style breach research and Flashpoint's 2026 threat reporting both keep "
        r"emphasizing credential abuse and attacker reuse of weak trust boundaries---client-side "
        r"gates do not change those economics if the API still trusts the app."
    )
    body.append(r"\subsection*{2. Make the bypass expensive (MASVS-RESILIENCE-1..4)}")
    body.append(
        "\n".join(
            [
                r"\begin{itemize}",
                r"\item \textbf{RESILIENCE-1:} Play Integrity / hardware-backed attestation instead of \texttt{su}-path grepping; cost: attacker needs compromised attestation path or stolen device identity.",
                r"\item \textbf{RESILIENCE-2:} Tamper/repack detection (signing cert + runtime checksums); cost: rebuilds and resigning break the binary.",
                r"\item \textbf{RESILIENCE-3:} Obfuscation, native checks, encrypted strings; cost: hours/days of RE instead of minutes in jadx.",
                r"\item \textbf{RESILIENCE-4:} Anti-Frida, anti-debug, emulator detection, timed integrity; cost: custom tooling and kernel-level work.",
                r"\end{itemize}",
                r"None of these make bypass impossible; they buy time and raise skill/price.",
            ]
        )
    )
    body.append(r"\subsection*{3. Move the trust boundary}")
    body.append(
        r"Redesign: the ``secret'' and any authorization decision live on Meridian's API (Lab~6.1 "
        r"pattern). The app authenticates (Cognito/OIDC), then calls \texttt{GET /accounts/\{id\}}; "
        r"Lambda enforces owner checks and field allow-lists. The mobile client displays only "
        r"server-returned fields. Root detection may still degrade UX or alert, but cannot be what "
        r"protects PHI. That is defense-in-depth consistent with MASVS's resilience philosophy."
    )

    body.append(r"\section*{MASVS scorecard (UnCrackable-L1)}")
    body.append(
        "\n".join(
            [
                r"{\footnotesize",
                r"\begin{tabularx}{\textwidth}{@{}P{3.6cm} P{1.6cm} Y@{}}",
                r"\toprule",
                r"\rowcolor{tblhead}",
                r"\textcolor{white}{\textbf{MASVS control}} & "
                r"\textcolor{white}{\textbf{Pass/Fail}} & "
                r"\textcolor{white}{\textbf{Evidence from this lab}} \\",
                r"\midrule",
                r"MASVS-RESILIENCE-1 (platform integrity) & Partial & Root check present (\texttt{c.a/b/c}) but trivially bypassed in Part~C. \\",
                r"MASVS-CRYPTO-2 (key management) & Fail & AES key hard-coded in APK; plaintext recovered via Frida and offline. \\",
                r"MASVS-RESILIENCE-3 (anti-static-analysis) & Fail & jadx produced clear class/method names; no obfuscation. \\",
                r"MASVS-RESILIENCE-4 (anti-dynamic-analysis) & Fail & Frida spawned, hooked Java methods, no anti-instrumentation. \\",
                r"MASVS-STORAGE-1 (secure storage) & Fail & Secret derivable entirely on-client (key+ciphertext in APK / process memory). \\",
                r"\bottomrule",
                r"\end{tabularx}}",
            ]
        )
    )

    body.append(r"\section*{Cleanup}")
    body.append(
        r"\begin{lstlisting}"
        "\n"
        r"adb uninstall owasp.mstg.uncrackable1"
        "\n"
        r"adb shell pkill frida-server"
        "\n"
        r"adb emu kill"
        "\n"
        r"\end{lstlisting}"
    )

    body.append(
        r"\vspace{0.3em}\noindent\textbf{Conclusion.} Root detection raised a dialog, not a security "
        r"boundary. Frida removed the gate; the AES secret was never a secret. Meridian must keep "
        r"authorization and sensitive material on the server (Lab~6.1) and treat MASVS resilience as "
        r"cost, not confidence."
    )
    body.append(r"\end{document}")
    return preamble + "\n".join(body)


def compile_pdf() -> int:
    TEX_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    SUBMIT.mkdir(parents=True, exist_ok=True)

    for name in ("01_root_detected.png", "02_bypassed.png", "04_success.png"):
        src = EV / name
        if src.is_file():
            shutil.copy2(src, FIG_DIR / name)

    TEX_PATH.write_text(build_tex(), encoding="utf-8")

    pdflatex = shutil.which("pdflatex") or str(
        Path(r"C:\Users\unais\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe")
    )
    for pass_no in (1, 2):
        proc = subprocess.run(
            [
                pdflatex,
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-output-directory",
                str(TEX_DIR),
                TEX_PATH.name,
            ],
            cwd=str(TEX_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            print(proc.stdout[-5000:], file=sys.stderr)
            print(proc.stderr[-2000:], file=sys.stderr)
            return proc.returncode
        print(f"pdflatex pass {pass_no} OK")

    built = TEX_DIR / "lab62.pdf"
    shutil.copy2(built, PDF_OUT)
    shutil.copy2(built, SUBMIT_PDF)
    if (SUBMIT / "evidence").exists():
        shutil.rmtree(SUBMIT / "evidence")
    shutil.copytree(EV, SUBMIT / "evidence")
    shutil.copy2(SCRIPT_DIR / "bypass_root.js", SUBMIT / "bypass_root.js")

    pages = "?"
    try:
        import pypdf

        pages = str(len(pypdf.PdfReader(str(PDF_OUT)).pages))
    except Exception:
        pass
    print(f"Wrote: {PDF_OUT}")
    print(f"Pages: {pages}  Size: {PDF_OUT.stat().st_size:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(compile_pdf())
