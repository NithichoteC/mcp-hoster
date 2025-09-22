import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Providers } from './providers'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'MCP Host - Professional MCP Server Gateway',
  description: 'Connect any MCP server to any AI agent (ChatGPT, Claude, etc.) with professional hosting and management',
  keywords: 'MCP, Model Context Protocol, AI, ChatGPT, Claude, server management, automation',
  authors: [{ name: 'MCP Host Team' }],
  viewport: 'width=device-width, initial-scale=1',
  robots: 'index, follow',
  openGraph: {
    title: 'MCP Host - Professional MCP Server Gateway',
    description: 'Connect any MCP server to any AI agent with professional hosting and management',
    type: 'website',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'MCP Host - Professional MCP Server Gateway',
    description: 'Connect any MCP server to any AI agent with professional hosting and management',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} h-full bg-gray-50 text-gray-900 antialiased`}>
        <Providers>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              className: 'bg-white shadow-lg border border-gray-200',
              success: {
                iconTheme: {
                  primary: '#10b981',
                  secondary: '#ffffff',
                },
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#ffffff',
                },
              },
            }}
          />
        </Providers>
      </body>
    </html>
  )
}