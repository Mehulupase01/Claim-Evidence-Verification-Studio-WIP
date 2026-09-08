# API Examples

## Upload a document

```powershell
$document = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/documents `
  -Form @{ file = Get-Item .\samples\sample_report.txt }
$document
```

Successful response:

```json
{
  "document_id": "doc_436b9c2f15fa48f0b3ec615d67c40fa6",
  "filename": "sample_report.txt",
  "content_type": "text/plain",
  "page_count": 1,
  "chunk_count": 1,
  "created_at": "2026-09-08T00:00:00Z"
}
```

## Create a review

```powershell
$body = @{
  document_id = $document.document_id
  claim = 'Revenue increased by 27 percent in the second quarter.'
} | ConvertTo-Json

$review = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/reviews `
  -ContentType application/json `
  -Body $body
$review
```

Successful response:

```json
{
  "review_id": "rev_59d8fa657cbc4dd588a3952df46dc4ac",
  "document_id": "doc_436b9c2f15fa48f0b3ec615d67c40fa6",
  "claim": "Revenue increased by 27 percent in the second quarter.",
  "verdict": "SUPPORTED",
  "reasoning": "The passage directly states the reported year-over-year increase.",
  "evidence": [
    {
      "evidence_id": "chunk_0001",
      "page": 1,
      "text": "The second quarter closed with revenue 27 percent above the same quarter last year.",
      "retrieval_score": 1.084327
    }
  ],
  "model": "gemini/gemini-2.5-flash-lite",
  "created_at": "2026-09-08T00:00:02Z"
}
```

The IDs and timestamps above illustrate the contract; each request creates new values, and the exact reasoning may vary. Evidence text is always resolved from the stored chunk.

## Retrieve the saved review

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/reviews/$($review.review_id)"
```

The returned body must match the created review. Generated OpenAPI documentation is available at `/docs` whenever the app is running.
