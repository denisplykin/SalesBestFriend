# 🎧 Zoom + Наушники - Полная настройка

## 🎯 Цель
Захватывать аудио из Zoom звонков **с наушниками** в твоё приложение для real-time анализа.

---

## 📊 Как это работает

```
┌─────────────┐
│  Твой голос │ (микрофон)
└──────┬──────┘
       │
       v
┌────────────────────────────────────┐
│    Aggregate Device "Zoom Input"   │
│  • BlackHole 2ch                   │
│  • MacBook Microphone              │
└────────────┬───────────────────────┘
             │
             v
        ┌────────┐
        │  ZOOM  │ ← звонок идёт
        └────┬───┘
             │
             v
┌────────────────────────────────────┐
│  Multi-Output "Zoom Output"        │
│  • BlackHole 2ch  ← захват         │
│  • Твои наушники  ← ты слышишь     │
└────────┬───────────────────────────┘
         │
    ┌────┴─────┐
    │          │
    v          v
┌─────────┐  ┌──────────────┐
│Наушники │  │  BlackHole   │
│(слышишь)│  │(виртуальный  │
└─────────┘  │   кабель)    │
             └──────┬───────┘
                    │
                    v
        ┌───────────────────────┐
        │  Твоё приложение      │
        │  • Захватывает аудио  │
        │  • Whisper → text     │
        │  • LLM → подсказки    │
        └───────────────────────┘
```

**Результат:**
- ✅ Ты слышишь клиента в наушниках
- ✅ Клиент слышит тебя
- ✅ Твоё приложение получает оба голоса
- ✅ Без эха, без петель

---

## 🚀 Установка (пошагово)

### Шаг 1: Установи BlackHole

**Вариант A: Через Homebrew**
```bash
# В новом терминале
brew install blackhole-2ch
# Введи пароль Mac
```

**Вариант B: Вручную**
1. Открой: https://existential.audio/blackhole/
2. Скачай **BlackHole 2ch.pkg**
3. Установи (двойной клик)

⚠️ **ВАЖНО: Перезагрузи Mac после установки!**

---

### Шаг 2: Проверь установку

После перезагрузки выполни:
```bash
system_profiler SPAudioDataType | grep BlackHole
```

Должно показать: `BlackHole 2ch`

---

### Шаг 3: Открой Audio MIDI Setup

```bash
open -a 'Audio MIDI Setup'
```

Или: `Spotlight (Cmd+Space)` → напиши "Audio MIDI"

---

### Шаг 4: Создай Multi-Output Device

**В Audio MIDI Setup:**

1. Нажми **"+"** (внизу слева)
2. Выбери **"Create Multi-Output Device"**
3. Поставь галочки:
   - ✅ **BlackHole 2ch**
   - ✅ **Твои наушники** (например "AirPods" или "External Headphones")
4. **Двойной клик** на название → назови: **"Zoom Output"**

![Multi-Output Device](https://docs-cdn.existential.audio/blackhole/multi-output.png)

---

### Шаг 5: Создай Aggregate Device

**В том же Audio MIDI Setup:**

1. Нажми **"+"** снова
2. Выбери **"Create Aggregate Device"**
3. Поставь галочки:
   - ✅ **BlackHole 2ch**
   - ✅ **Твой микрофон** (например "MacBook Pro Microphone")
4. Назови: **"Zoom Input"**

---

### Шаг 6: Настрой Zoom

1. **Zoom → Settings (⚙️) → Audio**

2. **Speaker:** выбери **"Zoom Output"**

3. **Microphone:** выбери **"Zoom Input"**

4. **Включи:**
   - ✅ "Original Sound for Musicians"
   - ✅ "Echo Cancellation" (можно оставить)

5. **Выключи:**
   - ❌ "Suppress background noise" (важно для качества)

6. **Нажми "Test Speaker" и "Test Mic"** - должно работать!

---

### Шаг 7: Настрой твоё приложение

1. **Запусти бэкенд** (если не запущен):
```bash
cd /Users/pavelloucker/SalesBestFriend/backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

2. **Запусти фронтенд** (если не запущен):
```bash
cd /Users/pavelloucker/SalesBestFriend/frontend
npm run dev
```

3. **Открой приложение** в браузере: http://localhost:5173

4. **Нажми "🔴 Start Live Recording"**

5. **В диалоге выбора аудио:**
   - Выбери **"BlackHole 2ch"** (не "Zoom Input"!)

---

## ✅ Тест

### Быстрый тест:

1. **Открой Zoom тестовый звонок:**
   - https://zoom.us/test

2. **В твоём приложении:**
   - Должна появиться кнопка "⏸ Pause Recording" (значит записывает)

3. **Говори что-то** в микрофон:
   - Через 10 секунд должна появиться транскрипция
   - Если скажешь "it's too expensive" → появится подсказка 💰

### Что должно работать:

- ✅ Ты слышишь Zoom audio в наушниках
- ✅ В Zoom test другая сторона слышит тебя
- ✅ В твоём приложении появляются транскрипции
- ✅ Подсказки срабатывают на триггеры
- ✅ Чеклист обновляется

---

## 🐛 Troubleshooting

### Проблема 1: "Не слышу звук в наушниках"

**Решение:**
- Audio MIDI Setup → Multi-Output "Zoom Output"
- Проверь что галочка стоит у **твоих наушников**
- Проверь что наушники **подключены** (Bluetooth/USB)

### Проблема 2: "Меня не слышат в Zoom"

**Решение:**
- Zoom → Settings → Audio → Microphone
- Проверь что выбран **"Zoom Input"** (не системный микрофон)
- Нажми "Test Mic" - должна двигаться полоска

### Проблема 3: "Транскрипции не появляются"

**Решение:**
```bash
# Проверь логи бэкенда
tail -f /Users/pavelloucker/SalesBestFriend/backend/logs/backend.log
```

Должны быть строки:
```
✅ Transcribed: 152 chars - "Hello this is a test..."
```

Если `Transcribed: 0 chars - ''` → значит аудио не захватывается:
- Проверь что в браузере выбрал **"BlackHole 2ch"**
- Перезапусти запись ("Stop" → "Start Live Recording")

### Проблема 4: "Эхо или feedback"

**Решение:**
- **НЕ** выбирай "Zoom Input" в браузере (только BlackHole!)
- Убедись что Multi-Output настроен правильно
- В Zoom включи "Echo Cancellation"

### Проблема 5: "BlackHole не появляется в списке"

**Решение:**
```bash
# Проверь установлен ли BlackHole
system_profiler SPAudioDataType | grep BlackHole
```

Если не показывает:
- Переустанови BlackHole
- **Обязательно перезагрузи Mac**
- После перезагрузки должен появиться

---

## 🎯 Автоматический скрипт

Я создал скрипт который проверяет установку:

```bash
cd /Users/pavelloucker/SalesBestFriend
./setup_zoom_audio.sh
```

Он проведёт тебя через все шаги настройки! 🚀

---

## 💡 Полезные команды

### Проверить аудио устройства:
```bash
system_profiler SPAudioDataType
```

### Проверить работает ли бэкенд:
```bash
curl http://localhost:8000/api/health
```

### Посмотреть логи в реальном времени:
```bash
tail -f /Users/pavelloucker/SalesBestFriend/backend/logs/backend.log
```

---

## 📚 Дополнительные ресурсы

- **BlackHole официальный сайт:** https://existential.audio/blackhole/
- **BlackHole Wiki:** https://github.com/ExistentialAudio/BlackHole/wiki
- **Zoom Audio Settings:** https://support.zoom.us/hc/en-us/articles/201362623

---

## ✨ Готово!

После настройки твоя система будет:
- 🎧 Работать с любыми наушниками (Bluetooth/проводные)
- 🎤 Захватывать оба голоса (твой + клиента)
- 🚀 Давать подсказки в реальном времени
- 📊 Обновлять чеклист автоматически

**Удачных продаж!** 💰

