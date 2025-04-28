# Problem Tracker

## Table of Contents
- [Unable to Stop Server Using Ctrl+C in IDE Terminal](#001)
- [ Hot Reloading Not Reflecting Changes Immediately](#002)
- [Streaming metadata results blocking](#003)
- [Virtualenv activation on Windows](#004)
- [Retry logic with exponential backoff](#005)
- [Concurrency throttling with asyncio.Semaphore](#006)
- [YouTube Data API integration](#007)
- [Smart fallback between API and scraping](#008)
- [Inbound rate-limiting per IP](#009)
- [Sync vs Async Django views](#010)

---
---
---
---

---
#### 001
`solved`
## Unable to Stop Server Using Ctrl+C in IDE Terminal
The terminal in the IDE (VS Code) was not responding to the usual Ctrl+C command to stop the server. Instead, it required Ctrl+Break, a key that was unavailable on the user’s keyboard. This prevented proper server termination and manual control.

<br><br>
Switching to the system's command line (CMD) allowed proper use of Ctrl+C, enabling server stop functionality as expected.

20

---

---
#### 002
`solved`
##  Hot Reloading Not Reflecting Changes Immediately
 Code changes were not being reflected in the server output immediately during development. This was likely due to the hot-reloading process not being triggered or not functioning properly. The server needed to be manually restarted each time for the changes to take effect.

<br><br>
 Running the server in a separate command line window (CMD) and manually restarting it after each change resolved the issue. This ensured that all updates were properly applied during testing.

6

---

---
#### 003
`solved`
## Streaming metadata results blocking
Attempted to yield individual yt-dlp.extract_info() entries to stream results as they arrive, but yt-dlp buffers and returns the full batch at once.

```python
async def regular_search(...):
    for entry in cleaned_entries:
        yield entry
```
				
<br><br>
Abandoned live streaming; collect full list and return it in one response.

```python
return cleaned_entries
```
				
30m

---

---
#### 004
`solved`
## Virtualenv activation on Windows
Windows venv activation wasn’t working; pip freeze showed global packages instead of project-specific ones.

```python
C:\\> .seek-venv/Scripts/activate
(.seek-venv) C:\\> pip freeze  # still global packages
```
				
<br><br>
Used the correct PowerShell activation script and reinstalled dependencies into the venv.

```python
. .\\.seek-venv\\Scripts\\Activate.ps1
(.seek-venv) C:\\> pip freeze  # now shows project deps
```
				
20m

---

---
#### 005
`solved`
## Retry logic with exponential backoff
Search calls failed intermittently with DNS or rate-limit errors and had no retry policy.

```python
for attempt in range(2):
    result = await asyncio.to_thread(...)  # no backoff
```
				
<br><br>
Introduced configurable retries and exponential backoff with jitter before each retry.

```python
for attempt in range(self.retries):
    try:
        ...
    except Exception:
        await asyncio.sleep(min(2**attempt + random.uniform(0,1),10))
```
				
45m

---

---
#### 006
`solved`
## Concurrency throttling with asyncio.Semaphore
Bulk searches spawned unlimited concurrent tasks and semaphore was bound to wrong event loop, causing errors.

```python
self._sem = asyncio.Semaphore(...); tasks = [asyncio.create_task(self._wrapped_search(term)) for term in terms]
```
				
<br><br>
Initialized Semaphore in __init__ and wrapped each bulk task in sync with self._sem to limit concurrency.

```python
async def sem_wrapped(term):
    async with self._sem:
        return await self._wrapped_search(term)
```
				
30m

---

---
#### 007
`solved`
## YouTube Data API integration
yt-dlp scraping was too slow; needed faster metadata with pagination and quotas.

```python
result = await asyncio.to_thread(self._execute_search, query)  # slow scraping
```
				
<br><br>
Added egular_search_with_yt_api() calling YouTube Search & Videos APIs in parallel, cleaned entries.

```python
response = await asyncio.to_thread(requests.get, url, params)
cleaned_entries.append({...})
```
				
1h

---

---
#### 008
`solved`
## Smart fallback between API and scraping
When API quotas were exceeded or calls failed, there was no fallback, causing search failures.

```python
response = await self._retry_request(...)  # no fallback on quota errors
```
				
<br><br>
Detected quota errors in retry logic; on single search fallback to yt-dlp, on bulk return clear API-down error.

```python
except Exception:
    return await self.regular_search(search_term)  # fallback to yt-dlp
```
				
30m

---

---
#### 009
`solved`
## Inbound rate-limiting per IP
Needed to throttle clients; initial high limits made testing impractical.

```python
@ratelimit(key='ip', rate='25/m', block=True) def search_view(...)
```
				
<br><br>
Applied django-ratelimit decorators with a test-friendly rate (e.g. 2/m), verified via 429 responses.

```python
@ratelimit(key='ip', rate='2/m', block=True) def search_view(request): ...
```
				
20m

---

---
#### 010
`solved`
## Sync vs Async Django views
async def views with ratelimit caused unawaited coroutine under WSGI, Django expected sync views.

```python
async def search_view(request):\n    result = await engine.regular_search(...)
```
				
<br><br>
Changed to regular def views and wrapped async calls with async_to_sync().

```python
def search_view(request):\n    result = async_to_sync(engine.regular_search)(query)\n    return JsonResponse(...)
```
				
40m

---
