/**
 * Client Card Component
 * 
 * Structured fields for tracking client information.
 * - Auto-filled by AI
 * - Manually editable
 * - Organized by category
 */

import { useState } from 'react'
import './ClientCard.css'

interface ClientCardProps {
  data: Record<string, string>
  onUpdate: (fieldId: string, value: string) => void
}

// Field definitions (should match backend config)
const CLIENT_CARD_FIELDS = [
  // Child Info
  {
    id: 'child_name',
    label: 'Child\'s Name',
    category: 'child_info',
    multiline: false
  },
  {
    id: 'child_interests',
    label: 'Child\'s Interests',
    category: 'child_info',
    multiline: true
  },
  {
    id: 'child_experience',
    label: 'Prior Experience',
    category: 'child_info',
    multiline: true
  },
  
  // Parent Goals
  {
    id: 'parent_goal',
    label: 'Parent\'s Goal',
    category: 'parent_info',
    multiline: true
  },
  {
    id: 'learning_motivation',
    label: 'Why Learning Now',
    category: 'parent_info',
    multiline: true
  },
  
  // Needs
  {
    id: 'main_pain_point',
    label: 'Main Pain Point',
    category: 'needs',
    multiline: true
  },
  {
    id: 'desired_outcome',
    label: 'Desired Outcome',
    category: 'needs',
    multiline: true
  },
  
  // Concerns
  {
    id: 'objections',
    label: 'Objections Raised',
    category: 'concerns',
    multiline: true
  },
  {
    id: 'budget_constraint',
    label: 'Budget Situation',
    category: 'concerns',
    multiline: false
  },
  {
    id: 'schedule_constraint',
    label: 'Schedule Constraints',
    category: 'concerns',
    multiline: false
  },
  
  // Notes
  {
    id: 'additional_notes',
    label: 'Additional Notes',
    category: 'notes',
    multiline: true
  }
]

const CATEGORY_LABELS: Record<string, string> = {
  child_info: '👶 Child Information',
  parent_info: '👨‍👩‍👧 Parent & Goals',
  needs: '🎯 Needs & Outcomes',
  concerns: '⚠️ Concerns',
  notes: '📝 Notes'
}

export default function ClientCard({ data, onUpdate }: ClientCardProps) {
  const [editingField, setEditingField] = useState<string | null>(null)

  const fieldsByCategory = CLIENT_CARD_FIELDS.reduce((acc, field) => {
    if (!acc[field.category]) {
      acc[field.category] = []
    }
    acc[field.category].push(field)
    return acc
  }, {} as Record<string, typeof CLIENT_CARD_FIELDS>)

  const handleBlur = (fieldId: string, value: string) => {
    setEditingField(null)
    if (value !== data[fieldId]) {
      onUpdate(fieldId, value)
    }
  }

  const getFilledFieldCount = () => {
    return Object.values(data).filter(v => v && v.trim().length > 0).length
  }

  return (
    <div className="client-card">
      <div className="card-header">
        <h2 className="card-title">Client Information</h2>
        <span className="filled-count">
          {getFilledFieldCount()}/{CLIENT_CARD_FIELDS.length} filled
        </span>
      </div>

      <div className="card-content">
        {Object.entries(fieldsByCategory).map(([category, fields]) => (
          <div key={category} className="field-category">
            <h3 className="category-title">{CATEGORY_LABELS[category]}</h3>
            
            <div className="fields-list">
              {fields.map(field => {
                const value = data[field.id] || ''
                const isEditing = editingField === field.id
                const isEmpty = !value || value.trim().length === 0

                return (
                  <div 
                    key={field.id}
                    className={`field-wrapper ${isEmpty ? 'empty' : 'filled'}`}
                  >
                    <label className="field-label">{field.label}</label>
                    
                    {field.multiline ? (
                      <textarea
                        className="field-input"
                        value={value}
                        onChange={(e) => onUpdate(field.id, e.target.value)}
                        onFocus={() => setEditingField(field.id)}
                        onBlur={(e) => handleBlur(field.id, e.target.value)}
                        placeholder={`Enter ${field.label.toLowerCase()}...`}
                        rows={3}
                      />
                    ) : (
                      <input
                        type="text"
                        className="field-input"
                        value={value}
                        onChange={(e) => onUpdate(field.id, e.target.value)}
                        onFocus={() => setEditingField(field.id)}
                        onBlur={(e) => handleBlur(field.id, e.target.value)}
                        placeholder={`Enter ${field.label.toLowerCase()}...`}
                      />
                    )}
                    
                    {!isEmpty && !isEditing && (
                      <span className="ai-indicator" title="AI extracted">🤖</span>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      {getFilledFieldCount() === 0 && (
        <div className="empty-state">
          <p>🎧 Listening for client information...</p>
          <p className="empty-hint">Information will be extracted automatically as the conversation progresses.</p>
        </div>
      )}
    </div>
  )
}

