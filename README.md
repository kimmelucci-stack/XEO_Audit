# XEO Audit

Python tool for running a deterministic technical SEO and performance audit for
a public website.

## Setup

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Optional Google API key for CrUX and PageSpeed Insights:

```powershell
$env:GOOGLE_API_KEY="your-api-key"
```

`PAGESPEED_API_KEY` is also supported as a fallback environment variable.

## Run

```powershell
.\.venv\Scripts\python.exe main.py --url https://example.com --device mobile
```

JSON output:

```powershell
.\.venv\Scripts\python.exe main.py --url https://example.com --format json
```

Limit action-plan recommendations:

```powershell
.\.venv\Scripts\python.exe main.py --url https://example.com --recommendation-limit 5
```

Reports are written to the audited site's directory under `data/` unless
`--output` is provided.

Each report includes crawl evidence, deterministic scoring, a severity summary,
and an action plan that groups related findings into prioritized recommendations.

## Web Demo

Run the local demo frontend and API:

```powershell
.\.venv\Scripts\python.exe web_demo_server.py
```

Open `http://127.0.0.1:8080`, submit a URL, and use the report's print action
to save the HTML report as a PDF.

The demo uses a smaller crawl sample and limited recommendations so it behaves
like a fast public product demo. `vercel.json` and `api/audit.py` provide a
minimal Vercel-oriented deployment shape for the same experience.

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The live-site collector test may depend on network access and the remote site's
current behavior.
