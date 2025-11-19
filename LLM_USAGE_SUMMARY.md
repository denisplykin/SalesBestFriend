# 🤖 LLM Usage Summary

## Overview

System uses **2 different LLM models** depending on the use case:

| Model | Cost per 1K tokens | Used for | Status |
|-------|-------------------|----------|--------|
| **Claude 3 Haiku** | $0.80 input, $4.00 output | Client sentiment analysis, checklist validation | ✅ **ACTIVE** |
| **Claude 3.5 Sonnet** | $3.00 input, $15.00 output | Hint & probability generation | ⚠️ **DEBUG ONLY** |

---

## 1️⃣ Primary Analysis: `analyze_client_sentiment()`

### Model
- **anthropic/claude-3-haiku**
- Cost: ~$0.0009 per call
- Speed: ~1-2 seconds

### What It Does
Analyzes client speech to extract:
- **Emotion**: engaged, curious, hesitant, defensive, negative, neutral
- **Objections**: ["price", "time", "family", "value", "feasibility"]
- **Interests**: ["game-based learning", "future skills", "logic"]
- **Needs**: Core pain point
- **Engagement**: 0.0-1.0 scale
- **Stage**: profiling → presentation → objection → closing
- **Buying Signals**: Positive indicators

### Where It's Called
✅ Live recording: Every 10 seconds (540 times per 90 min)
✅ Debug text mode: Once per request
✅ YouTube mode: Once per video

### Cost
- **Live**: $0.49 per 90-min call
- **Debug**: $0.0009 per request

---

## 2️⃣ Checklist Validation: `check_checklist_item_semantic()`

### Model: Claude 3 Haiku
- Cost: ~$0.001 per call
- **Status**: ✅ ACTIVE

### What It Does
Semantic validation of checklist items based on conversation context.

### Cache
60 seconds per item (reduces calls ~50%)

### Cost
- ~$0.05 per 90-min call (with caching)

---

## 3️⃣ Hint & Probability: `call_openrouter()`

### Model
- **anthropic/claude-3.5-sonnet** ⬅️ **5x MORE EXPENSIVE**
- Cost: ~$0.0044 per call

### Status
❌ **NOT used in live recording** (removed Oct 26)
⚠️ **ONLY in debug modes** (text & YouTube)

### Cost
- Live: $0.00 (DISABLED)
- Debug: $0.0044 per request

---

## 4️⃣ FREE Trigger Detection: `intent_detector.detect_trigger()`

### Type
- **Keyword/Regex matching** (NO LLM)
- Cost: **$0.00** ✅

### What It Does
Detects 25 sales triggers in real-time:
- Price objections
- Competitor mentions
- Lack of interest
- Time constraints
- Family decisions
- Positive signals

### Cost
**COMPLETELY FREE**

---

## 💰 Summary Costs (90 min call)

| Function | Calls | Total |
|----------|-------|-------|
| analyze_client_sentiment (Haiku) | 540 | **$0.49** |
| check_checklist_item (Haiku) | 50 | **$0.05** |
| intent_detector (FREE!) | 540 | **$0.00** |
| call_openrouter (Sonnet) | 0 | **$0.00** |
| **TOTAL** | | **$0.54** ✅ |

---

## 📍 Code Locations

**Main Analysis:**
- `backend/utils/llm_analyzer.py` line 70-180

**Live Recording:**
- `backend/main.py` line 220-570 (websocket_ingest)

**Debug Endpoints:**
- `backend/main.py` line 664-760 (text)
- `backend/main.py` line 921-1020 (youtube)

**Trigger Detection:**
- `backend/utils/intent_detector.py` line 60-110

---

## ✅ What's Recommended

✅ **USE**: analyze_client_sentiment (Haiku - cheap)
✅ **USE**: check_checklist_item (Haiku - cheap)
✅ **USE**: intent_detector (FREE!)
❌ **AVOID**: call_openrouter for live (too expensive)

---

Last Updated: October 26, 2025
