import { ServerCard } from './ServerCard'
import { Server } from '@/types'

interface ServerListProps {
  servers: Server[]
  loading: boolean
  onRefresh: () => void
}

export function ServerList({ servers, loading, onRefresh }: ServerListProps) {
  if (loading) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-gray-900">Your MCP Servers</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg shadow p-6">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
                <div className="h-8 bg-gray-200 rounded w-20"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold text-gray-900">
          Your MCP Servers {servers.length > 0 && `(${servers.length})`}
        </h2>
        {servers.length > 0 && (
          <button
            onClick={onRefresh}
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            Refresh
          </button>
        )}
      </div>

      {servers.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <div className="max-w-sm mx-auto">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No servers added yet
            </h3>
            <p className="text-gray-600">
              Add your first MCP server to get started connecting it to AI agents.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {servers.map((server) => (
            <ServerCard key={server.id} server={server} />
          ))}
        </div>
      )}
    </div>
  )
}