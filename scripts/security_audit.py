import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "Google API key": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    "AWS-style access key": re.compile(r"(?:AKIA|ASIA)[0-9A-Z]{16}"),
    "credential in URL": re.compile(r"https?://[^\s/:]+:[^\s/@]+@"),
}
ASSIGNMENT = re.compile(
    r"(?m)^\s*[A-Z0-9_]*(?:API_KEY|ACCESS_KEY_ID|SECRET_ACCESS_KEY|AUTH_TOKEN|PASSWORD)\s*=\s*([^\s#]+)"
)
ALLOWED_VALUES = {"", "replace_me", "placeholder", "unit_test_placeholder"}


def git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout


def scan_text(label: str, text: str) -> list[str]:
    findings = [name for name, pattern in SECRET_PATTERNS.items() if pattern.search(text)]
    for match in ASSIGNMENT.finditer(text):
        value = match.group(1).strip("'\"")
        if value not in ALLOWED_VALUES and "<" not in value:
            findings.append(f"credential-like assignment in {label}")
    return findings


def main() -> None:
    tracked = [line for line in git("ls-files").splitlines() if line]
    untracked = [
        line
        for line in git("ls-files", "--others", "--exclude-standard").splitlines()
        if line
    ]
    files_to_scan = sorted(set(tracked + untracked))
    forbidden_names = [
        name for name in tracked if Path(name).name == ".env" or name.endswith("/.env")
    ]
    findings = [f"tracked environment file: {name}" for name in forbidden_names]

    for name in files_to_scan:
        path = ROOT / name
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        findings.extend(f"{name}: {item}" for item in scan_text(name, text))

    history = git("log", "-p", "--all", "--", ":!LICENSE")
    findings.extend(f"Git history: {item}" for item in scan_text("history", history))

    if findings:
        print("Secret audit failed:")
        for finding in sorted(set(findings)):
            print(f"- {finding}")
        raise SystemExit(1)
    print(
        f"PASS scanned {len(tracked)} tracked and {len(untracked)} untracked files plus Git patch history"
    )


if __name__ == "__main__":
    main()
