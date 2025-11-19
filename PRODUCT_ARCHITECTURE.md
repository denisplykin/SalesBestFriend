# 🎯 Архитектура Sales Best Friend

## 📋 Общее описание

**Sales Best Friend** — это система реального времени для коучинга менеджеров по продажам во время звонков. Система использует:
- **Транскрипцию речи** через Whisper
- **LLM-анализ** через Claude (OpenRouter)
- **WebSocket** для real-time обновлений
- **React** фронтенд с компонентами для отображения подсказок

---

## 🏗️ Компоненты системы

### **1. Backend (FastAPI + Python)**

#### Главный файл: `backend/main.py`

**Основные компоненты:**

1. **WebSocket `/ingest`** — принимает аудио поток
2. **WebSocket `/coach`** — отправляет подсказки фронтенду
3. **HTTP endpoints** для обработки текста, YouTube, видео

**Глобальное состояние:**
- `accumulated_transcript` — накопленная транскрипция
- `checklist_progress` — прогресс по чек-листу
- `last_client_insight` — последний анализ клиента
- `current_stage` — текущий этап звонка
- `transcription_language` — выбранный язык

---

### **2. Основные модули Backend**

#### **a) `utils/realtime_transcriber.py`**
- Транскрибирует аудио через **faster-whisper**
- Работает каждые **10 секунд** (настраиваемо)
- Поддерживает множество языков (id, en, ru и т.д.)

#### **b) `utils/llm_analyzer.py`**
Выполняет **семантический анализ** через LLM (Claude Haiku):

**Методы:**
- `identify_speakers()` — определяет кто говорит (клиент vs продавец)
- `analyze_client_sentiment()` — анализирует эмоции, интересы, возражения
- `check_checklist_item_semantic()` — проверяет выполнение пунктов чек-листа через LLM
- `generate_next_step()` — генерирует следующий шаг

**Важно:** использует **guard clauses**:
- Пропускает слишком короткие тексты (< 20 символов)
- Требует **confidence ≥ 0.8** для подтверждения пункта чек-листа

#### **c) `utils/intent_detector.py`**
Детектирует **триггеры** в транскрипции на основе ключевых слов из `playbook.json`:

**Логика:**
1. Сканирует транскрипцию на предмет ключевых слов
2. Выбирает триггер с **наивысшим приоритетом**
3. **Anti-spam:** не повторяет тот же триггер чаще чем раз в 30 секунд
4. Возвращает карточку с подсказкой для фронтенда

**Примеры триггеров:**
- "дорого" / "expensive" → 💰 Price objection
- "подумаю" / "think about" → ⏰ Delaying decision
- "согласен" / "let's do it" → ✨ Positive signal!

#### **d) `sales_checklist.py`**
Определяет **структуру чек-листа** продаж:

**5 этапов:**
1. **Greeting** — приветствие, установка контакта
2. **Discovery** — выявление потребностей
3. **Presentation** — презентация решения
4. **Objections** — обработка возражений
5. **Closing** — закрытие сделки

Каждый этап содержит 4-6 пунктов (всего ~25 пунктов).

**Функции:**
- `detect_stage_from_text()` — определяет текущий этап по ключевым словам
- `generate_next_step_recommendation()` — генерирует рекомендацию для следующего шага

#### **e) `utils/audio_buffer.py`**
Буфер для накопления аудио данных:
- Накапливает PCM чанки от фронтенда
- Триггерит транскрипцию каждые **10 секунд**
- Поддерживает сброс буфера после обработки

#### **f) `insights/client_insight.py`**
Резервный **keyword-based анализ** клиента (fallback если LLM недоступен).

#### **g) `utils/youtube_processor.py`**
Обработка YouTube видео:
- Скачивание через yt-dlp
- Извлечение аудио через FFmpeg
- Транскрипция всего видео

---

### **3. Frontend (React + TypeScript)**

#### Главный файл: `frontend/src/App.tsx`

**Основные возможности:**

1. **Live Recording** — захват аудио из вкладки Chrome (Google Meet, Zoom, YouTube)
2. **YouTube Mode** — обработка видео с YouTube
3. **Text Mode** — отладка через текстовый ввод

**WebSocket подключения:**
- **`/ingest`** — отправляет аудио чанки (PCM 16kHz mono)
- **`/coach`** — получает подсказки, инсайты, триггеры

**Компоненты интерфейса:**

#### **a) `InCallAssist.tsx`**
**Карточка с подсказками in-call** (появляется при триггере):
- Показывает **title** и **hint** из playbook.json
- Автоматически исчезает через 10 секунд
- Имеет кнопку ручного закрытия
- Отображается **поверх** NextStepCard

#### **b) `NextStepCard.tsx`**
**Рекомендация следующего шага:**
- Генерируется LLM на основе текущего этапа
- Обновляется каждые 5-10 секунд
- Показывает текущий этап звонка (Greeting → Discovery → Presentation → Objections → Closing)

#### **c) `ClientInfoSummary.tsx`**
**Информация о клиенте:**
- **Эмоция** (engaged, hesitant, defensive...)
- **Возражения** (price, time, quality...)
- **Интересы** (game-based learning, logic...)
- **Потребности** (core pain point)
- **Уровень вовлеченности** (0-100%)

#### **d) `CallChecklist.tsx`**
**Чек-лист прогресса звонка:**
- Показывает все 5 этапов
- Отмечает выполненные пункты ✅
- Показывает "📋 Details" с доказательствами (evidence)
- Обновляется в реальном времени

#### **e) `LanguageSelector.tsx`**
Выбор языка транскрипции (id, en, ru и т.д.)

#### **f) `DebugPanel.tsx`**
Панель для отладки:
- Ввод текста вручную
- Загрузка видео-файла
- Вставка YouTube URL

---

## 🔄 Полный цикл работы (Real-time mode)

### **Шаг 1: Захват аудио (Frontend)**

```
1. Пользователь нажимает "🎤 Start Live Recording"
2. Chrome запрашивает разрешение на захват вкладки
3. Пользователь выбирает вкладку Google Meet + включает "Share audio"
4. Web Audio API конвертирует аудио в PCM 16kHz mono
5. Frontend отправляет чанки по 8KB через WebSocket /ingest
```

### **Шаг 2: Накопление аудио (Backend)**

```
1. /ingest WebSocket получает PCM чанки
2. AudioBuffer накапливает данные
3. Каждые 10 секунд (163KB буфер) → триггер транскрипции
```

### **Шаг 3: Транскрипция (Backend)**

```
1. faster-whisper транскрибирует буфер → текст
2. Транскрипция добавляется в accumulated_transcript
3. Сохраняем последние 500 слов (для контекста)
```

### **Шаг 4: LLM Анализ (Backend) — параллельно**

#### **4a. Speaker Diarization**
```
llm_analyzer.identify_speakers(transcript)
→ Определяет кто говорит (client vs sales)
→ Извлекает только клиентскую речь
```

#### **4b. Client Sentiment Analysis**
```
llm_analyzer.analyze_client_sentiment(client_text, context)
→ Извлекает:
   - emotion: "hesitant", "engaged"
   - objections: ["price", "time"]
   - interests: ["game-based learning"]
   - needs: "Affordable solution"
   - engagement_level: 0.7
   - stage_hint: "objection"
```

#### **4c. Trigger Detection**
```
intent_detector.detect_trigger(transcript, language)
→ Сканирует ключевые слова из playbook.json
→ Выбирает триггер с highest priority
→ Anti-spam: cooldown 30s
→ Возвращает: {id, title, hint, priority}
```

#### **4d. Checklist Validation (LLM-based)**
```
Для каждого невыполненного пункта:
1. Проверяем cache (30s cooldown)
2. Вызываем llm_analyzer.check_checklist_item_semantic()
3. LLM проверяет: "Введение выполнено?" → {completed: true, confidence: 0.95}
4. Если confidence >= 0.8 → отмечаем ✅
5. Сохраняем evidence (последние 2 предложения)
```

#### **4e. Stage Detection**
```
detect_stage_from_text(accumulated_transcript)
→ Определяет текущий этап на основе ключевых слов
→ Возвращает: "greeting" | "discovery" | "presentation" | "objection" | "closing"
```

#### **4f. Next Step Recommendation**
```
llm_analyzer.generate_next_step(stage, insights, progress, context)
→ Генерирует контекстную рекомендацию (max 15 слов)
→ Пример: "Ask about their budget and timeline constraints"
```

### **Шаг 5: Broadcast через WebSocket (Backend)**

```json
Отправляем JSON всем подключенным клиентам через /coach:

{
  "hint": "Ask about budget",
  "prob": 0.65,
  "client_insight": {
    "emotion": "hesitant",
    "objections": ["price"],
    "interests": ["game-based learning"],
    "engagement_level": 0.7
  },
  "checklist_progress": {
    "intro_yourself": true,
    "ask_availability": true,
    ...
  },
  "checklist_evidence": {
    "intro_yourself": "Hi, I'm John from SalesBestFriend..."
  },
  "current_stage": "objection",
  "next_step": "Address price concern with value proposition",
  "assist_trigger": {
    "id": "price_objection",
    "title": "💰 Client says it's too expensive",
    "hint": "Emphasize value, share success stories, offer trial",
    "priority": 10
  },
  "transcript_preview": "...last 500 chars..."
}
```

### **Шаг 6: Отображение на Frontend**

```
1. /coach WebSocket получает сообщение
2. Rate limiting: не чаще 1 раз в секунду
3. Обновляет все компоненты:
   - InCallAssist (если есть assist_trigger)
   - NextStepCard (next_step)
   - ClientInfoSummary (client_insight)
   - CallChecklist (checklist_progress + evidence)
   - Probability bar (prob)
```

---

## 📊 Кеширование и оптимизация

### **1. Checklist Completion Cache**
```python
checklist_completion_cache: Dict[str, float]
```
- Хранит timestamp последней проверки пункта
- Не проверяем повторно, если прошло < 30 секунд
- **Permanent completion:** если пункт отмечен ✅ — больше никогда не проверяем

### **2. LLM Response Cache**
```python
checklist_llm_cache: Dict[str, Dict]
```
- Кешируем LLM ответы на 60 секунд
- Избегаем повторных вызовов для одного и того же пункта

### **3. Trigger Anti-spam**
```python
last_trigger_time: float
active_trigger_id: str
```
- Не показываем тот же триггер чаще чем раз в 30 секунд
- Предотвращает спам карточек

### **4. Frontend Rate Limiting**
```typescript
lastUpdateRef.current
```
- Обновляем UI не чаще 1 раз в секунду
- Предотвращает flickering

---

## 💰 Стоимость использования

**За 1 минуту разговора:**
- **Whisper transcription:** 6 вызовов (каждые 10 сек)
- **Client sentiment analysis:** 6 LLM вызовов
- **Checklist validation:** ~2-4 LLM вызова (с кешированием)
- **Next step generation:** 6 LLM вызовов

**Модель:** Claude 3 Haiku (рекомендуется для MVP)
- **Стоимость:** ~$0.01-0.05 за минуту разговора
- **Альтернатива:** llama-3.3-70b-instruct:free (БЕСПЛАТНО!)

---

## 🎯 Режимы работы

### **1. Live Recording Mode**
- Захват аудио из вкладки Chrome
- Real-time транскрипция + анализ
- **Используется:** Web Audio API → /ingest → Whisper → LLM → /coach

### **2. YouTube Mode**
- Скачивает видео через yt-dlp
- Извлекает аудио через FFmpeg
- Транскрибирует целиком
- **Endpoint:** `POST /api/process-youtube`

### **3. Text Mode**
- Вставка готовой транскрипции
- Мгновенный анализ без ASR
- **Endpoint:** `POST /api/process-transcript`

### **4. Video Upload Mode**
- Загрузка видео файла (mp4, avi, mov, webm, mkv)
- Извлечение аудио через FFmpeg
- Транскрипция и анализ
- **Endpoint:** `POST /api/process-video`

---

## 🔐 Guard Clauses (защита от ошибок)

### **1. В LLM Analyzer**
```python
# Пропускаем слишком короткие тексты
if len(client_text) < 20:
    return neutral_analysis

# Требуем высокую уверенность
if confidence < 0.8:
    return False  # Don't mark complete
```

### **2. В Intent Detector**
```python
# Пропускаем пустые транскрипты
if len(transcript) < 5:
    return None

# Anti-spam cooldown
if time_since_last_trigger < 30s:
    return None
```

### **3. В Checklist**
```python
# Permanent completion
if item.completed == True:
    continue  # Never check again

# Check cooldown
if last_check_time < 30s ago:
    continue  # Skip duplicate check
```

---

## 🎨 Playbook.json структура

**25 триггеров** для различных ситуаций:

```json
{
  "id": "price_objection",
  "match": ["дорого", "expensive", "mahal"],
  "title": "💰 Client says it's too expensive",
  "hint": "Emphasize value, not price...",
  "priority": 10
}
```

**Приоритеты:**
- **10** = критично (price objection, trial request, positive signal)
- **7-9** = важно (competitor, quality doubt)
- **4-6** = средне (budget, time constraint)
- **1-3** = низко (technical concerns)

**Категории триггеров:**
1. **Возражения** (price, time, quality, competition)
2. **Стадии принятия решения** (need to think, family decision)
3. **Технические вопросы** (equipment, technical issues)
4. **Мотивация** (child motivation, previous bad experience)
5. **Позитивные сигналы** (trial request, positive feedback)

---

## 🌐 Поддержка языков

**Текущие языки:**
- 🇮🇩 **Bahasa Indonesia (id)** — по умолчанию
- 🇬🇧 **English (en)**
- 🇷🇺 **Русский (ru)**

**Где используется:**
- `transcription_language` — для Whisper
- Ключевые слова в playbook.json (мультиязычные)
- Ключевые слова в sales_checklist.py (мультиязычные)
- Промпты для LLM (автоматически адаптируются)

**Как добавить новый язык:**
1. Добавить код языка в `LanguageSelector.tsx`
2. Добавить ключевые слова в `playbook.json` (поле `match`)
3. Добавить ключевые слова в `sales_checklist.py` (для stage detection)
4. Whisper автоматически поддерживает 99+ языков

---

## 🚀 Порядок вызовов при Live Recording

```
Frontend: startRecording()
  ↓
1. navigator.mediaDevices.getDisplayMedia()
   → Захват вкладки Chrome + audio track
  ↓
2. Web Audio API: AudioContext (16kHz) + ScriptProcessor
   → Конвертация в PCM Int16
  ↓
3. WebSocket /ingest.send(pcm_chunk)
   → Отправка каждые 0.5 сек
  ↓
Backend: /ingest WebSocket
  ↓
4. AudioBuffer.add_chunk()
   → Накопление до 10 секунд
  ↓
5. transcribe_audio_buffer(buffer, language)
   → faster-whisper → transcript
  ↓
6. Параллельно:
   ├─ llm_analyzer.identify_speakers()
   ├─ llm_analyzer.analyze_client_sentiment()
   ├─ intent_detector.detect_trigger()
   ├─ llm_analyzer.check_checklist_item_semantic() (для каждого пункта)
   ├─ detect_stage_from_text()
   └─ llm_analyzer.generate_next_step()
  ↓
7. Формирование JSON message
  ↓
8. WebSocket /coach.send_text(json)
   → Broadcast всем клиентам
  ↓
Frontend: /coach WebSocket.onmessage
  ↓
9. Обновление React state
  ↓
10. Re-render компонентов:
    - InCallAssist (if trigger)
    - NextStepCard
    - ClientInfoSummary
    - CallChecklist
    - Probability bar
```

---

## ✅ Итоговая диаграмма потока данных

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│  (React + TypeScript + Web Audio API)                           │
│                                                                  │
│  Chrome Tab Audio → AudioContext (16kHz) → PCM Int16 chunks     │
└─────────────────────────────────┬────────────────────────────────┘
                                  │ WebSocket /ingest
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
│  (FastAPI + Python)                                             │
│                                                                  │
│  AudioBuffer (10s) → faster-whisper → transcript                │
│                           ↓                                      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  Parallel Processing:                                 │      │
│  │  1. LLMAnalyzer (Claude Haiku)                       │      │
│  │     - identify_speakers()                            │      │
│  │     - analyze_client_sentiment()                     │      │
│  │     - check_checklist_item_semantic() x N            │      │
│  │     - generate_next_step()                           │      │
│  │  2. IntentDetector (playbook.json)                   │      │
│  │     - detect_trigger()                               │      │
│  │  3. StageDetector (keyword-based)                    │      │
│  │     - detect_stage_from_text()                       │      │
│  └──────────────────────────────────────────────────────┘      │
│                           ↓                                      │
│  Build JSON message with all insights                           │
└─────────────────────────────────┬────────────────────────────────┘
                                  │ WebSocket /coach
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│  (React Components Update)                                      │
│                                                                  │
│  - InCallAssist card (if trigger)                               │
│  - NextStepCard (AI recommendation)                             │
│  - ClientInfoSummary (emotions, objections, interests)          │
│  - CallChecklist (progress with evidence)                       │
│  - Probability bar (deal success %)                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Технические детали реализации

### **Web Audio API (Frontend)**

```javascript
// Создание AudioContext с частотой 16kHz (требование Whisper)
const audioContext = new AudioContext({ sampleRate: 16000 })

// Создание источника из MediaStream
const source = audioContext.createMediaStreamSource(stream)

// ScriptProcessor для обработки аудио чанков
const processor = audioContext.createScriptProcessor(4096, 1, 1)

processor.onaudioprocess = (e) => {
  const inputData = e.inputBuffer.getChannelData(0) // Float32Array
  
  // Конвертация Float32 → Int16 (требование для PCM)
  const int16Data = new Int16Array(inputData.length)
  for (let i = 0; i < inputData.length; i++) {
    int16Data[i] = inputData[i] < 0 
      ? inputData[i] * 0x8000 
      : inputData[i] * 0x7FFF
  }
  
  // Отправка через WebSocket
  websocket.send(int16Data.buffer)
}
```

### **faster-whisper (Backend)**

```python
from faster_whisper import WhisperModel

# Загрузка модели (один раз при старте)
model = WhisperModel("base", device="cpu", compute_type="int8")

# Транскрипция
segments, info = model.transcribe(
    audio_data,
    language=language,  # "id", "en", "ru"
    beam_size=5,
    vad_filter=True  # Voice Activity Detection
)

# Объединение сегментов в текст
transcript = " ".join([segment.text for segment in segments])
```

### **OpenRouter API (Backend)**

```python
import requests

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "anthropic/claude-3-haiku",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.5,
    "max_tokens": 2000
}

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers=headers,
    json=payload,
    timeout=30
)

result = response.json()
content = result["choices"][0]["message"]["content"]
```

---

## 📈 Метрики и мониторинг

### **System Status Endpoint**

`GET /api/status` возвращает:

```json
{
  "status": "running",
  "timestamp": "2025-11-19T10:30:00",
  "metrics": {
    "uptime_seconds": 3600,
    "audio_active": true,
    "last_audio_chunk": "2025-11-19T10:29:55",
    "transcription_count": 360,
    "last_transcription": "2025-11-19T10:29:50",
    "lm_analysis": {
      "count": 360,
      "errors": 0
    },
    "recommendations": {
      "count": 360,
      "errors": 0
    },
    "last_error": null
  }
}
```

### **Логирование**

Backend выводит детальные логи:
```
🎯 TRANSCRIPTION #42:
====================================================================
📝 REAL-TIME TRANSCRIPT (235 chars):
====================================================================
Client: It's too expensive for us right now.
Sales: I understand. Let me show you the value...
====================================================================

🧠 LLM SEMANTIC ANALYSIS:
   👤 Client: 1 segments
   💼 Sales: 1 segments
   
   👤 CLIENT TEXT FOR ANALYSIS (42 chars):
   'It's too expensive for us right now.'
🧠 Analyzing client sentiment with LLM...
   Emotion: hesitant
   Objections: ['price']
   Interests: []

📋 Checking checklist (LLM=True)...
   ✅ COMPLETED: Introduce yourself and company
   ❌ Not yet: Check if they have time for the call

🎯 ASSIST TRIGGER: price_objection - 💰 Client says it's too expensive

✅ Real-time analysis sent to 1 clients
```

---

## 🛡️ Обработка ошибок

### **1. WebSocket разрывы**
```python
try:
    await websocket.send_text(message)
except Exception as e:
    print(f"❌ Ошибка отправки: {e}")
    disconnected.add(websocket)

coach_connections.difference_update(disconnected)
```

### **2. LLM timeout**
```python
try:
    response = requests.post(url, json=payload, timeout=30)
except requests.Timeout:
    # Fallback to cached response or simple analysis
    return neutral_analysis
```

### **3. Whisper failures**
```python
try:
    transcript = transcribe_audio_buffer(buffer, language)
except Exception as e:
    print(f"❌ Transcription failed: {e}")
    return ""  # Skip this cycle
```

### **4. Frontend audio capture failures**
```javascript
try {
  const stream = await navigator.mediaDevices.getDisplayMedia({...})
  const audioTracks = stream.getAudioTracks()
  
  if (audioTracks.length === 0) {
    throw new Error('No audio track. Did you check "Share audio"?')
  }
} catch (err) {
  if (err.name === 'NotAllowedError') {
    setHint('Access denied. Please allow screen sharing.')
  } else if (err.name === 'NotFoundError') {
    setHint('Audio source not found. Check "Share audio".')
  }
}
```

---

## 🔄 Состояния системы

### **Backend States**

```python
is_live_recording: bool = False  # True during live recording session
use_llm_analysis: bool = True    # Enable/disable LLM analysis
transcription_language: str = "id"  # Current language
```

### **Frontend States**

```typescript
status: 'idle' | 'connecting' | 'connected' | 'error'
isRecording: boolean
selectedLanguage: string
assistTrigger: Trigger | null
transcriptLines: string[]
```

---

## 🎓 Примеры использования

### **Пример 1: Live Recording с Google Meet**

```
1. Открыть Google Meet звонок
2. В Sales Best Friend нажать "🎤 Start Live Recording"
3. В диалоге выбрать вкладку Google Meet
4. ✅ Включить "Share audio"
5. Начать разговор
6. Система транскрибирует каждые 10 секунд
7. Подсказки появляются автоматически
```

### **Пример 2: Анализ YouTube видео**

```
1. Найти YouTube видео с записью звонка
2. Скопировать URL
3. В Sales Best Friend вставить URL
4. Выбрать язык (id/en/ru)
5. Нажать "Process YouTube"
6. Дождаться полной транскрипции
7. Получить все инсайты одновременно
```

### **Пример 3: Отладка через текст**

```
1. Открыть Debug Panel
2. Вставить текст разговора:
   Client: It's too expensive
   Sales: Let me show you the value
3. Выбрать язык
4. Нажать "Submit"
5. Мгновенный анализ без ASR
```

---

## 🚀 Производительность

### **Латентность (от речи до подсказки)**

```
Audio capture: ~500ms (buffer accumulation)
↓
Audio transmission: ~50ms (WebSocket)
↓
Transcription (Whisper): ~2-3s (for 10s audio)
↓
LLM Analysis (parallel):
├─ Speaker identification: ~1s
├─ Sentiment analysis: ~1-2s
├─ Checklist validation: ~1s per item (cached)
├─ Trigger detection: <10ms (regex)
└─ Next step generation: ~1s
↓
WebSocket transmission: ~50ms
↓
Frontend render: ~50ms

Total: ~5-7 seconds от речи до подсказки
```

### **Оптимизации**

1. **Транскрипция каждые 10 секунд** (не 5) — экономия Whisper вызовов
2. **LLM кеширование** — 60s TTL для checklist
3. **Checklist cooldown** — 30s между проверками
4. **Trigger anti-spam** — 30s cooldown
5. **Frontend rate limiting** — 1 update/sec
6. **Parallel LLM calls** — все анализы одновременно

---

## 📚 Зависимости

### **Backend (requirements.txt)**

```
fastapi
uvicorn[standard]
websockets
python-dotenv
requests
faster-whisper
yt-dlp
ffmpeg-python
```

### **Frontend (package.json)**

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.0.0",
    "vite": "^4.3.0"
  }
}
```

### **Системные зависимости**

- **FFmpeg** — для извлечения аудио из видео
- **Python 3.11+** — для backend
- **Node.js 16+** — для frontend
- **Chrome/Edge/Brave** — для audio capture (Firefox не поддерживает)

---

## 🔮 Будущие улучшения

### **Planned Features**

1. **Persistence** — сохранение истории звонков в базу данных
2. **Multi-user** — поддержка множества пользователей
3. **Dashboard** — аналитика по всем звонкам
4. **Custom Playbooks** — редактирование триггеров через UI
5. **Export** — выгрузка транскриптов и инсайтов
6. **Integrations** — Zoom SDK, Google Meet API
7. **Voice Commands** — управление через голос
8. **Mobile App** — React Native версия

### **Technical Improvements**

1. **Streaming Whisper** — реальная потоковая транскрипция (< 1s латентность)
2. **GPU Acceleration** — использование GPU для Whisper
3. **Caching Layer** — Redis для распределенного кеша
4. **Load Balancing** — для масштабирования на множество пользователей
5. **WebRTC** — прямое подключение к звонкам без screen capture

---

## 📝 Лицензия

MIT License - см. LICENSE файл

---

## 👥 Контакты

Для вопросов и предложений:
- GitHub Issues
- Email: support@salesbestfriend.ai

---

**Удачных продаж! 🚀**

