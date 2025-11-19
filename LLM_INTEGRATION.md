# 🤖 LLM Integration - Техническое описание

## 1. 🏗️ Архитектура LLM

### Используемая модель
```
Provider: OpenRouter
Model: anthropic/claude-3-haiku
Version: Latest
Cost: ~$0.80 per million input tokens, ~$4 per million output tokens
Context: 200K tokens
Temperature: 0.5 (balanced)
Max tokens: 1000–2000
```

### Где используется LLM

```
Backend (FastAPI)
│
├─ LLMAnalyzer (backend/utils/llm_analyzer.py)
│  ├─ analyze_client_sentiment()           ← Client insights extraction
│  ├─ check_checklist_item_semantic()      ← Checklist validation
│  ├─ identify_speakers()                  ← Speaker diarization (optional)
│  └─ generate_next_step()                 ← Next step recommendation (optional)
│
└─ IntentDetector (backend/utils/intent_detector.py)
   └─ detect_trigger()                     ← Keyword/regex only (NO LLM)
```

---

## 2. 📍 LLMAnalyzer - Где используется

### 2.1 `analyze_client_sentiment()`

**Вызывается:** Каждые 5 секунд при наличии транскрибированного текста

**Когда вызывается:**
- В `/ws/ingest` цикле (real-time live recording)
- В `/api/process-transcript` (debug text mode)
- В `/api/process-youtube` (YouTube mode)
- В `/api/process-video` (video file mode)

**Входные данные:**
```python
client_text = "I'm hesitant. It's too expensive. But the game-based learning sounds fun."
full_transcript_context = "... previous 500 chars of transcript ..."
```

**Prompt:**
```
You are analyzing a sales call to understand the client's interests, objections, needs, and emotional state.

Client speech segment:
 I'm hesitant. It's too expensive. But the game-based learning sounds fun.
 
Full conversation context (last messages):
... context ...

Analyze and provide:
1. EMOTION: How is the client feeling? (engaged, curious, hesitant, defensive, negative, neutral)
2. INTERESTS: What topics interest them? (e.g., "game-based learning", "future skills", "logic", "creativity", "confidence")
3. OBJECTIONS: What are their concerns or obstacles? (e.g., "price", "time", "family", "value", "feasibility")
4. NEEDS: What is their core need or pain point?
5. ENGAGEMENT_LEVEL: 0.0-1.0 scale of how engaged they seem
6. STAGE_HINT: What stage of the call is this? (greeting, profiling, presentation, objection, closing)

CONFIDENCE: Only extract interests/objections if you are confident they were explicitly mentioned.
Avoid false positives from unclear or partial utterances.

Return ONLY valid JSON with no extra text:
{
  "emotion": "engaged|curious|hesitant|defensive|negative|neutral",
  "interests": ["topic1", "topic2"],
  "objections": ["concern1", "concern2"],
  "needs": "core need or pain point",
  "engagement_level": 0.75,
  "stage_hint": "profiling|presentation|objection|closing",
  "buying_signals": ["signal1", "signal2"],
  "reasoning": "Brief explanation of the analysis"
}

Focus on MEANING and CONTEXT, not just keywords. Understand what the client truly cares about.
```

**Выходные данные:**
```json
{
  "emotion": "hesitant",
  "interests": ["game-based learning"],
  "objections": ["price"],
  "needs": "Affordable solution",
  "engagement_level": 0.7,
  "stage_hint": "objection",
  "buying_signals": [],
  "reasoning": "Client hesitant about price but interested in game-based learning..."
}
```

**Guard clauses:**
```python
# Skip if text too short
if len(client_text.strip()) < 20:
    return {
        "emotion": "neutral",
        "objections": [],
        "interests": [],
        "needs": None,
        "engagement_level": 0.3,
        "stage_hint": "profiling",
        "buying_signals": [],
        "reasoning": "Text too short for analysis"
    }
```

**Где используется результат:**
```
JSON → Backend state
 └─ last_client_insight (cache)
    └─ WebSocket /coach broadcast
       └─ Frontend: ClientInfoSummary component
```

---

### 2.2 `check_checklist_item_semantic()`

**Вызывается:** Каждые 5 секунд, для каждого незавершённого пункта чеклиста

**Кэширование (3 уровня):**
```
Level 1: Permanent completion
  if item.completed == True:
    └─ SKIP (never re-check)

Level 2: 30-second cooldown
  if item.id in checklist_completion_cache:
    if time.now() - cache[item.id] < 30s:
      └─ SKIP

Level 3: 60-second LLM cache
  if item.id in checklist_llm_cache:
    if time.now() - cache[item.id] < 60s:
      └─ Reuse cached response
```

**Входные данные:**
```python
item_text = "Introduce yourself and company"
conversation_context = "Hi, I'm John. We help kids learn coding..."
language = "en"
```

**Prompt:**
```
You are a sales call analyzer. Determine if a specific sales action has been completed in the conversation.

Sales action to check:
"Introduce yourself and company"

Conversation so far (last 2000 chars):
Hi, I'm John. We help kids learn coding...

Task:
1. Determine if this action was clearly done in the conversation
2. Provide confidence level (0.0-1.0)
3. Extract the exact text evidence (2 sentences max)

Return ONLY valid JSON:
{
  "completed": true|false,
  "confidence": 0.95,
  "evidence": "Exact text from conversation proving completion"
}

STRICT RULES:
- Confidence must be >= 0.8 to mark as completed
- Evidence must be from actual conversation text
- If unsure, return confidence < 0.8
```

**Выходные данные:**
```json
{
  "completed": true,
  "confidence": 0.95,
  "evidence": "Hi, I'm John. We help kids learn coding."
}
```

**Validation logic:**
```python
if response["completed"] and response.get("confidence", 0) >= 0.8:
    checklist_progress[item_id] = {"completed": True}
    checklist_evidence[item_id] = response["evidence"]
    checklist_completion_cache[item_id] = time.time()
else:
    # Don't mark complete, retry next cycle (with cooldown)
    pass
```

**Guard clauses:**
```python
# Skip if text too short
if len(conversation_context) < 30:
    return False, ""

# Skip if LLM confidence too low
if llm_response.get("confidence", 0) < 0.8:
    return False, ""
```

**Где используется результат:**
```
JSON → Backend state
 └─ checklist_progress (Dict[item_id, {completed: bool}])
 └─ checklist_evidence (Dict[item_id, evidence_text])
    └─ WebSocket /coach broadcast
       └─ Frontend: CallChecklist component
```

---

### 2.3 `identify_speakers()` (опционально)

**Вызывается:** Один раз при наличии транскрибированного текста

**Входные данные:**
```python
transcript = "Hi, I'm John. That's great. What about pricing? It's 100 dollars."
```

**Prompt:**
```
Identify who is speaking in this sales call transcript. Mark each sentence with [SALES] or [CLIENT].

Format:
[SALES] Hi, I'm John.
[CLIENT] That's great.
[SALES] What about pricing?
[CLIENT] It's 100 dollars.

Return ONLY the formatted transcript with no extra text.
```

**Выходные данные:**
```python
[
    {"speaker": "sales", "text": "Hi, I'm John."},
    {"speaker": "client", "text": "That's great."},
    {"speaker": "sales", "text": "What about pricing?"},
    {"speaker": "client", "text": "It's 100 dollars."}
]
```

**Использование:**
```
Extract client_text from identified [CLIENT] segments
└─ Pass to analyze_client_sentiment()
```

---

### 2.4 `generate_next_step()` (опционально)

**Вызывается:** Один раз каждые 15-30 секунд

**Входные данные:**
```python
current_stage = "objection"
client_insight = {"emotion": "hesitant", "objections": ["price"], ...}
checklist_progress = {"intro_yourself": {"completed": True}, ...}
conversation_context = "..."
```

**Prompt:**
```
Based on the sales call state, provide the next recommended action for the sales manager.

Current stage: objection
Client state:
- Emotion: hesitant
- Objections: price
- Interests: game-based learning

Completed actions:
- Introduced yourself and company
- Identified pain points

Conversation so far: ...

Provide ONE concise, actionable next step (max 2 sentences) that:
1. Addresses the current objection
2. Follows best sales practices
3. Is specific and contextual

Return plain text (no JSON).
```

**Выходные данные:**
```
"Address the price objection: Show ROI calculations or offer flexible payment options."
```

**Использование:**
```
next_step = response
└─ WebSocket /coach: "next_step" field
   └─ Frontend: NextStepCard component
```

---

## 3. 🔧 API Integration - OpenRouter

### Request format

```python
import requests
import json

url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "anthropic/claude-3-haiku",
    "messages": [
        {
            "role": "system",
            "content": "You are a sales coach analyzing client calls..."
        },
        {
            "role": "user",
            "content": "Analyze this client speech: ..."
        }
    ],
    "temperature": 0.5,
    "max_tokens": 1000,
    "response_format": {"type": "json_object"}  # For JSON mode
}

response = requests.post(url, headers=headers, json=payload, timeout=10)
result = response.json()
llm_response_text = result["choices"][0]["message"]["content"]
```

### Error handling

```python
try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    result = response.json()
    
    if "error" in result:
        raise Exception(f"OpenRouter error: {result['error']}")
    
    return result["choices"][0]["message"]["content"]
    
except requests.Timeout:
    print("⚠️ LLM timeout (10s)")
    return None
except requests.RequestException as e:
    print(f"⚠️ LLM request failed: {e}")
    return None
except json.JSONDecodeError:
    print("⚠️ LLM response not valid JSON")
    return None
except Exception as e:
    print(f"⚠️ LLM error: {e}")
    return None
```

### Fallback strategy

```python
# If LLM fails → Use keyword-based analysis
try:
    llm_result = llm_analyzer.analyze_client_sentiment(client_text, context)
except Exception as e:
    print(f"⚠️ LLM analysis failed: {e}, using fallback")
    llm_result = keyword_analyzer.analyze_client_text(client_text)
    # Returns: {emotion, objections, interests, needs, engagement, stage}
```

---

## 4. 📊 Cost estimation

### Per 5-second update cycle

```
Assumptions:
- client_text: ~100 tokens (average)
- full_context: ~200 tokens
- Per request: ~300 tokens input

Per cycle (5s):
  1. analyze_client_sentiment()
     └─ 1 LLM call × 300 tokens ≈ $0.00024 (input only)

Per cycle per checklist item (with cooldown):
  2. check_checklist_item_semantic()
     └─ ~1 call per 30s (with 30s cooldown)
     └─ Per cycle: 1/6 call × 300 tokens ≈ $0.00004

Total per minute (12 cycles):
  - analyze_client_sentiment: 12 × $0.00024 ≈ $0.00288
  - check_checklist_item: (varies) ≈ $0.0005–0.001
  - Total: ~$0.003–0.005 per minute
  - Per hour: ~$0.18–0.30
  - Per day: ~$4–7
```

### Optimization techniques already in place

```
1. 30-second cooldown for checklist items
   └─ Reduces calls by 83% per item

2. 60-second LLM response cache
   └─ Reuses response if identical request within 60s

3. Guard clauses (skip short texts)
   └─ Text < 20 chars → skip analyze_client_sentiment
   └─ Text < 30 chars → skip check_checklist_item

4. Permanent completion cache
   └─ Once item.completed = True → never re-check

5. Keyword-based fallback
   └─ If LLM fails → use fast keyword matching
```

---

## 5. 🎯 Where IntentDetector does NOT use LLM

### IntentDetector (backend/utils/intent_detector.py)

```python
def detect_trigger(transcript: str) -> Dict | None:
    """
    Detect sales triggers using KEYWORD MATCHING ONLY (no LLM)
    """
    
    # Step 1: Keyword matching against playbook
    for trigger in self.playbook:
        for keyword in trigger["match"]:
            if keyword.lower() in transcript.lower():
                # Step 2: Priority selection
                if not self.active_trigger or trigger["priority"] > self.active_trigger_priority:
                    # Step 3: Anti-spam cooldown (30s)
                    if time.time() - self.last_trigger_time > 30:
                        self.active_trigger = trigger
                        self.last_trigger_time = time.time()
                        return trigger
    
    return None
```

**Why no LLM here?**
- Real-time requirement (instant response needed)
- Keyword matching is fast enough (regex only)
- Cost savings
- 25 triggers in playbook

**Performance:** ~1ms per transcript

---

## 6. 🔄 Request/Response lifecycle

### Example: analyze_client_sentiment flow

```
┌─ Client speaks: "It's too expensive"
│
├─ /ws/ingest receives audio chunk (PCM)
│
├─ AudioBuffer accumulates for 5s
│
├─ faster-whisper transcribes
│  └─ transcript = "It's too expensive"
│
├─ LLMAnalyzer.identify_speakers()
│  └─ [CLIENT] It's too expensive
│
├─ LLMAnalyzer.analyze_client_sentiment()
│  └─ Build prompt + send to OpenRouter
│  └─ Wait for response (timeout: 10s)
│  └─ Parse JSON
│     {
│       "emotion": "negative",
│       "objections": ["price"],
│       "interests": [],
│       "needs": "Lower price",
│       "engagement_level": 0.4,
│       "stage_hint": "objection"
│     }
│
├─ IntentDetector.detect_trigger()
│  └─ Regex match: "expensive" in "price_objection"
│  └─ Return: {id: "price_objection", title: "💰 Client...", hint: "..."}
│
├─ Send WebSocket message:
│  {
│    "client_insight": {...},
│    "assist_trigger": {...},
│    "hint": "...",
│    "prob": 0.8
│  }
│
└─ Frontend updates UI (throttled 1/sec)
```

---

## 7. 🛑 Known limitations

### Rate limiting (implicit)

```
No explicit rate limiting, but:
- 5-second update cycle = 12 LLM calls/minute max
- OpenRouter default: generous (no strict limits mentioned)
- Practical limit: ~1000 calls/day before hitting cost concerns
```

### Timeout handling

```
If LLM response > 10 seconds:
  └─ Request aborts
  └─ Fallback to keyword analysis
  └─ User sees delayed recommendation
```

### Context size

```
Max input per request: ~1500 tokens
- client_text: ~100 tokens
- full_context: ~200 tokens
- Prompt template: ~1000 tokens
Total: ~1300 tokens (safe margin)
```

### Temperature sensitivity

```
Current: temperature=0.5 (balanced)
- Lower (0.2): More deterministic, consistent
- Higher (0.9): More creative, variable
For checklist: Consider lowering to 0.3 for stricter validation
```

---

## 8. 📈 Monitoring

### Metrics to track

```python
class SystemStatus:
    llm_analysis_count: int          # Total LLM calls made
    llm_analysis_errors: int         # Failed LLM calls
    llm_cache_hits: int              # Responses from cache
    avg_llm_latency_ms: float        # Average response time
    checklist_validations: int       # Total checklist checks
    checklist_false_positives: int   # Incorrect markings
    
    # Per endpoint
    process_transcript_llm_calls: int
    process_youtube_llm_calls: int
    process_video_llm_calls: int
```

### Log examples

```
🤖 LLM Analyzer initialized with model: anthropic/claude-3-haiku
🔍 ANALYZING CLIENT TEXT:
   📝 Input (66 chars): Я не уверен что этот курс подходит...
   ✅ LLM Analysis:
      Emotion: hesitant
      Interests: ['future skills', 'value']
      Objections: ['feasibility']
      Engagement: 0.7

⏭️ Text too short (13 chars), using minimal analysis
   (guard clause triggered)

⚠️ Sentiment analysis failed: timeout
   (fallback to keyword analysis)
```

---

## 9. 🔐 Security

### API Key management

```python
# .env file (never commit)
OPENROUTER_API_KEY=sk-or-v1-...

# Load in backend
from dotenv import load_dotenv
import os

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Use in requests
headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
```

### No sensitive data in prompts

```
❌ DON'T include:
- Client real names
- Phone numbers
- Email addresses
- Company names

✅ DO include:
- Generic descriptions: "client", "child", "course"
- Anonymized speech: "The client said..."
```
