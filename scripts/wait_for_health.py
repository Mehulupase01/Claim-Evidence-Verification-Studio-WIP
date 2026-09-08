import json
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/wait_for_health.py <health-url>")
    url = sys.argv[1]
    last_error = "no response"
    for _ in range(30):
        try:
            with urlopen(url, timeout=2) as response:
                payload = json.load(response)
                if response.status == 200 and payload == {"status": "ok"}:
                    print(f"PASS {url} is healthy")
                    return
                last_error = f"unexpected response {response.status}: {payload}"
        except (URLError, TimeoutError, ValueError) as exc:
            last_error = type(exc).__name__
        time.sleep(1)
    raise SystemExit(f"Health check failed after 30 seconds: {last_error}")


if __name__ == "__main__":
    main()
