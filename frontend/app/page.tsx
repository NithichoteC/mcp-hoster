'use client'

import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ServerIcon,
  ChatBubbleLeftRightIcon,
  GlobeAltIcon,
  ChartBarIcon,
  PlusIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline'
import { CheckCircleIcon, ExclamationTriangleIcon, XCircleIcon } from '@heroicons/react/24/solid'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { StatsCard } from '@/components/ui/StatsCard'
import { ServerCard } from '@/components/servers/ServerCard'
import { SystemHealth } from '@/components/dashboard/SystemHealth'
import { RecentActivity } from '@/components/dashboard/RecentActivity'
import { QuickActions } from '@/components/dashboard/QuickActions'
import { useApi } from '@/lib/api'
import { Server, SystemStatus } from '@/types'

export default function DashboardPage() {
  const api = useApi()

  // Fetch system status
  const { data: systemStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['system-status'],
    queryFn: () => api.get<SystemStatus>('/health'),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Fetch servers
  const { data: servers = [], isLoading: serversLoading } = useQuery({
    queryKey: ['servers'],
    queryFn: () => api.get<Server[]>('/api/v1/servers'),
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  // Stats data
  const stats = [
    {
      name: 'Total Servers',
      value: systemStatus?.total_servers || 0,
      icon: ServerIcon,
      change: '+2',
      changeType: 'positive' as const,
      description: 'MCP servers configured'
    },
    {
      name: 'Active Servers',
      value: systemStatus?.active_servers || 0,
      icon: CheckCircleIcon,
      change: `${systemStatus?.active_servers || 0}/${systemStatus?.total_servers || 0}`,
      changeType: 'neutral' as const,
      description: 'Currently running'
    },
    {
      name: 'Active Sessions',
      value: systemStatus?.active_sessions || 0,
      icon: ChatBubbleLeftRightIcon,
      change: '+1',
      changeType: 'positive' as const,
      description: 'Connected AI clients'
    },
    {
      name: 'Uptime',
      value: formatUptime(systemStatus?.uptime_seconds || 0),
      icon: ChartBarIcon,
      change: '99.9%',
      changeType: 'positive' as const,
      description: 'System availability'
    },
  ]

  // Recent servers (last 4)
  const recentServers = servers.slice(0, 4)

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="mt-1 text-sm text-gray-500">
              Monitor and manage your MCP servers and AI connections
            </p>
          </div>
          <QuickActions />
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <StatsCard
              key={stat.name}
              name={stat.name}
              value={stat.value}
              icon={stat.icon}
              change={stat.change}
              changeType={stat.changeType}
              description={stat.description}
              loading={statusLoading}
            />
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* System Health */}
          <div className="lg:col-span-2">
            <SystemHealth systemStatus={systemStatus} loading={statusLoading} />
          </div>

          {/* Recent Activity */}
          <div>
            <RecentActivity />
          </div>
        </div>

        {/* Recent Servers */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-medium text-gray-900">Recent Servers</h2>
            <button className="btn-secondary text-sm">
              View all servers
            </button>
          </div>

          {serversLoading ? (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="card">
                  <div className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
                    <div className="h-8 bg-gray-200 rounded w-20"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : recentServers.length > 0 ? (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {recentServers.map((server) => (
                <ServerCard key={server.id} server={server} compact />
              ))}
            </div>
          ) : (
            <div className="card text-center py-12">
              <ServerIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No servers</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by adding your first MCP server.
              </p>
              <div className="mt-6">
                <button className="btn-primary">
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Add Server
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Quick Setup Guide */}
        {servers.length === 0 && (
          <div className="card bg-gradient-to-r from-primary-50 to-indigo-50 border-primary-200">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <GlobeAltIcon className="h-8 w-8 text-primary-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-medium text-gray-900">
                  Welcome to MCP Host!
                </h3>
                <p className="mt-1 text-sm text-gray-600">
                  Get started by connecting your first MCP server. You can add servers from GitHub,
                  configure n8n integration, or set up custom servers.
                </p>
                <div className="mt-4 flex space-x-3">
                  <button className="btn-primary">
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Add from GitHub
                  </button>
                  <button className="btn-secondary">
                    <Cog6ToothIcon className="h-4 w-4 mr-2" />
                    Configure n8n
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`
  return `${Math.floor(seconds / 86400)}d`
}