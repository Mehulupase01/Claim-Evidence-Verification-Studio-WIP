import argparse
import json
from urllib.request import Request, urlopen


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-check a deployed verifier.")
    parser.add_argument("base_url", help="Public origin, for example https://name.trycloudflare.com")
    args = parser.parse_args()

    url = f"{args.base_url.rstrip('/')}/health"
    request = Request(url, headers={"X-Request-ID": "deployment-smoke-check"})
    with urlopen(request, timeout=15) as response:
        payload = json.load(response)
        request_id = response.headers.get("X-Request-ID")
        if response.status != 200 or payload != {"status": "ok"}:
            raise SystemExit(f"Unexpected health response: {response.status} {payload}")
        if request_id != "deployment-smoke-check":
            raise SystemExit("The deployment did not preserve the request ID header.")
    print(f"PASS {url} returned 200 with the expected body and request ID")


if __name__ == "__main__":
    main()
