'use client'

import React, { useState } from 'react'
import { PDFUpload } from '@/components/pdf/pdf-upload'
import { ChatInterface } from '@/components/chat/chat-interface'
import { Message } from '@/lib/types'
import { FileText, Bot, Settings, Moon, Sun } from 'lucide-react'

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [documentUploaded, setDocumentUploaded] = useState(false)

  const handleUploadSuccess = (response: any) => {
    setDocumentUploaded(true)
    // Clear previous messages when new document is uploaded
    setMessages([])
    setSessionId(null)
  }

  const handleUploadError = (error: string) => {
    console.error('Upload error:', error)
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div className="w-80 border-r bg-card p-6 flex flex-col">
        <div className="flex items-center gap-2 mb-6">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Bot className="w-4 h-4 text-primary-foreground" />
          </div>
          <h1 className="text-lg font-semibold">PDF Chatbot</h1>
        </div>

        <div className="flex-1 space-y-6">
          {/* Upload Section */}
          <div>
            <h2 className="text-sm font-medium mb-3">Upload Document</h2>
            <PDFUpload
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
            />
          </div>

          {/* Status */}
          {documentUploaded && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg dark:bg-green-950 dark:border-green-800">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-green-600 dark:text-green-400" />
                <span className="text-sm font-medium text-green-900 dark:text-green-100">
                  Document Ready
                </span>
              </div>
              <p className="text-xs text-green-700 dark:text-green-300 mt-1">
                You can now ask questions about your document
              </p>
            </div>
          )}

          {/* Features */}
          <div>
            <h3 className="text-sm font-medium mb-3">Features</h3>
            <ul className="space-y-2 text-xs text-muted-foreground">
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                Hybrid search (vector + keyword)
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                Page citations
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                Streaming responses
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                Export conversations
              </li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t text-xs text-muted-foreground">
          <p>Powered by Groq & ChromaDB</p>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="flex h-14 items-center px-6">
            <div className="flex-1">
              <h2 className="text-lg font-semibold">
                {documentUploaded ? 'Document Chat' : 'PDF Assistant'}
              </h2>
              <p className="text-sm text-muted-foreground">
                {documentUploaded 
                  ? 'Ask questions about your uploaded document'
                  : 'Upload a PDF to get started'
                }
              </p>
            </div>
            
            <div className="flex items-center gap-2">
              {/* Theme toggle placeholder */}
              <button className="p-2 rounded-lg hover:bg-accent">
                <Sun className="w-4 h-4" />
              </button>
              
              {/* Settings placeholder */}
              <button className="p-2 rounded-lg hover:bg-accent">
                <Settings className="w-4 h-4" />
              </button>
            </div>
          </div>
        </header>

        {/* Chat Interface */}
        <div className="flex-1">
          <ChatInterface
            messages={messages}
            onMessagesChange={setMessages}
            sessionId={sessionId}
            onSessionIdChange={setSessionId}
            isLoading={isLoading}
            onLoadingChange={setIsLoading}
          />
        </div>
      </div>
    </div>
  )
}
