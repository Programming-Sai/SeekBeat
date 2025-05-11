Summary of What We've Done (Relevant to Streaming)
Seekbeat Search Module – Finalized Components:

Single & Bulk Search System:

Input: title, artist, lyrics, or direct YouTube link.

Output: structured metadata (title, artist, thumbnail, etc.).

Bulk search supports up to 10 entries with concurrency via httpx.

Link Parsing Logic:

Differentiates between normal, playlist, and "mix" links.

Validates and categorizes YouTube links accordingly.

API Integration:

Currently uses yt-dlp locally for metadata.

Placeholder structure for later switch to hosted API or scraper microservice.

Performance Consideration:

Bulk search with concurrency is functional but slow.

Final decision deferred to production profiling.

Logging System:

Initially set up with rotation per day.

Needs fixing due to logs no longer being written.
