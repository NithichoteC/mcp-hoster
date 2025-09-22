import { useState } from 'react'
import { ClipboardIcon, CheckIcon } from '@heroicons/react/24/outline'

export function ConnectionInfo() {
  const [copiedItem, setCopiedItem] = useState<string | null>(null)

  const copyToClipboard = (text: string, item: string) => {
    navigator.clipboard.writeText(text)
    setCopiedItem(item)
    setTimeout(() => setCopiedItem(null), 2000)
  }

  const baseUrl = 'your-domain.com' // In real app, this would be dynamic

  const connections = [
    {
      id: 'chatgpt',
      title: 'ChatGPT Custom Connector',
      description: 'Use this URL in ChatGPT\'s custom connector settings',
      url: `https://${baseUrl}/api/mcp/chatgpt`,
      instructions: 'Go to ChatGPT → Settings → Custom Connectors → Add New'
    },
    {
      id: 'claude',
      title: 'Claude Desktop',
      description: 'Add this configuration to your Claude Desktop config',
      url: `https://${baseUrl}/api/mcp/claude`,
      instructions: 'Add to your Claude Desktop configuration file'
    },
    {
      id: 'websocket',
      title: 'WebSocket Endpoint',
      description: 'Direct WebSocket connection for custom integrations',
      url: `wss://${baseUrl}/ws/mcp`,
      instructions: 'Connect directly via WebSocket for custom AI agents'
    }
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">
          Connection Endpoints
        </h2>
        <p className="text-gray-600">
          Use these endpoints to connect your MCP servers to AI agents
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {connections.map((connection) => (
          <div key={connection.id} className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {connection.title}
            </h3>
            <p className="text-gray-600 text-sm mb-4">
              {connection.description}
            </p>

            {/* URL Display */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-medium text-gray-700">
                  Endpoint URL:
                </label>
                <button
                  onClick={() => copyToClipboard(connection.url, connection.id)}
                  className="inline-flex items-center text-xs text-blue-600 hover:text-blue-700"
                >
                  {copiedItem === connection.id ? (
                    <>
                      <CheckIcon className="h-3 w-3 mr-1" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <ClipboardIcon className="h-3 w-3 mr-1" />
                      Copy
                    </>
                  )}
                </button>
              </div>
              <code className="block p-3 bg-gray-100 rounded text-xs text-gray-800 break-all">
                {connection.url}
              </code>
            </div>

            {/* Instructions */}
            <div className="text-xs text-gray-500 bg-blue-50 p-3 rounded">
              <strong>How to use:</strong> {connection.instructions}
            </div>
          </div>
        ))}
      </div>

      {/* Additional Info */}
      <div className="mt-8 p-6 bg-gray-50 rounded-lg">
        <h3 className="text-lg font-medium text-gray-900 mb-3">
          Quick Setup Guide
        </h3>
        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex items-start">
            <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded mr-3 mt-0.5">1</span>
            <span>Add an MCP server using the form above</span>
          </div>
          <div className="flex items-start">
            <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded mr-3 mt-0.5">2</span>
            <span>Start the server by clicking the play button</span>
          </div>
          <div className="flex items-start">
            <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded mr-3 mt-0.5">3</span>
            <span>Copy the appropriate endpoint URL above</span>
          </div>
          <div className="flex items-start">
            <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded mr-3 mt-0.5">4</span>
            <span>Configure your AI agent with the copied URL</span>
          </div>
        </div>
      </div>
    </div>
  )
}