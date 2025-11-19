/**
 * Call Timer Component
 * 
 * Simple, clean timer showing elapsed call time.
 */

import './CallTimer.css'

interface CallTimerProps {
  elapsedSeconds: number
}

export default function CallTimer({ elapsedSeconds }: CallTimerProps) {
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="call-timer">
      <span className="timer-icon">⏱️</span>
      <span className="timer-value">{formatTime(elapsedSeconds)}</span>
    </div>
  )
}

