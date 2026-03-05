# API Contract: Knowledge Endpoints

---

## GET /knowledge/search

Search the knowledge base by keyword.

**Query parameters**:
- `q` (string, required): Search query text

**Response** `200 OK`:
```json
{
  "query": "understeer causes",
  "results": [
    {
      "source_file": "balance-handling.md",
      "section_title": "Causes of Understeer",
      "content": "Understeer occurs when the front tyres lose grip before the rears...",
      "tags": ["understeer", "balance", "front-grip"]
    }
  ],
  "total": 15
}
```

**Behavior**:
- Results are ranked by relevance (match count descending)
- Maximum 10 results returned; `total` reflects full match count before cap
- Empty or whitespace-only `q` returns `{"query": "", "results": [], "total": 0}`
- No matches returns `{"query": "xyznonexistent", "results": [], "total": 0}`
- This endpoint never returns an error status for valid requests

---

## GET /sessions/{session_id}/knowledge

Retrieve knowledge fragments relevant to an analyzed session's detected signals.

**Path parameters**:
- `session_id` (string): The session identifier

**Response** `200 OK`:
```json
{
  "session_id": "2026-03-01_monza_rss_formula_hybrid",
  "signals": ["high_understeer", "tyre_temp_spread_high"],
  "fragments": [
    {
      "source_file": "balance-handling.md",
      "section_title": "Causes of Understeer",
      "content": "Understeer occurs when...",
      "tags": ["understeer", "balance"]
    },
    {
      "source_file": "tyre-management.md",
      "section_title": "Temperature Spread",
      "content": "When the inner/outer temperature spread...",
      "tags": ["tyres", "temperature", "camber"]
    }
  ]
}
```

**Error** `404 Not Found` — session does not exist:
```json
{
  "detail": "Session not found: nonexistent_session"
}
```

**Error** `409 Conflict` — session not yet analyzed:
```json
{
  "detail": "Session has not been analyzed yet. Current state: discovered. Process the session first."
}
```

**Error** `409 Conflict` — analysis cache missing:
```json
{
  "detail": "Cached results are corrupted or missing — re-process the session"
}
```

**Behavior**:
- Accepts sessions in "analyzed" or "engineered" state
- Signals are detected by running `detect_signals()` on the cached AnalyzedSession
- Fragments are the knowledge base sections mapped to those signals
- If no signals are detected, returns empty signals and fragments lists
