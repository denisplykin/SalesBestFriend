# 🔄 Trial Class Sales Assistant - Refactor Summary

## 📋 Overview

This refactor transforms the Sales Best Friend into a **focused, real-time sales assistant** specifically designed for **Zoom trial class calls** in **Bahasa Indonesia**.

---

## 🎯 Key Changes

### **1. Focus Shift**
- **Before**: General-purpose sales coach with post-call analytics
- **After**: Real-time assistant for trial class calls only
- **Result**: Simpler, faster, more targeted

### **2. New Configuration System**
- **Structured stages** with timing budgets
- **Configurable checklist items** per stage
- **Structured client card fields**
- **All configurable** without code changes

### **3. Minimal UI Design**
- Clean, whitespace-heavy interface
- Unobtrusive for screen sharing
- Clear hierarchy and typography
- Follows Claude's design principles

---

## 📁 New File Structure

### **Backend**

```
backend/
├── main_trial_class.py          # NEW: Refactored main app
├── call_structure_config.py     # NEW: Stage/timing configuration
├── client_card_config.py        # NEW: Client card fields
├── trial_class_analyzer.py      # NEW: LLM analyzer for trial classes
├── main.py                      # OLD: Keep for reference
└── utils/                       # Existing utilities (unchanged)
```

### **Frontend**

```
frontend/src/
├── App_TrialClass.tsx           # NEW: Main app (minimal design)
├── App_TrialClass.css           # NEW: Main styles
├── components/
│   ├── StageChecklist.tsx       # NEW: Stages with timing
│   ├── StageChecklist.css
│   ├── CallTimer.tsx            # NEW: Simple timer
│   ├── CallTimer.css
│   ├── ClientCard.tsx           # NEW: Structured client info
│   ├── ClientCard.css
│   ├── SettingsPanel.tsx        # NEW: Configuration UI
│   ├── SettingsPanel.css
│   ├── CallChecklist.tsx        # OLD: Keep for reference
│   ├── ClientInfoSummary.tsx    # OLD: Keep for reference
│   └── NextStepCard.tsx         # OLD: Keep for reference
├── App.tsx                      # OLD: Keep for reference
└── App.css                      # OLD: Keep for reference
```

---

## 🚀 How to Run

### **Option 1: Use New Trial Class Version**

#### Backend:
```bash
cd backend
source venv/bin/activate

# Run the NEW main file
python main_trial_class.py
# OR
uvicorn main_trial_class:app --reload --port 8000
```

#### Frontend:
Update `frontend/src/main.tsx` to use the new App:

```typescript
// Change this line:
import App from './App.tsx'

// To this:
import App from './App_TrialClass.tsx'
```

Then start frontend:
```bash
cd frontend
npm run dev
```

### **Option 2: Keep Both Versions**

You can keep both the old and new versions by:
1. Running old version on port 8000
2. Running new version on port 8001

---

## 🎨 Design Principles Applied

Based on [Claude's Frontend Design Skills](https://github.com/anthropics/skills/blob/main/frontend-design/SKILL.md):

### **1. Clear Hierarchy**
- Large, bold titles for sections
- Consistent sizing: h1 (1.25rem) → h2 (1.125rem) → h3 (1rem)
- Visual weight through font-weight, not color

### **2. Plenty of Whitespace**
- Generous padding: 1.5-2rem
- Gap between elements: 0.75-1.5rem
- No dense, cramped layouts

### **3. Minimal Colors**
- Base: White background, dark gray text (#111827)
- Accent: Green (#10b981) for success/active states
- Neutral: Gray scale (#f3f4f6, #9ca3af, #6b7280)
- Alerts: Yellow (#f59e0b) for warnings, Red (#ef4444) for errors

### **4. Subtle Interactions**
- Small shadows: `0 1px 3px rgba(0, 0, 0, 0.05)`
- Smooth transitions: `0.15s ease`
- Hover states: Slightly darker/lighter, not jarring

### **5. Typography**
- System fonts for speed and familiarity
- Tabular numbers for timer/counters
- Clear line-height: 1.5-1.8 for readability

---

## 🔧 Configuration

### **1. Call Structure**

Edit `backend/call_structure_config.py`:

```python
DEFAULT_CALL_STRUCTURE = [
    {
        "id": "stage_1_opening",
        "name": "Opening & Greeting",
        "startOffsetSeconds": 0,      # When this stage starts
        "durationSeconds": 120,        # How long it should last
        "items": [
            {
                "id": "greet_client",
                "type": "say",         # "say" or "discuss"
                "content": "Greet the client warmly"
            },
            # ... more items
        ]
    },
    # ... more stages
]
```

### **2. Client Card Fields**

Edit `backend/client_card_config.py`:

```python
DEFAULT_CLIENT_CARD_FIELDS = [
    {
        "id": "child_name",
        "label": "Child's Name",
        "hint": "Name and age of the child",
        "multiline": False,
        "category": "child_info"  # Grouping for UI
    },
    # ... more fields
]
```

### **3. Language**

Set in frontend Settings panel or via WebSocket:

```typescript
// Indonesian (default)
selectedLanguage = 'id'

// English
selectedLanguage = 'en'

// Russian
selectedLanguage = 'ru'
```

---

## 📡 API Changes

### **WebSocket `/coach` Payload (NEW)**

```typescript
interface CoachMessage {
  type: 'initial' | 'update',
  callElapsedSeconds: number,
  currentStageId: string,
  stages: [
    {
      id: string,
      name: string,
      startOffsetSeconds: number,
      durationSeconds: number,
      items: [
        {
          id: string,
          type: 'discuss' | 'say',
          content: string,
          completed: boolean,
          evidence: string
        }
      ],
      isCurrent: boolean,
      timingStatus: 'not_started' | 'on_time' | 'slightly_late' | 'very_late',
      timingMessage: string
    }
  ],
  clientCard: {
    field_id: "extracted text"
  },
  transcriptPreview: string
}
```

### **WebSocket `/coach` Commands (NEW)**

Frontend can send these commands:

```typescript
// Manual checkbox toggle
{
  type: 'manual_toggle_item',
  item_id: 'greet_client'
}

// Update client card field
{
  type: 'update_client_card',
  field_id: 'child_name',
  value: 'Budi, 10 years old'
}

// Set language
{
  type: 'set_language',
  language: 'id'
}
```

### **New HTTP Endpoints**

```
GET  /api/config/call-structure    # Get current structure
POST /api/config/call-structure    # Update structure

GET  /api/config/client-card        # Get field definitions
POST /api/config/client-card        # Update fields
```

---

## 🎯 UI Components

### **1. StageChecklist**

**Features:**
- Shows all stages with timing
- Collapsible/expandable stages
- Current stage highlighted
- Progress per stage
- Timing status badges (on time / late)
- Manual checkbox override

**Location:** Left panel (main area)

### **2. ClientCard**

**Features:**
- Structured fields organized by category
- Auto-filled by AI (🤖 indicator)
- Manually editable
- Shows fill progress (X/11 filled)
- Categories:
  - 👶 Child Information
  - 👨‍👩‍👧 Parent & Goals
  - 🎯 Needs & Outcomes
  - ⚠️ Concerns
  - 📝 Notes

**Location:** Right panel

### **3. CallTimer**

**Features:**
- Simple elapsed time display
- Tabular numbers for clarity
- Format: MM:SS or H:MM:SS

**Location:** Top bar

### **4. SettingsPanel**

**Features:**
- Language selection
- Configuration UI (coming soon for structure/fields)
- Modal overlay

**Location:** Triggered by ⚙️ button in top bar

---

## 🔄 Migration Guide

### **If you want to keep the old version:**

1. Rename files:
   ```bash
   mv backend/main.py backend/main_old.py
   mv frontend/src/App.tsx frontend/src/App_Old.tsx
   ```

2. Use new files as default

### **If you want to switch back and forth:**

Keep both versions and change the import in `frontend/src/main.tsx`:

```typescript
// For old version:
import App from './App.tsx'

// For new version:
import App from './App_TrialClass.tsx'
```

---

## 🧪 Testing

### **Test Scenarios**

1. **Basic Flow**
   - Start session → Capture Zoom audio
   - Speak in Indonesian
   - Check if stages update
   - Check if client card fills
   - Verify timing indicators

2. **Manual Override**
   - Click checkboxes manually
   - Edit client card fields
   - Verify changes persist

3. **Configuration**
   - Change language in Settings
   - Verify transcription uses new language

4. **Edge Cases**
   - Stop/restart session
   - Long call (> 45 min)
   - No audio (verify graceful handling)
   - Network disconnect/reconnect

---

## 📊 Performance

### **Latency**

```
Audio chunk → Transcription → Analysis → UI Update
0.5s         2-3s            1-2s       0.05s
Total: ~4-6 seconds
```

### **Cost (per minute)**

With Claude 3 Haiku:
- Transcription (Whisper): 6 calls/min
- Item checks: ~2-4 LLM calls/item (with caching)
- Client card: 1 call per new info
- **Total: ~$0.01-0.03/min**

### **Optimization**

- 30s cooldown between item checks
- 60s LLM response cache
- Permanent completion (never re-check)
- 10s transcription intervals (not 5s)

---

## 🚧 Known Limitations (MVP)

1. **Configuration UI**: Settings UI for structure/fields is placeholder (edit Python files)
2. **localStorage**: Config not yet persisted in browser
3. **Multi-user**: One session at a time
4. **History**: No call history saved
5. **Analytics**: No post-call reports

---

## 🔮 Future Enhancements

### **Planned for v2.0**

- [ ] Full configuration UI (drag-drop stage editor)
- [ ] localStorage persistence
- [ ] Multi-user support with session IDs
- [ ] Call history and recordings
- [ ] Post-call summary reports
- [ ] Export to PDF/CSV
- [ ] Integration with Zoom SDK (no screen capture needed)
- [ ] Mobile responsive design
- [ ] Offline mode

---

## 📝 Developer Notes

### **Code Organization**

```
Backend:
- Config files are pure Python (easy to edit)
- Main app uses configs dynamically
- Analyzer is stateless (for scaling)

Frontend:
- Components are self-contained
- CSS is modular (one file per component)
- Types are clearly defined
- No global state (except WebSocket refs)
```

### **Adding a New Stage**

1. Edit `backend/call_structure_config.py`
2. Add to `DEFAULT_CALL_STRUCTURE` array
3. Set `startOffsetSeconds` and `durationSeconds`
4. Add items with `id`, `type`, `content`
5. Restart backend → UI updates automatically

### **Adding a Client Card Field**

1. Edit `backend/client_card_config.py`
2. Add to `DEFAULT_CLIENT_CARD_FIELDS` array
3. Set `id`, `label`, `hint`, `multiline`, `category`
4. Add extraction hint to `LLM_EXTRACTION_HINTS`
5. Restart backend → UI updates automatically

---

## 🎓 Design Resources

- [Claude Frontend Design Skill](https://github.com/anthropics/skills/blob/main/frontend-design/SKILL.md)
- [Claude Design Blog Post](https://claude.com/blog/improving-frontend-design-through-skills)

Key Takeaways:
- **Whitespace** is your friend
- **Hierarchy** through size and weight
- **Subtle** colors and interactions
- **Consistency** in spacing and sizing

---

## 📞 Support

For questions or issues:
1. Check `PRODUCT_ARCHITECTURE.md` for system overview
2. Check `REFACTOR_SUMMARY.md` (this file) for changes
3. Check code comments in new files
4. GitHub Issues (if applicable)

---

## ✅ Checklist for Going Live

- [ ] Backend running on production server
- [ ] Frontend built and deployed
- [ ] OpenRouter API key configured
- [ ] FFmpeg installed on server
- [ ] Language set to Indonesian (id)
- [ ] Call structure reviewed and approved
- [ ] Client card fields reviewed and approved
- [ ] Tested with real Zoom calls
- [ ] Sales team trained on UI
- [ ] Backup/fallback plan ready

---

**Last Updated**: 2025-11-19
**Version**: 2.0.0
**Status**: MVP Ready for Testing

🚀 **Happy Coaching!**

