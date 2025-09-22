import { useState } from 'react'
import { PlayIcon, StopIcon, TrashIcon } from '@heroicons/react/24/outline'
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/solid'
import { Server } from '@/types'

interface ServerCardProps {
  server: Server
}

export function ServerCard({ server }: ServerCardProps) {
  const [loading, setLoading] = useState(false)

  const handleToggleStatus = async () => {
    setLoading(true)
    try {
      // In a real app, this would call the API
      await new Promise(resolve => setTimeout(resolve, 1000))
    } catch (error) {
      console.error('Failed to toggle server status:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this server?')) return

    setLoading(true)
    try {
      // In a real app, this would call the API
      await new Promise(resolve => setTimeout(resolve, 1000))
    } catch (error) {
      console.error('Failed to delete server:', error)
    } finally {
      setLoading(false)
    }
  }

  const isRunning = server.status === 'running'

  return (
    <div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            {server.name}
          </h3>
          <div className="flex items-center">
            {isRunning ? (
              <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1" />
            ) : (
              <XCircleIcon className="h-4 w-4 text-red-500 mr-1" />
            )}
            <span className={`text-sm font-medium ${
              isRunning ? 'text-green-600' : 'text-red-600'
            }`}>
              {isRunning ? 'Running' : 'Stopped'}
            </span>
          </div>
        </div>
      </div>

      {/* Description */}
      {server.description && (
        <p className="text-gray-600 text-sm mb-4 line-clamp-2">
          {server.description}
        </p>
      )}

      {/* GitHub URL */}
      {server.github_url && (
        <div className="mb-4">
          <a
            href={server.github_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            View on GitHub →
          </a>
        </div>
      )}

      {/* Connection Endpoint */}
      <div className="mb-4 p-3 bg-gray-50 rounded border">
        <div className="text-xs font-medium text-gray-700 mb-1">Endpoint:</div>
        <code className="text-xs text-gray-900 break-all">
          {server.endpoint || `ws://localhost:8000/mcp/${server.id}`}
        </code>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <button
          onClick={handleToggleStatus}
          disabled={loading}
          className={`inline-flex items-center px-3 py-1.5 text-sm font-medium rounded transition-colors disabled:opacity-50 ${
            isRunning
              ? 'bg-red-100 text-red-700 hover:bg-red-200'
              : 'bg-green-100 text-green-700 hover:bg-green-200'
          }`}
        >
          {loading ? (
            <div className="h-4 w-4 mr-1.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
          ) : isRunning ? (
            <StopIcon className="h-4 w-4 mr-1.5" />
          ) : (
            <PlayIcon className="h-4 w-4 mr-1.5" />
          )}
          {loading ? 'Loading...' : isRunning ? 'Stop' : 'Start'}
        </button>

        <button
          onClick={handleDelete}
          disabled={loading}
          className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-red-600 hover:text-red-700 transition-colors disabled:opacity-50"
        >
          <TrashIcon className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}