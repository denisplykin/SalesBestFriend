/**
 * Debug Log Panel
 * 
 * Shows real-time AI decisions for debugging:
 * - Checklist item completions with reasoning
 * - Client field extractions
 * - Stage transitions
 * - Validation passes/failures
 */

import { useState, useEffect, useRef } from 'react'
import './DebugLogPanel.css'

interface LogEntry {
  timestamp: string
  type: string
  [key: string]: any // Backend sends flexible format
}

interface DebugLogPanelProps {
  logs: LogEntry[]
  isVisible: boolean
  onClose: () => void
}

// Helper to format log entry into display format
function formatLogEntry(log: LogEntry): {
  type: string
  action: string
  status: 'success' | 'warning' | 'error' | 'info'
  details: Record<string, any>
} {
  const type = log.type || 'unknown'
  let action = ''
  let status: 'success' | 'warning' | 'error' | 'info' = 'info'
  const details: Record<string, any> = {}

  if (type === 'checklist_item') {
    action = log.item_content || 'Checklist item checked'
    status = log.completed ? 'success' : 'info'
    details.item = log.item_content
    details.confidence = log.confidence
    details.evidence = log.first_evidence || log.evidence
    details.reasoning = log.first_reasoning || log.reasoning
    details.validated = log.validation_passed
  } else if (type === 'duplicate_evidence') {
    action = `Duplicate evidence detected for ${log.item_id}`
    status = 'warning'
    details.item = log.item_id
    details.evidence = log.evidence
    details.duplicate_of = log.duplicate_of
  } else if (type === 'client_field') {
    action = `Client field: ${log.field_id || 'extracted'}`
    status = log.validated ? 'success' : 'warning'
    details.field = log.field_id
    details.value = log.value
    details.evidence = log.evidence
    details.confidence = log.confidence
  } else if (type === 'stage_transition') {
    action = `Stage transition: ${log.from_stage} → ${log.to_stage}`
    status = 'info'
    details.stage = log.to_stage
    details.confidence = log.confidence
  } else {
    action = JSON.stringify(log).substring(0, 100)
    status = 'info'
  }

  return { type, action, status, details }
}

export default function DebugLogPanel({ logs, isVisible, onClose }: DebugLogPanelProps) {
  const [filter, setFilter] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const logsEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Auto-scroll to bottom when new logs arrive
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  if (!isVisible) return null

  const filteredLogs = logs.filter(log => {
    if (filter !== 'all' && log.type !== filter) return false
    if (searchTerm && !JSON.stringify(log).toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return '#10b981'
      case 'warning': return '#f59e0b'
      case 'error': return '#ef4444'
      default: return '#6b7280'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'checklist_item': return '📋'
      case 'client_field': return '👤'
      case 'stage_transition': return '🔄'
      case 'duplicate_evidence': return '⚠️'
      default: return '📝'
    }
  }

  return (
    <div className="debug-log-overlay">
      <div className="debug-log-panel">
        {/* Header */}
        <div className="debug-log-header">
          <h2>🐛 Debug Log</h2>
          <button onClick={onClose} className="close-btn">✕</button>
        </div>

        {/* Filters */}
        <div className="debug-log-filters">
          <div className="filter-buttons">
            <button 
              className={filter === 'all' ? 'active' : ''}
              onClick={() => setFilter('all')}
            >
              All ({logs.length})
            </button>
            <button 
              className={filter === 'checklist_item' ? 'active' : ''}
              onClick={() => setFilter('checklist_item')}
            >
              📋 Checklist
            </button>
            <button 
              className={filter === 'client_field' ? 'active' : ''}
              onClick={() => setFilter('client_field')}
            >
              👤 Client
            </button>
            <button 
              className={filter === 'stage_transition' ? 'active' : ''}
              onClick={() => setFilter('stage_transition')}
            >
              🔄 Stages
            </button>
            <button 
              className={filter === 'duplicate_evidence' ? 'active' : ''}
              onClick={() => setFilter('duplicate_evidence')}
            >
              ⚠️ Duplicates
            </button>
          </div>

          <input
            type="text"
            placeholder="Search logs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>

        {/* Logs */}
        <div className="debug-log-content">
          {filteredLogs.length === 0 ? (
            <div className="no-logs">
              <p>No logs yet. Start recording to see AI decisions in real-time.</p>
            </div>
          ) : (
            filteredLogs.map((log, index) => {
              const formatted = formatLogEntry(log)
              return (
                <div 
                  key={index} 
                  className="log-entry"
                  style={{ borderLeftColor: getStatusColor(formatted.status) }}
                >
                  <div className="log-header">
                    <span className="log-icon">{getTypeIcon(formatted.type)}</span>
                    <span className="log-time">{log.timestamp}</span>
                    <span 
                      className="log-status"
                      style={{ backgroundColor: getStatusColor(formatted.status) }}
                    >
                      {formatted.status}
                    </span>
                  </div>

                  <div className="log-action">{formatted.action}</div>

                  <div className="log-details">
                    {formatted.details.item && (
                      <div className="detail-row">
                        <strong>Item:</strong> {formatted.details.item}
                      </div>
                    )}
                    
                    {formatted.details.field && (
                      <div className="detail-row">
                        <strong>Field:</strong> {formatted.details.field}
                      </div>
                    )}

                    {formatted.details.stage && (
                      <div className="detail-row">
                        <strong>Stage:</strong> {formatted.details.stage}
                      </div>
                    )}

                    {formatted.details.confidence !== undefined && (
                      <div className="detail-row">
                        <strong>Confidence:</strong> {(formatted.details.confidence * 100).toFixed(0)}%
                      </div>
                    )}

                    {formatted.details.evidence && (
                      <div className="detail-row">
                        <strong>Evidence:</strong>
                        <div className="evidence-text">{formatted.details.evidence}</div>
                      </div>
                    )}

                    {formatted.details.reasoning && (
                      <div className="detail-row">
                        <strong>Reasoning:</strong>
                        <div className="reasoning-text">{formatted.details.reasoning}</div>
                      </div>
                    )}

                    {formatted.details.validated !== undefined && (
                      <div className="detail-row">
                        <strong>Validated:</strong> {formatted.details.validated ? '✅ Pass' : '❌ Fail'}
                      </div>
                    )}

                    {formatted.details.duplicate_of && (
                      <div className="detail-row">
                        <strong>Duplicate of:</strong> {formatted.details.duplicate_of}
                      </div>
                    )}
                  </div>
                </div>
              )
            })
          )}
          <div ref={logsEndRef} />
        </div>

        {/* Footer */}
        <div className="debug-log-footer">
          <button onClick={() => {/* Clear logs */}} className="clear-btn">
            🗑️ Clear Logs
          </button>
          <button onClick={() => {/* Export logs */}} className="export-btn">
            📥 Export JSON
          </button>
        </div>
      </div>
    </div>
  )
}

