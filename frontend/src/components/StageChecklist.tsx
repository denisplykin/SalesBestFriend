/**
 * Stage Checklist Component
 * 
 * Shows call stages with:
 * - Time budget per stage
 * - Progress indicators
 * - Timing status (on time / late)
 * - Checklist items with manual override
 */

import { useState } from 'react'
import './StageChecklist.css'

interface ChecklistItem {
  id: string
  type: 'discuss' | 'say'
  content: string
  completed: boolean
  evidence: string
}

interface Stage {
  id: string
  name: string
  startOffsetSeconds: number
  durationSeconds: number
  items: ChecklistItem[]
  isCurrent: boolean
  timingStatus: 'not_started' | 'on_time' | 'slightly_late' | 'very_late'
  timingMessage: string
}

interface StageChecklistProps {
  stages: Stage[]
  currentStageId: string
  callElapsed: number
  onManualToggle: (itemId: string) => void
}

export default function StageChecklist({ stages, currentStageId, callElapsed, onManualToggle }: StageChecklistProps) {
  const [expandedStages, setExpandedStages] = useState<Set<string>>(new Set())

  const toggleStage = (stageId: string) => {
    setExpandedStages(prev => {
      const next = new Set(prev)
      if (next.has(stageId)) {
        next.delete(stageId)
      } else {
        next.add(stageId)
      }
      return next
    })
  }

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getTimingBadgeColor = (status: string): string => {
    switch (status) {
      case 'on_time': return '#10b981'
      case 'slightly_late': return '#f59e0b'
      case 'very_late': return '#ef4444'
      default: return '#9ca3af'
    }
  }

  const getStageProgress = (stage: Stage) => {
    const completed = stage.items.filter(item => item.completed).length
    const total = stage.items.length
    return { completed, total, percentage: total > 0 ? Math.round((completed / total) * 100) : 0 }
  }

  return (
    <div className="stage-checklist">
      <h2 className="checklist-title">Call Structure</h2>
      
      <div className="stages-container">
        {stages.map((stage, index) => {
          const progress = getStageProgress(stage)
          const isExpanded = expandedStages.has(stage.id) || stage.isCurrent
          const stageStart = formatTime(stage.startOffsetSeconds)
          const stageEnd = formatTime(stage.startOffsetSeconds + stage.durationSeconds)

          return (
            <div 
              key={stage.id}
              className={`stage-block ${stage.isCurrent ? 'current' : ''}`}
            >
              {/* Stage Header */}
              <div 
                className="stage-header"
                onClick={() => toggleStage(stage.id)}
              >
                <div className="stage-header-left">
                  <span className="stage-number">{index + 1}</span>
                  <div className="stage-info">
                    <h3 className="stage-name">{stage.name}</h3>
                    <span className="stage-time">{stageStart} – {stageEnd}</span>
                  </div>
                </div>

                <div className="stage-header-right">
                  <span 
                    className="timing-badge"
                    style={{ backgroundColor: getTimingBadgeColor(stage.timingStatus) }}
                  >
                    {stage.timingMessage}
                  </span>
                  
                  <div className="progress-indicator">
                    <span className="progress-text">{progress.completed}/{progress.total}</span>
                    <div className="progress-bar-small">
                      <div 
                        className="progress-fill-small"
                        style={{ width: `${progress.percentage}%` }}
                      />
                    </div>
                  </div>

                  <button className="expand-btn">
                    {isExpanded ? '▼' : '▶'}
                  </button>
                </div>
              </div>

              {/* Stage Items (collapsible) */}
              {isExpanded && (
                <div className="stage-items">
                  {stage.items.map(item => (
                    <div 
                      key={item.id}
                      className={`checklist-item ${item.completed ? 'completed' : ''}`}
                    >
                      <label className="checkbox-wrapper">
                        <input 
                          type="checkbox"
                          checked={item.completed}
                          onChange={() => onManualToggle(item.id)}
                          className="checkbox-input"
                        />
                        <span className="checkbox-custom">
                          {item.completed && <span className="checkmark">✓</span>}
                        </span>
                      </label>

                      <div className="item-content">
                        <span className="item-type-badge">
                          {item.type === 'discuss' ? '💬 Discuss' : '💡 Say'}
                        </span>
                        <span className="item-text">{item.content}</span>
                        {item.completed && item.evidence && (
                          <span className="item-evidence" title={item.evidence}>
                            📋
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {stages.length === 0 && (
        <div className="empty-state">
          <p>⏳ Waiting for session to start...</p>
        </div>
      )}
    </div>
  )
}

