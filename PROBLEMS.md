# Problem Tracker<br><br>
## 📋 Table of Contents<br>
- [Return after metadata branch to prevent double‐streaming](#🆔-014---return-after-metadata-branch-to-prevent-doublestreaming)

- [JSON.stringify needed with Django FormData](#🆔-013---jsonstringify-needed-with-django-formdata)

- [No logging output in Django app](#🆔-012---no-logging-output-in-django-app)

- [Could not enter input in Spectacular API UI](#🆔-011---could-not-enter-input-in-spectacular-api-ui)

- [Sync vs Async Django views](#🆔-010---sync-vs-async-django-views)

- [Inbound rate-limiting per IP](#🆔-009---inbound-rate-limiting-per-ip)

- [Smart fallback between API and scraping](#🆔-008---smart-fallback-between-api-and-scraping)

- [YouTube Data API integration](#🆔-007---youtube-data-api-integration)

- [Concurrency throttling with asyncio.Semaphore](#🆔-006---concurrency-throttling-with-asynciosemaphore)

- [Retry logic with exponential backoff](#🆔-005---retry-logic-with-exponential-backoff)

- [Virtualenv activation on Windows](#🆔-004---virtualenv-activation-on-windows)

- [Streaming metadata results blocking](#🆔-003---streaming-metadata-results-blocking)

- [ Hot Reloading Not Reflecting Changes Immediately](#🆔-002---hot-reloading-not-reflecting-changes-immediately)

- [Unable to Stop Server Using Ctrl+C in IDE Terminal](#🆔-001---unable-to-stop-server-using-ctrlc-in-ide-terminal)

---

---
### 🆔 014 - Return after metadata branch to prevent double‐streaming
<br>**Status:** ✅ Solved

**Language:** Python

**Time Taken:** 10m

### 🐞 Problem Description<br>
Without an early return after streaming the metadata‐injected file, the FFmpeg pipe branch also ran—resulting in the track being sent twice back‐to‐back.

```python
with open(input_src, 'rb') as f: … yield chunk  # but no return here, so FFmpeg stream also runs
```
				
### ✅ Solution Description
<br>
Added return immediately after the metadata file loop so the generator stops before hitting the FFmpeg pipe.

```python
    with open(input_src, 'rb') as f:\n        for chunk in iter(lambda: f.read(8192), b''):\n            yield chunk\n    return
```
				
<br>
<br>

---
### 🆔 013 - JSON.stringify needed with Django FormData
<br>**Status:** ✅ Solved

**Language:** Python

**Time Taken:** 35m

### 🐞 Problem Description<br>
Sending plain objects in FormData to Django without JSON.stringify results in '[object Object]'. Django receives it as a string, not valid JSON.

```python
formData.append('edits', edits)  // causes 'str' object has no attribute 'get'
```
				
### ✅ Solution Description
<br>
Stringified the object before appending. Parsed it safely on Django side with json.loads.

```python
formData.append('edits', JSON.stringify(edits))\n...\nedits_raw = request.data.get('edits', '{}')\nedits = json.loads(edits_raw) if isinstance(edits_raw, str) else edits_raw
```
				
<br>
<br>

---
### 🆔 012 - No logging output in Django app
<br>**Status:** ✅ Solved

**Language:** Python

**Time Taken:** 25m

### 🐞 Problem Description<br>
Logging stopped appearing after working the first few days. Thought it was broken.

### ✅ Solution Description
<br>
The active log file was seekbeat.log and not the dated rotated files like seekbeat.log.2025-05-10. I was checking the wrong file.

<br>
<br>

---
### 🆔 011 - Could not enter input in Spectacular API UI
<br>**Status:** ✅ Solved

**Language:** Python

**Time Taken:** 5m

### 🐞 Problem Description<br>
Swagger UI section for testing endpoints appeared read-only. Thought manual config was needed to enable input.

### ✅ Solution Description
<br>
Realized I needed to click the 'Try it out' button to enable editing and input.

<br>
<br>

---
### 🆔 010 - Sync vs Async Django views
<br>**Status:** ✅ Solved

**Language:** Python

**Time Taken:** 40m

### 🐞 Problem Description<br>
async def views with ratelimit caused unawaited coroutine under WSGI, Django expected sync views.

```python
async def search_view(request):\n    result = await engine.regular_search(...)
```
				
### ✅ Solution Description
<br>
Changed to regular def views and wrapped async calls with async_to_sync().

```python
def search_view(request):\n    result = async_to_sync(engine.regular_search)(query)\n    return JsonResponse(...)
```
				
<br>
<br>

---
### 🆔 009 - Inbound rate-limiting per IP
<br>**Status:** ✅ Solved

**Language:** Python

**Time Taken:** 20m

### 🐞 Problem Description<br>
Needed to throttle clients; initial high limits made testing impractical.

```python
@ratelimit(key='ip', rate='25/m', block=True) def search_view(...)
```
				
### ✅ Solution Description
<br>
Applied django-ratelimit decorators with a test-friendly rate (e.g. 2/m), verified via 429 responses.

```python
@ratelimit(key='ip', rate='2/m', block=True) def search_view(request): ...
```
				
<br>
<br>

---
### 🆔 008 - Smart fallback between API and scraping
<br>**Status:** ✅ Solved

**Language:** Python

**Time Taken:** 30m

### 🐞 Problem Description<br>
When API quotas were exceeded or calls failed, there was no fallback, causing search failures.

```python
response = await self._retry_request(...)  # no fallback on quota errors
```
				
### ✅ Solution Description
<br>
Detected quota errors in retry logic; on single search fallback to yt-dlp, on bulk return clear API-down error.

```python
except Exception:
    return await self.regular_search(search_term)  # fallback to yt-dlp
```
				
<br>
<br>

---
### 🆔 007 - YouTube Data API integration
<br>**Status:** ✅ Solved

**Language:** Python

**Time Taken:** 1h

### 🐞 Problem Description<br>
yt-dlp scraping was too slow; needed faster metadata with pagination and quotas.

```python
result = await asyncio.to_thread(self._execute_search, query)  # slow scraping
```
				
### ✅ Solution Description
<br>
Added egular_search_with_yt_api() calling YouTube Search & Videos APIs in parallel, cleaned entries.

```python
response = await asyncio.to_thread(requests.get, url, params)
cleaned_entries.append({...})
```
				
<br>
<br>

---
### 🆔 006 - Concurrency throttling with asyncio.Semaphore
<br>**Status:** ✅ Solved

**Language:** Python

**Time Taken:** 30m

### 🐞 Problem Description<br>
Bulk searches spawned unlimited concurrent tasks and semaphore was bound to wrong event loop, causing errors.

```python
self._sem = asyncio.Semaphore(...); tasks = [asyncio.create_task(self._wrapped_search(term)) for term in terms]
```
				
### ✅ Solution Description
<br>
Initialized Semaphore in __init__ and wrapped each bulk task in sync with self._sem to limit concurrency.

```python
async def sem_wrapped(term):
    async with self._sem:
        return await self._wrapped_search(term)
```
				
<br>
<br>

---
### 🆔 005 - Retry logic with exponential backoff
<br>**Status:** ✅ Solved

**Language:** Python

**Time Taken:** 45m

### 🐞 Problem Description<br>
Search calls failed intermittently with DNS or rate-limit errors and had no retry policy.

```python
for attempt in range(2):
    result = await asyncio.to_thread(...)  # no backoff
```
				
### ✅ Solution Description
<br>
Introduced configurable retries and exponential backoff with jitter before each retry.

```python
for attempt in range(self.retries):
    try:
        ...
    except Exception:
        await asyncio.sleep(min(2**attempt + random.uniform(0,1),10))
```
				
<br>
<br>

---
### 🆔 004 - Virtualenv activation on Windows
<br>**Status:** ✅ Solved

**Language:** Python

**Time Taken:** 20m

### 🐞 Problem Description<br>
Windows venv activation wasn’t working; pip freeze showed global packages instead of project-specific ones.

```python
C:\\> .seek-venv/Scripts/activate
(.seek-venv) C:\\> pip freeze  # still global packages
```
				
### ✅ Solution Description
<br>
Used the correct PowerShell activation script and reinstalled dependencies into the venv.

```python
. .\\.seek-venv\\Scripts\\Activate.ps1
(.seek-venv) C:\\> pip freeze  # now shows project deps
```
				
<br>
<br>

---
### 🆔 003 - Streaming metadata results blocking
<br>**Status:** ✅ Solved

**Language:** Python

**Time Taken:** 30m

### 🐞 Problem Description<br>
Attempted to yield individual yt-dlp.extract_info() entries to stream results as they arrive, but yt-dlp buffers and returns the full batch at once.

```python
async def regular_search(...):
    for entry in cleaned_entries:
        yield entry
```
				
### ✅ Solution Description
<br>
Abandoned live streaming; collect full list and return it in one response.

```python
return cleaned_entries
```
				
<br>
<br>

---
### 🆔 002 -  Hot Reloading Not Reflecting Changes Immediately
<br>**Status:** ✅ Solved

**Language:** Python

**Time Taken:** 6

### 🐞 Problem Description<br>
 Code changes were not being reflected in the server output immediately during development. This was likely due to the hot-reloading process not being triggered or not functioning properly. The server needed to be manually restarted each time for the changes to take effect.

### ✅ Solution Description
<br>
 Running the server in a separate command line window (CMD) and manually restarting it after each change resolved the issue. This ensured that all updates were properly applied during testing.

<br>
<br>

---
### 🆔 001 - Unable to Stop Server Using Ctrl+C in IDE Terminal
<br>**Status:** ✅ Solved

**Language:** Python

**Time Taken:** 20

### 🐞 Problem Description<br>
The terminal in the IDE (VS Code) was not responding to the usual Ctrl+C command to stop the server. Instead, it required Ctrl+Break, a key that was unavailable on the user’s keyboard. This prevented proper server termination and manual control.

### ✅ Solution Description
<br>
Switching to the system's command line (CMD) allowed proper use of Ctrl+C, enabling server stop functionality as expected.

<br>
<br>
