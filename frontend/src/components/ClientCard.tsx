/**
 * Client Card Component
 * 
 * Structured fields for tracking client information.
 * - Auto-filled by AI (read-only)
 * - Organized by category
 * - Updates in real-time during conversation
 */

import { useState } from 'react'
import './ClientCard.css'

interface ClientFieldData {
  value: string
  evidence?: string
  extractedAt?: string
}

interface ClientCardProps {
  data: Record<string, string | ClientFieldData>
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

export default function ClientCard({ data }: ClientCardProps) {
  const [detailsModal, setDetailsModal] = useState<{ field: typeof CLIENT_CARD_FIELDS[0]; data: ClientFieldData } | null>(null)

  const fieldsByCategory = CLIENT_CARD_FIELDS.reduce((acc, field) => {
    if (!acc[field.category]) {
      acc[field.category] = []
    }
    acc[field.category].push(field)
    return acc
  }, {} as Record<string, typeof CLIENT_CARD_FIELDS>)

  const getFieldValue = (fieldId: string): string => {
    const fieldData = data[fieldId]
    if (!fieldData) return ''
    if (typeof fieldData === 'string') return fieldData
    return fieldData.value || ''
  }

  const getFieldData = (fieldId: string): ClientFieldData => {
    const fieldData = data[fieldId]
    if (!fieldData) return { value: '' }
    if (typeof fieldData === 'string') return { value: fieldData }
    return fieldData
  }

  const getFilledFieldCount = () => {
    return Object.keys(data).filter(key => {
      const value = getFieldValue(key)
      return value && value.trim().length > 0
    }).length
  }

  const showDetails = (field: typeof CLIENT_CARD_FIELDS[0]) => {
    const fieldData = getFieldData(field.id)
    setDetailsModal({ field, data: fieldData })
  }

  const closeDetails = () => {
    setDetailsModal(null)
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
                const value = getFieldValue(field.id)
                const fieldData = getFieldData(field.id)
                const isEmpty = !value || value.trim().length === 0

                return (
                  <div 
                    key={field.id}
                    className={`field-wrapper ${isEmpty ? 'empty' : 'filled'}`}
                  >
                    <label className="field-label">
                      {field.label}
                      {!isEmpty && <span className="ai-indicator" title="AI extracted">🤖</span>}
                    </label>
                    
                    <div className="field-content-row">
                      <div className={`field-value ${field.multiline ? 'multiline' : ''}`}>
                        {isEmpty ? (
                          <span className="placeholder-text">Listening...</span>
                        ) : (
                          value
                        )}
                      </div>

                      {!isEmpty && fieldData.evidence && (
                        <button 
                          className="field-details-btn"
                          onClick={() => showDetails(field)}
                          title="Show extraction details"
                        >
                          Details
                        </button>
                      )}
                    </div>
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

      {/* Details Modal */}
      {detailsModal && (
        <div className="modal-overlay" onClick={closeDetails}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Field Details</h3>
              <button className="modal-close" onClick={closeDetails}>✕</button>
            </div>
            
            <div className="modal-body">
              <div className="detail-section">
                <label>Field:</label>
                <div className="detail-value">{detailsModal.field.label}</div>
              </div>

              <div className="detail-section">
                <label>Category:</label>
                <div className="detail-value">{CATEGORY_LABELS[detailsModal.field.category]}</div>
              </div>

              <div className="detail-section">
                <label>Extracted Value:</label>
                <div className="detail-value extracted-value">
                  {detailsModal.data.value}
                </div>
              </div>

              {detailsModal.data.extractedAt && (
                <div className="detail-section">
                  <label>Extracted At:</label>
                  <div className="detail-value">
                    {new Date(detailsModal.data.extractedAt).toLocaleString()}
                  </div>
                </div>
              )}

              <div className="detail-section">
                <label>Evidence / Source:</label>
                <div className="detail-value evidence-box">
                  {detailsModal.data.evidence || 'No evidence available'}
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-close" onClick={closeDetails}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

