/**
 * Settings Panel Component
 * 
 * Modal for configuring:
 * - Call structure (stages, items, timing)
 * - Client card fields
 * - Language selection
 * 
 * For MVP: Simple interface with localStorage persistence
 */

import { useState, useEffect } from 'react'
import './SettingsPanel.css'

interface SettingsPanelProps {
  onClose: () => void
  selectedLanguage: string
  onLanguageChange: (lang: string) => void
}

const LANGUAGES = [
  { code: 'id', name: 'Bahasa Indonesia' },
  { code: 'en', name: 'English' },
  { code: 'ru', name: 'Русский' }
]

export default function SettingsPanel({ onClose, selectedLanguage, onLanguageChange }: SettingsPanelProps) {
  const [activeTab, setActiveTab] = useState<'general' | 'structure' | 'fields'>('general')

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-panel" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="settings-header">
          <h2>Settings</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        {/* Tabs */}
        <div className="settings-tabs">
          <button 
            className={`tab ${activeTab === 'general' ? 'active' : ''}`}
            onClick={() => setActiveTab('general')}
          >
            General
          </button>
          <button 
            className={`tab ${activeTab === 'structure' ? 'active' : ''}`}
            onClick={() => setActiveTab('structure')}
          >
            Call Structure
          </button>
          <button 
            className={`tab ${activeTab === 'fields' ? 'active' : ''}`}
            onClick={() => setActiveTab('fields')}
          >
            Client Fields
          </button>
        </div>

        {/* Content */}
        <div className="settings-content">
          {activeTab === 'general' && (
            <div className="settings-section">
              <h3>General Settings</h3>
              
              <div className="setting-item">
                <label className="setting-label">Conversation Language</label>
                <p className="setting-description">
                  Language spoken during the call (for transcription)
                </p>
                <select 
                  className="setting-select"
                  value={selectedLanguage}
                  onChange={(e) => onLanguageChange(e.target.value)}
                >
                  {LANGUAGES.map(lang => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="setting-item">
                <label className="setting-label">Interface Language</label>
                <p className="setting-description">
                  Interface is always in English (optimized for screen sharing)
                </p>
                <select className="setting-select" disabled>
                  <option>English</option>
                </select>
              </div>
            </div>
          )}

          {activeTab === 'structure' && (
            <div className="settings-section">
              <h3>Call Structure Configuration</h3>
              <p className="section-info">
                Configure stages and checklist items for your trial class flow.
              </p>
              
              <div className="coming-soon">
                <p>🚧 Configuration UI coming soon</p>
                <p className="coming-soon-details">
                  For now, call structure is defined in the backend configuration.
                  <br />
                  See <code>backend/call_structure_config.py</code>
                </p>
              </div>
            </div>
          )}

          {activeTab === 'fields' && (
            <div className="settings-section">
              <h3>Client Card Fields</h3>
              <p className="section-info">
                Configure which fields to track for client information.
              </p>
              
              <div className="coming-soon">
                <p>🚧 Configuration UI coming soon</p>
                <p className="coming-soon-details">
                  For now, client card fields are defined in the backend.
                  <br />
                  See <code>backend/client_card_config.py</code>
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="settings-footer">
          <button className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

