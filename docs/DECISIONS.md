# Decision Log

## 2026-09-08 - Right-sized service composition

Use one FastAPI process with Cloudflare R2 and Gemini as the two external integrations. Internal microservices, agents, and queues would increase setup and failure surface without improving the bounded review workflow.

## 2026-09-08 - Grounded evidence contract

The model may select immutable evidence IDs but cannot provide authoritative quotation text. The backend validates each selected ID against the retrieved candidates and resolves the displayed text from the extracted source artifact.

## 2026-09-08 - Provider selection

Use Cloudflare R2 Standard storage and Gemini Flash-Lite. The master plan selected Gemini 2.5 Flash-Lite, but the real release smoke test returned Google's new-project retirement response and directed the application to Gemini 3.5 Flash-Lite. The replacement is GA, supports structured output, and retains a documented free tier. Keeping the provider behind an interface made the lifecycle update a configuration change rather than a domain rewrite.

## 2026-09-08 - Live review path

Use a Cloudflare Quick Tunnel for the temporary public review URL. The alternative Sites publisher would require replacing the prescribed Python/Docker runtime with a Worker build, while a container host or named tunnel needs an owner account. The Quick Tunnel proves public reachability without changing the application, but it has no uptime guarantee and is not presented as production hosting.
