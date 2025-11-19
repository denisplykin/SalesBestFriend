#!/bin/bash

# 🎧 Скрипт для настройки Zoom аудио с наушниками через BlackHole

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🎧 НАСТРОЙКА ZOOM + BLACKHOLE + НАУШНИКИ                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Проверка установлен ли BlackHole
if system_profiler SPAudioDataType | grep -q "BlackHole 2ch"; then
    echo "✅ BlackHole 2ch установлен!"
else
    echo "❌ BlackHole не найден!"
    echo ""
    echo "Установи BlackHole:"
    echo "  1. Открой новый терминал"
    echo "  2. Выполни: brew install blackhole-2ch"
    echo "  3. Перезагрузи Mac"
    echo "  4. Запусти этот скрипт снова"
    echo ""
    exit 1
fi

echo ""
echo "📋 Теперь настрой вручную (займёт 3 минуты):"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Шаг 1: Открой Audio MIDI Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Выполни в терминале:"
echo "    open -a 'Audio MIDI Setup'"
echo ""
read -p "Нажми Enter когда откроешь..." dummy

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Шаг 2: Создай Multi-Output Device"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. Нажми '+' (внизу слева окна)"
echo "  2. Выбери: 'Create Multi-Output Device'"
echo "  3. Поставь галочки:"
echo "     ✅ BlackHole 2ch"
echo "     ✅ Твои наушники (например 'AirPods' или 'External Headphones')"
echo "  4. Назови: 'Zoom Output' (двойной клик на название)"
echo ""
read -p "Нажми Enter когда создашь..." dummy

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Шаг 3: Создай Aggregate Device"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. Нажми '+' снова"
echo "  2. Выбери: 'Create Aggregate Device'"
echo "  3. Поставь галочки:"
echo "     ✅ BlackHole 2ch"
echo "     ✅ Твой микрофон (например 'MacBook Pro Microphone')"
echo "  4. Назови: 'Zoom Input'"
echo ""
read -p "Нажми Enter когда создашь..." dummy

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Шаг 4: Настрой Zoom"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. Открой Zoom → Settings → Audio"
echo "  2. Speaker: выбери 'Zoom Output'"
echo "  3. Microphone: выбери 'Zoom Input'"
echo "  4. Включи 'Original Sound for Musicians'"
echo "  5. Выключи 'Suppress background noise'"
echo ""
read -p "Нажми Enter когда настроишь Zoom..." dummy

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Шаг 5: Настрой твоё приложение"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. Открой твоё приложение в браузере"
echo "  2. Нажми '🔴 Start Live Recording'"
echo "  3. В диалоге выбора аудио → выбери 'BlackHole 2ch'"
echo ""
read -p "Нажми Enter когда настроишь..." dummy

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ НАСТРОЙКА ЗАВЕРШЕНА!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Теперь:"
echo "  • Ты слышишь клиента в наушниках ✅"
echo "  • Клиент слышит тебя ✅"
echo "  • Твоё приложение захватывает оба голоса ✅"
echo "  • Без эха, без петель обратной связи ✅"
echo ""
echo "🎯 Протестируй:"
echo "  1. Зайди в Zoom тестовый звонок: https://zoom.us/test"
echo "  2. Говори что-то"
echo "  3. В твоём приложении должны появиться транскрипции"
echo ""
echo "Если что-то не работает - напиши мне в чате!"
echo ""

