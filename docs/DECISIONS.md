# Decision Log

## 2026-09-08 - Right-sized service composition

Use one FastAPI process with Cloudflare R2 and Gemini as the two external integrations. Internal microservices, agents, and queues would increase setup and failure surface without improving the bounded review workflow.

## 2026-09-08 - Grounded evidence contract

The model may select immutable evidence IDs but cannot provide authoritative quotation text. The backend validates each selected ID against the retrieved candidates and resolves the displayed text from the extracted source artifact.

## 2026-09-08 - Provider selection

Use Cloudflare R2 Standard storage and Gemini 2.5 Flash-Lite. Both had documented free-tier paths when selected. Keep both behind interfaces so availability changes do not alter the domain flow.

## 2026-09-08 - Live review path

Use a Cloudflare Quick Tunnel for the temporary public review URL. The alternative Sites publisher would require replacing the prescribed Python/Docker runtime with a Worker build, while a container host or named tunnel needs an owner account. The Quick Tunnel proves public reachability without changing the application, but it has no uptime guarantee and is not presented as production hosting.
