# 🎯 Sales Best Friend - Архитектура

## 1. 🔧 Что технически под капотом

### Stack

```
┌─────────────────────────────────────┬─────────────────────────────────┐
│ FRONTEND (React/Vite/TypeScript)    │ BACKEND (FastAPI/Python)        │
├─────────────────────────────────────┼─────────────────────────────────┤
│                                     │                                 │
│  Web Audio API                      │  AudioBuffer                    │
│  (16kHz mono Int16 PCM)             │  (accumulate 5s of data)        │
│         ↓                           │         ↓                       │
│  WebSocket /ingest                  │  faster-whisper                 │
│  (send PCM chunks)                  │  (speech-to-text, multi-lang)   │
│                                     │         ↓                       │
│  WebSocket /coach ←─────────────────┼─────────────────────────────────┤
│  (receive JSON updates)             │                                 │
│         ↓                           │  Parallel Processing:           │
│  React components                   │  ├─ LLMAnalyzer                 │
│  - InCallAssist card                │  │  (Claude 3 Haiku via         │
│  - ClientInfoSummary                │  │   OpenRouter API)            │
│  - CallChecklist                    │  │                              │
│                                     │  ├─ IntentDetector              │
│                                     │  │  (playbook.json matching)    │
│                                     │  │                              │
│                                     │  └─ Checklist validator         │
│                                     │     (LLM-based semantic check)  │
└─────────────────────────────────────┴─────────────────────────────────┘
```

### Цикл обновления (каждые 5 сек)

```
1. Frontend: Audio buffer accumulates PCM chunks (Web Audio API)
   └─ 8KB chunks from ScriptProcessorNode

2. Backend: AudioBuffer triggers when ready
   └─ 163KB buffer = 5 sec of audio at 16kHz

3. Transcription: faster-whisper converts PCM → text
   └─ Language: configurable (en, id, ru, etc.)

4. Parallel LLM processing:
   ├─ LLMAnalyzer.analyze_client_sentiment()
   │  └─ Extract: emotion, objections, interests, needs, stage
   ├─ IntentDetector.detect_trigger()
   │  └─ Match keywords against playbook (25 triggers)
   └─ Checklist validator
      └─ LLMAnalyzer.check_checklist_item_semantic()

5. Send JSON via /coach WebSocket to all connected clients
   └─ Rate-limited to 1 update/sec on frontend

6. Frontend: React re-renders components
   └─ InCallAssist card (if trigger), ClientInfoSummary, CallChecklist
```

---

## 2. 📍 In-Call Assist (карточка с подсказками)

### Flow

```
User speaks: "It's too expensive"
        ↓
Transcript received in backend
        ↓
IntentDetector.detect_trigger(transcript)
        ↓
Keyword matching against playbook:
  - Text: "it's too expensive"
  - Check each trigger in playbook
  - Match: "expensive" ∈ price_objection.match[]
        ↓
Priority-based selection:
  - price_objection: priority=10 (highest wins)
        ↓
Anti-spam cooldown (30s):
  - Skip if same trigger active
  - Skip if last trigger < 30s ago
        ↓
Send via WebSocket:
{
  "assist_trigger": {
    "id": "price_objection",
    "title": "💰 Client says it's too expensive",
    "hint": "Emphasize value, not price. Share success stories and offer a free intro lesson.",
    "priority": 10
  }
}
        ↓
Frontend: InCallAssist component
  - Fade in
  - Display for 10 seconds
  - Auto-dismiss (or manual close)
  - Only one card active at a time
```

### Playbook структура (playbook.json)

```json
[
  {
    "id": "price_objection",
    "match": ["дорого", "цена", "expensive", "costly", "mahal", "harga"],
    "title": "💰 Client says it's too expensive",
    "hint": "Emphasize value, not price. Share success stories and offer a free intro lesson.",
    "priority": 10
  },
  ...
]
```

**Логика:** keyword regex matching → priority selection → anti-spam cooldown (30s) → one active card

---

## 3. 👤 Key Client Information

### Flow

```
Transcript: "I'm hesitant. It's too expensive. But the game-based learning sounds fun."
        ↓
LLMAnalyzer.analyze_client_sentiment(client_text, full_context)
        ↓
Claude prompt:
  - Extract emotion: engaged|curious|hesitant|defensive|negative|neutral
  - Extract objections: [list of concerns]
  - Extract interests: [list of topics they like]
  - Extract needs: [core pain point]
  - Extract engagement_level: 0.0–1.0
  - Extract stage_hint: greeting|profiling|presentation|objection|closing
        ↓
Parse JSON response:
{
  "emotion": "hesitant",
  "objections": ["price"],
  "interests": ["game-based learning"],
  "needs": "Affordable solution that engages child",
  "engagement_level": 0.7,
  "stage_hint": "objection",
  "buying_signals": [],
  "reasoning": "Client is hesitant but interested in game-based learning..."
}
        ↓
Send via /coach WebSocket:
{
  "client_insight": {...}
}
        ↓
Frontend: ClientInfoSummary component
  - Display objections (red)
  - Display interests (blue)
  - Display needs (yellow)
  - Display emotion (emoji)
  - Update in real-time
```

### Guard clauses (для точности)

```python
# If text too short → return neutral analysis (skip processing)
if len(client_text.strip()) < 20:
    return {emotion: "neutral", objections: [], ...}

# If LLM confidence too low → skip item
if llm_confidence < 0.8:
    return False (don't mark checklist item)
```

**Логика:** LLM semantic analysis → JSON parsing → cache results → broadcast via WebSocket

---

## 4. 📋 Call Progress Checklist

### Flow

```
Accumulated transcript: "Hi, I'm John. We help kids learn coding..."
        ↓
For each uncompleted checklist item in the active stage:
        ├─ if item.completed == True:
        │  └─ SKIP (permanent, never re-check)
        │
        ├─ if item.id in checklist_completion_cache:
        │  └─ if last_check_time < 30s ago:
        │     └─ SKIP (cooldown)
        │
        └─ else: Call LLMAnalyzer.check_checklist_item_semantic()
        ↓
Claude prompt:
  "Is this sales action done?
   Item: 'Introduce yourself and company'
   Conversation: [last 2000 chars of transcript]
   Your answer: {completed: true/false, confidence: 0.0-1.0, evidence: '...'}"
        ↓
Parse response:
{
  "completed": true,
  "confidence": 0.95,
  "evidence": "Hi, I'm John from SalesBestFriend. We help kids learn coding..."
}
        ↓
Validation:
  - If confidence < 0.8 → reject
  - If completed + confidence >= threshold:
    └─ Mark item complete
    └─ Store evidence (last 2 sentences)
    └─ Store in checklist_evidence cache
    └─ Update checklist_completion_cache
        ↓
Send via /coach WebSocket:
{
  "checklist_progress": {
    "greeting": {
      "intro_yourself": {
        "completed": true,
        "evidence": "Hi, I'm John from SalesBestFriend..."
      }
    }
  }
}
        ↓
Frontend: CallChecklist component
  - Mark item ✅
  - Add "📋 Details" button
  - Modal shows evidence on click
```

### Caching strategy

```
Three levels of caching:

1. checklist_completion_cache: Dict[str, float]
   - Store timestamp of last check
   - Skip if checked < 30s ago

2. checklist_llm_cache: Dict[str, Dict]
   - Store LLM response for 60 seconds
   - Reuse for repeated checks

3. Permanent completion cache
   - Once item.completed = True
   - Never re-check (save LLM calls)
```

**Логика:** permanent completion → 30s check cooldown → LLM semantic validation (0.8+ confidence) → evidence extraction

---

## 5. 🔄 Полный цикл обновления

```
┌─────────────────────────────────────────────────────────────────┐
│ Every 5 seconds (from buffer ready):                            │
└─────────────────────────────────────────────────────────────────┘

Step 1: Transcription
  Audio Buffer (163KB) → faster-whisper → transcript string

Step 2: Speaker identification (if LLM enabled)
  transcript → LLMAnalyzer.identify_speakers() → client_text

Step 3: Client sentiment analysis
  client_text → LLMAnalyzer.analyze_client_sentiment()
  └─ Result: emotion, objections, interests, needs, engagement

Step 4: Trigger detection (In-Call Assist)
  transcript → IntentDetector.detect_trigger()
  └─ Match: keywords vs playbook
  └─ Result: {id, title, hint, priority} or None
  └─ Anti-spam: skip if same trigger active + < 30s

Step 5: Checklist validation
  For each uncompleted item:
    ├─ Skip if completed (permanent)
    ├─ Skip if checked < 30s ago
    └─ LLMAnalyzer.check_checklist_item_semantic()
        └─ Store evidence in checklist_evidence

Step 6: Stage detection
  transcript → detect_stage_from_text()
  └─ Result: greeting | profiling | presentation | objection | closing

Step 7: Broadcast via WebSocket
  Send JSON to all /coach clients:
  {
    "hint": "...",                        # from coach recommendation
    "prob": 0.8,                          # probability score
    "client_insight": {...},              # from LLM analysis
    "checklist_progress": {...},          # completion status
    "checklist_evidence": {...},          # text proof
    "current_stage": "objection",
    "next_step": "Address price objection...",
    "assist_trigger": {...} or null       # from IntentDetector
  }

Step 8: Frontend rate-limiting
  React hook: useEffect throttle (1 update/sec max)
  └─ InCallAssist card updates
  └─ ClientInfoSummary updates
  └─ CallChecklist updates
```

---

## 6. 📊 Data Models

### CoachMessage (WebSocket /coach)

```typescript
interface CoachMessage {
  hint: string;                           // Sales coaching hint
  prob: number;                           // 0.0–1.0 probability
  client_insight: {
    emotion: string;
    objections: string[];
    interests: string[];
    needs: string | null;
    engagement_level: number;
    stage_hint: string;
    buying_signals: string[];
  };
  checklist_progress: Record<string, Record<string, {
    completed: boolean;
  }>>;
  checklist_evidence: Record<string, string>; // item_id → evidence text
  current_stage: string;
  transcript_preview: string;
  next_step: string;
  assist_trigger?: {
    id: string;
    title: string;
    hint: string;
    priority: number;
  } | null;
}
```

### Global state (backend)

```python
# Audio & transcription
accumulated_transcript: str          # Full transcript so far
audio_buffer: AudioBuffer            # Current buffer instance
transcription_language: str          # 'en', 'id', 'ru', etc.
is_live_recording: bool              # True during live session

# Client insights (cached)
last_client_insight: Dict            # Latest analysis
last_hint: str                       # Last hint sent
last_prob: float                     # Last probability

# Checklist tracking
current_stage: str                   # Current call stage
checklist_progress: Dict             # item_id → {completed: bool}
checklist_completion_cache: Dict     # item_id → timestamp
checklist_llm_cache: Dict            # item_id → {response, timestamp}
checklist_evidence: Dict             # item_id → evidence text

# Intent detection
last_trigger_time: float             # Timestamp of last trigger
active_trigger_id: str | None        # Current active trigger ID
```

---

## 7. 🛠️ Error handling

### Fallback strategy

```
If LLM fails:
  └─ Use keyword-based analysis (client_insight.py)

If Whisper fails:
  └─ Return empty transcript (no update sent)

If trigger detection fails:
  └─ assist_trigger = None (no card shown)

If checklist LLM fails:
  └─ Skip item, retry next cycle (cached for 60s)
```

### Guard clauses

```
analyze_client_sentiment:
  - Skip if text < 20 chars
  - Return neutral analysis

check_checklist_item_semantic:
  - Skip if text < 30 chars
  - Skip if LLM confidence < 0.8
  - Return False (don't mark complete)

detect_trigger:
  - Skip if text < 10 chars
  - Skip if same trigger + < 30s ago
  - Return None
```

---

## 8. 📈 Performance tuning

| Component | Update Interval | Cache | Cost |
|-----------|-----------------|-------|------|
| Transcription | 5s | None | 1 Whisper call/5s |
| Client Sentiment | 5s | None | 1 LLM call/5s |
| Trigger Detection | 5s | None | Regex only |
| Checklist Check | 5s | 30s cooldown + 60s LLM cache | 1 LLM call per item per 30s |
| WebSocket Rate | 1/sec | Throttle on frontend | Network only |

**Total cost per minute:**
- Whisper: 12 calls
- LLM (sentiment): 12 calls
- LLM (checklist): ~2–4 calls per item
- OpenRouter: ~$0.01–0.05/min (Claude 3 Haiku)
