'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Copy, Download, Settings } from 'lucide-react'
import { streamChat, exportConversation } from '@/lib/api'
import { Message, ChatRequest } from '@/lib/types'
import { cn, extractCitations, copyToClipboard, downloadFile } from '@/lib/utils'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface ChatInterfaceProps {
  messages: Message[]
  onMessagesChange: (messages: Message[]) => void
  sessionId: string | null
  onSessionIdChange: (sessionId: string) => void
  isLoading: boolean
  onLoadingChange: (loading: boolean) => void
  className?: string
}

export function ChatInterface({
  messages,
  onMessagesChange,
  sessionId,
  onSessionIdChange,
  isLoading,
  onLoadingChange,
  className
}: ChatInterfaceProps) {
  const [input, setInput] = useState('')
  const [localMessages, setLocalMessages] = useState<Message[]>(messages)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    setLocalMessages(messages)
  }, [messages])

  useEffect(() => {
    scrollToBottom()
  }, [localMessages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    const updatedMessages = [...localMessages, userMessage]
    setLocalMessages(updatedMessages)
    onMessagesChange(updatedMessages)
    setInput('')
    onLoadingChange(true)

    try {
      const request: ChatRequest = {
        message: input.trim(),
        session_id: sessionId || undefined
      }

      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      if (!response.body) {
        throw new Error('Response body is null')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      let assistantContent = ''
      const assistantMessage: Message = {
        role: 'assistant',
        content: '',
        timestamp: new Date()
      }

      const messagesWithAssistant = [...updatedMessages, assistantMessage]
      setLocalMessages(messagesWithAssistant)

      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                if (data.type === 'content') {
                  assistantContent += data.content
                  assistantMessage.content = assistantContent
                  setLocalMessages([...messagesWithAssistant])
                } else if (data.type === 'done') {
                  if (data.session_id) {
                    onSessionIdChange(data.session_id)
                  }
                  onMessagesChange([...messagesWithAssistant])
                  onLoadingChange(false)
                  return
                } else if (data.type === 'error') {
                  throw new Error(data.content)
                }
              } catch (parseError) {
                console.warn('Failed to parse SSE data:', line)
              }
            }
          }
        }
      } finally {
        reader.releaseLock()
      }
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date()
      }
      const finalMessages = [...updatedMessages, errorMessage]
      setLocalMessages(finalMessages)
      onMessagesChange(finalMessages)
      onLoadingChange(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
  }

  const copyMessage = async (content: string) => {
    const success = await copyToClipboard(content)
    if (success) {
      console.log('Message copied to clipboard')
    }
  }

  const exportChat = async () => {
    if (!sessionId) return
    
    try {
      const blob = await exportConversation(sessionId)
      downloadFile(blob, `conversation_${sessionId}.md`)
    } catch (error) {
      console.error('Export error:', error)
    }
  }

  const CitationBadge = ({ page }: { page: number }) => (
    <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 ml-1">
      Page {page}
    </span>
  )

  const MessageComponent = ({ message }: { message: Message }) => {
    const citations = extractCitations(message.content)
    const isUser = message.role === 'user'

    return (
      <div className={cn(
        "flex gap-3 p-4",
        isUser ? "bg-muted/50" : "bg-background"
      )}>
        <div className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          isUser ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
        )}>
          {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
        </div>
        
        <div className="flex-1 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">
              {isUser ? 'You' : 'Assistant'}
            </span>
            <span className="text-xs text-muted-foreground">
              {message.timestamp.toLocaleTimeString()}
            </span>
          </div>
          
          <div className="prose prose-sm max-w-none dark:prose-invert">
            {isUser ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            )}
          </div>
          
          {!isUser && citations.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {citations.map(page => (
                <CitationBadge key={page} page={page} />
              ))}
            </div>
          )}
          
          {!isUser && (
            <div className="flex gap-2">
              <button
                onClick={() => copyMessage(message.content)}
                className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1"
              >
                <Copy className="w-3 h-3" />
                Copy
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }

  const exampleQuestions = [
    "What are power requirements?",
    "How do I configure GPS module?",
    "What are voltage specifications?",
    "Show me communication protocols"
  ]

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        {localMessages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <div className="max-w-md space-y-4">
              <h2 className="text-2xl font-bold">Welcome to PDF Chatbot</h2>
              <p className="text-muted-foreground">
                Upload a PDF document and start asking questions about its content.
              </p>
              
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">Example questions:</p>
                <div className="grid grid-cols-1 gap-2">
                  {exampleQuestions.map((question, index) => (
                    <button
                      key={index}
                      onClick={() => setInput(question)}
                      className="text-left p-3 rounded-lg border bg-card hover:bg-accent text-sm"
                      disabled={isLoading}
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {localMessages.map((message, index) => (
              <MessageComponent key={index} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t bg-background p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your document..."
            className="flex-1 resize-none rounded-lg border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 min-h-[40px] max-h-[120px]"
            rows={1}
            disabled={isLoading}
          />
          
          <div className="flex gap-2">
            {sessionId && (
              <button
                type="button"
                onClick={exportChat}
                className="px-3 py-2 text-sm rounded-lg border bg-background hover:bg-accent focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                title="Export conversation"
              >
                <Download className="w-4 h-4" />
              </button>
            )}
            
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="px-4 py-2 text-sm rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              {isLoading ? 'Sending...' : 'Send'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
