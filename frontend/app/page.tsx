'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { PlusIcon } from '@heroicons/react/24/outline'
import { Layout } from '@/components/Layout'
import { AddServerForm } from '@/components/AddServerForm'
import { ServerList } from '@/components/ServerList'
import { ConnectionInfo } from '@/components/ConnectionInfo'
import { useApi } from '@/lib/api'
import { Server } from '@/types'

export default function HomePage() {
  const [showAddForm, setShowAddForm] = useState(false)
  const api = useApi()

  // Fetch servers
  const { data: servers = [], isLoading, refetch } = useQuery({
    queryKey: ['servers'],
    queryFn: () => api.get<Server[]>('/api/v1/servers'),
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            MCP Host
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Connect any MCP server to ChatGPT, Claude, or any AI agent.
            Simple, professional, and secure.
          </p>
        </div>

        {/* Add Server Button */}
        <div className="text-center mb-8">
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add MCP Server
          </button>
        </div>

        {/* Add Server Form */}
        {showAddForm && (
          <div className="mb-12">
            <AddServerForm
              onSuccess={() => {
                setShowAddForm(false)
                refetch()
              }}
              onCancel={() => setShowAddForm(false)}
            />
          </div>
        )}

        {/* Connection Info */}
        <div className="mb-12">
          <ConnectionInfo />
        </div>

        {/* Server List */}
        <div>
          <ServerList servers={servers} loading={isLoading} onRefresh={refetch} />
        </div>

        {/* Getting Started */}
        {servers.length === 0 && !showAddForm && (
          <div className="text-center py-16 bg-gray-50 rounded-lg">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Get Started
            </h3>
            <p className="text-gray-600 mb-6 max-w-md mx-auto">
              Add your first MCP server from GitHub to start connecting it to AI agents.
            </p>
            <button
              onClick={() => setShowAddForm(true)}
              className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Add Your First Server
            </button>
          </div>
        )}
      </div>
    </Layout>
  )
}