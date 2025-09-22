// Server types
export interface Server {
  id: number
  name: string
  description?: string
  github_url?: string
  command: string
  args: string[]
  env: Record<string, string>
  transport_type: TransportType
  host: string
  port?: number
  status: ServerStatus
  auth_type: AuthType
  auth_config: Record<string, any>
  created_at: string
  updated_at: string
  last_health_check?: string
  health_check_interval: number
  auto_restart: boolean
  max_restarts: number
  restart_count: number
}

export enum ServerStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  ERROR = 'error',
  STARTING = 'starting',
  STOPPING = 'stopping',
}

export enum TransportType {
  STDIO = 'stdio',
  HTTP = 'http',
  SSE = 'sse',
  STREAMABLE_HTTP = 'streamable_http',
}

export enum AuthType {
  NONE = 'none',
  OAUTH = 'oauth',
  API_KEY = 'api_key',
  BEARER = 'bearer',
}

// Server creation/update types
export interface CreateServerRequest {
  name: string
  description?: string
  github_url?: string
  command: string
  args?: string[]
  env?: Record<string, string>
  transport_type?: TransportType
  host?: string
  port?: number
  auth_type?: AuthType
  auth_config?: Record<string, any>
  auto_restart?: boolean
  max_restarts?: number
  health_check_interval?: number
}

export interface UpdateServerRequest extends Partial<CreateServerRequest> {}

// Health types
export interface HealthStatus {
  server_id: number
  status: ServerStatus
  last_check: string
  response_time_ms?: number
  error?: string
  tools_count?: number
  resources_count?: number
}

export interface SystemStatus {
  total_servers: number
  active_servers: number
  inactive_servers: number
  error_servers: number
  total_sessions: number
  active_sessions: number
  uptime_seconds: number
  memory_usage_mb: number
  cpu_usage_percent: number
}

// API Key types
export interface ApiKey {
  id: number
  name: string
  permissions: string[]
  created_at: string
  last_used?: string
  is_active: boolean
  expires_at?: string
}

export interface CreateApiKeyRequest {
  name: string
  permissions?: string[]
  expires_at?: string
}

export interface CreateApiKeyResponse extends ApiKey {
  api_key: string // Only returned on creation
}

// Session types
export interface Session {
  id: number
  session_id: string
  client_type: string
  client_info: Record<string, any>
  connected_servers: number[]
  created_at: string
  last_activity: string
  is_active: boolean
}

// Activity types
export interface Activity {
  id: number
  type: ActivityType
  title: string
  description: string
  metadata?: Record<string, any>
  created_at: string
  user?: string
  server_id?: number
}

export enum ActivityType {
  SERVER_CREATED = 'server_created',
  SERVER_STARTED = 'server_started',
  SERVER_STOPPED = 'server_stopped',
  SERVER_ERROR = 'server_error',
  SESSION_CREATED = 'session_created',
  SESSION_ENDED = 'session_ended',
  TOOL_CALLED = 'tool_called',
  ERROR_OCCURRED = 'error_occurred',
}

// MCP Protocol types
export interface McpTool {
  name: string
  description: string
  inputSchema: any
}

export interface McpResource {
  uri: string
  name: string
  description?: string
  mimeType?: string
}

export interface McpPrompt {
  name: string
  description: string
  arguments?: any
}

export interface McpCapabilities {
  resources?: {
    subscribe?: boolean
    listChanged?: boolean
  }
  tools?: Record<string, any>
  prompts?: Record<string, any>
  experimental?: Record<string, any>
}

// GitHub integration types
export interface GitHubRepo {
  name: string
  description: string
  url: string
  stars: number
  language: string
  updated_at: string
}

// Chart/metrics types
export interface MetricDataPoint {
  timestamp: string
  value: number
  label?: string
}

export interface ChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    borderColor?: string
    backgroundColor?: string
    fill?: boolean
  }[]
}

// UI component types
export interface SelectOption {
  value: string
  label: string
  description?: string
  disabled?: boolean
}

export interface TableColumn<T = any> {
  key: keyof T | string
  header: string
  cell?: (item: T) => React.ReactNode
  sortable?: boolean
  width?: string
  align?: 'left' | 'center' | 'right'
}

export interface PaginationInfo {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

// Form types
export interface FormFieldError {
  message: string
  type?: string
}

export interface FormState {
  errors: Record<string, FormFieldError>
  isSubmitting: boolean
  isValid: boolean
}

// Notification types
export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  actions?: NotificationAction[]
  autoClose?: boolean
  duration?: number
}

export interface NotificationAction {
  label: string
  action: () => void
  style?: 'primary' | 'secondary'
}

// WebSocket message types
export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

export interface ServerEventMessage extends WebSocketMessage {
  type: 'server_event'
  data: {
    server_id: number
    event: string
    status?: ServerStatus
    details?: any
  }
}

export interface ActivityEventMessage extends WebSocketMessage {
  type: 'activity'
  data: Activity
}

// Export utility types
export type ServerWithHealth = Server & {
  health?: HealthStatus
}

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>