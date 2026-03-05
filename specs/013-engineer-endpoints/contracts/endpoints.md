# API Contract: Engineer Endpoints

All endpoints are prefixed with `/sessions` (applied via router registration in main.py).

## POST /sessions/{session_id}/engineer

Trigger the AI engineer pipeline as a background job.

**Request**: No body required.

**Response 202**:
```json
{
  "job_id": "abc123",
  "session_id": "session-2026-03-05-12-00-00"
}
```

**Error 404**: Session not found.
**Error 409**: Session not analyzed yet (state must be "analyzed" or "engineered").
**Error 409**: Engineer job already running for this session.

---

## GET /sessions/{session_id}/recommendations

List all recommendations for a session.

**Response 200**:
```json
{
  "session_id": "session-2026-03-05-12-00-00",
  "recommendations": [
    {
      "recommendation_id": "a1b2c3d4",
      "session_id": "session-2026-03-05-12-00-00",
      "status": "proposed",
      "summary": "Reduce front ARB to address understeer in turns 3 and 7.",
      "change_count": 2,
      "created_at": "2026-03-05T12:05:00+00:00"
    }
  ]
}
```

**Error 404**: Session not found.

---

## GET /sessions/{session_id}/recommendations/{recommendation_id}

Get full detail for a specific recommendation.

**Response 200**:
```json
{
  "recommendation_id": "a1b2c3d4",
  "session_id": "session-2026-03-05-12-00-00",
  "status": "proposed",
  "summary": "Reduce front ARB to address understeer in turns 3 and 7.",
  "explanation": "Your telemetry shows consistent understeer in medium-speed corners...",
  "confidence": "high",
  "signals_addressed": ["high_understeer", "tyre_temp_imbalance"],
  "setup_changes": [
    {
      "section": "ARB",
      "parameter": "FRONT",
      "old_value": "5",
      "new_value": "3",
      "reasoning": "Reducing front ARB allows more front-end grip in mid-corner.",
      "expected_effect": "Less understeer in turns 3 and 7, improved corner exit speed.",
      "confidence": "high"
    }
  ],
  "driver_feedback": [
    {
      "area": "braking",
      "observation": "Trail braking intensity is low in turns 3 and 7.",
      "suggestion": "Try maintaining light brake pressure past turn-in to rotate the car.",
      "corners_affected": [3, 7],
      "severity": "medium"
    }
  ],
  "created_at": "2026-03-05T12:05:00+00:00"
}
```

**Error 404**: Session or recommendation not found.

---

## POST /sessions/{session_id}/recommendations/{recommendation_id}/apply

Apply a recommendation's setup changes to a .ini file.

**Request**:
```json
{
  "setup_path": "C:/Program Files/Steam/steamapps/common/assettocorsa/content/cars/ks_ferrari_488/setups/monza/my_setup.ini"
}
```

**Response 200**:
```json
{
  "recommendation_id": "a1b2c3d4",
  "status": "applied",
  "backup_path": "C:/.../my_setup_2026-03-05_120500.ini",
  "changes_applied": 2
}
```

**Error 404**: Session or recommendation not found.
**Error 409**: Recommendation already applied.
**Error 400**: Setup file not found at specified path.

---

## GET /sessions/{session_id}/messages

Get conversation history for a session.

**Response 200**:
```json
{
  "session_id": "session-2026-03-05-12-00-00",
  "messages": [
    {
      "message_id": "msg-001",
      "role": "user",
      "content": "Why do you recommend reducing front ARB?",
      "created_at": "2026-03-05T12:10:00+00:00"
    },
    {
      "message_id": "msg-002",
      "role": "assistant",
      "content": "Your telemetry shows consistent understeer through turns 3 and 7...",
      "created_at": "2026-03-05T12:10:05+00:00"
    }
  ]
}
```

**Error 404**: Session not found.

---

## POST /sessions/{session_id}/messages

Send a chat message and trigger an AI response.

**Request**:
```json
{
  "content": "Why do you recommend reducing front ARB?"
}
```

**Response 202**:
```json
{
  "job_id": "def456",
  "message_id": "msg-001"
}
```

**Error 404**: Session not found.
**Error 409**: Session not analyzed yet.

---

## DELETE /sessions/{session_id}/messages

Clear all conversation history for a session.

**Response 200**:
```json
{
  "session_id": "session-2026-03-05-12-00-00",
  "deleted_count": 5
}
```

**Error 404**: Session not found.
