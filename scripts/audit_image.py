import json
import re
import subprocess
import sys


SENSITIVE_VALUE_PATTERNS = {
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "Google API key": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    "AWS-style access key": re.compile(r"(?:AKIA|ASIA)[0-9A-Z]{16}"),
    "credential in URL": re.compile(r"https?://[^\s/:]+:[^\s/@]+@"),
}


def docker(*arguments: str) -> str:
    return subprocess.run(
        ["docker", *arguments],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/audit_image.py <image-tag>")
    image = sys.argv[1]
    inspect_output = docker("image", "inspect", image)
    history_output = docker("history", "--no-trunc", image)
    combined = inspect_output + "\n" + history_output

    findings = [
        name for name, pattern in SENSITIVE_VALUE_PATTERNS.items() if pattern.search(combined)
    ]
    configuration = json.loads(inspect_output)[0].get("Config", {})
    environment = configuration.get("Env") or []
    forbidden_names = (
        "API_KEY=",
        "ACCESS_KEY_ID=",
        "SECRET_ACCESS_KEY=",
        "AUTH_TOKEN=",
        "PASSWORD=",
    )
    for entry in environment:
        if any(name in entry.upper() for name in forbidden_names):
            findings.append(
                f"credential-shaped image environment entry: {entry.split('=', 1)[0]}"
            )

    if findings:
        print("Image audit failed:")
        for finding in sorted(set(findings)):
            print(f"- {finding}")
        raise SystemExit(1)
    print(f"PASS image {image} has no credential-shaped metadata, environment, or history")


if __name__ == "__main__":
    main()
