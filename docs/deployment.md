# Deployment

## Current review endpoint

The temporary review endpoint created on 8 September 2026 is:

**https://hose-defendant-correctly-priorities.trycloudflare.com**

The root workspace and `/health` were both verified through Cloudflare. This is an account-less Quick Tunnel: the URL lasts only while the local application and `cloudflared` process remain running, and Cloudflare does not provide an uptime guarantee. It is suitable for a scheduled review window, not unattended production service.

The public upload-to-verdict flow has not been run because this machine does not contain the owner's R2 or Gemini credentials. The application returns a safe configuration error instead of silently substituting local storage or a fake model.

## Start the application

1. Copy `.env.example` to `.env` and replace only the placeholder values.
2. Start Docker Desktop.
3. From the repository root, run the project's one start command:

   ```powershell
   docker compose up --build
   ```

4. Wait for the app service to become healthy at `http://localhost:8000/health`.

The `PORT` value in `.env` changes the host-side port. The application remains on port 8000 inside Compose.

## Open a free temporary tunnel

Install Cloudflare's `cloudflared` package once if it is not already present:

```powershell
winget install --id Cloudflare.cloudflared --exact
```

With the application running, open a second terminal and run:

```powershell
.\scripts\start-tunnel.ps1 -Port 8000
```

The command prints a random `trycloudflare.com` URL. Keep both processes running, verify the new URL, and replace the temporary URL in the README before sending the project to a reviewer.

```powershell
uv run python scripts/verify_deployment.py https://your-tunnel.trycloudflare.com
```

## Longer-lived review deployment

For an unattended review window, use a named Cloudflare Tunnel or a container host that accepts runtime environment variables. Keep the same image and `python -m app` entrypoint. Configure every value from `.env.example` in the host's secret settings, expose the host-provided port, and run the same `/health` and end-to-end checks. Do not put keys in a platform manifest, image build argument, repository variable, or command transcript.

## Operational limits

- Quick Tunnels have no uptime commitment and can change URL after restart.
- The application has no authentication by design; expose it only for the review window.
- Host and provider free tiers can sleep, throttle, or change limits.
- A successful public health check proves reachability, not the R2 and Gemini integrations. Run the credential-gated smoke tests and one real review before submission.
