"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { X, MessageCircle, Clock, Trash2 } from "lucide-react"
import { useSession } from "@/contexts/session-context"
import { cn } from "@/lib/utils"

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

interface ConversationSession {
  session_id: string
  user_id?: string
  created_at: string
  last_activity: string
  message_count: number
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const [sessions, setSessions] = useState<ConversationSession[]>([])
  const [loading, setLoading] = useState(false)
  const { sessionId, createNewSession } = useSession()

  useEffect(() => {
    if (isOpen) {
      loadSessions()
    }
  }, [isOpen])

  const loadSessions = async () => {
    setLoading(true)
    try {
      const response = await fetch("/api/sessions")
      if (response.ok) {
        const data = await response.json()
        setSessions(data.sessions || [])
      }
    } catch (error) {
      console.error("Failed to load sessions:", error)
    } finally {
      setLoading(false)
    }
  }

  const deleteSession = async (sessionIdToDelete: string) => {
    try {
      const response = await fetch(`/api/conversation/${sessionIdToDelete}`, {
        method: "DELETE",
      })
      if (response.ok) {
        setSessions(sessions.filter((s) => s.session_id !== sessionIdToDelete))
        if (sessionIdToDelete === sessionId) {
          createNewSession()
        }
      }
    } catch (error) {
      console.error("Failed to delete session:", error)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)

    if (diffInHours < 1) {
      return "Just now"
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`
    } else {
      return date.toLocaleDateString()
    }
  }

  return (
    <>
      {/* Overlay */}
      {isOpen && <div className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden" onClick={onClose} />}

      {/* Sidebar */}
      <div
        className={cn(
          "fixed left-0 top-0 z-50 h-full w-80 bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Chat History</h2>
          <Button variant="ghost" size="sm" onClick={onClose} className="md:hidden">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="p-4">
          <Button
            onClick={() => {
              createNewSession()
              onClose()
            }}
            className="w-full"
          >
            <MessageCircle className="h-4 w-4 mr-2" />
            New Conversation
          </Button>
        </div>

        <ScrollArea className="flex-1 px-4">
          {loading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
                  <div className="h-3 bg-gray-200 rounded w-1/2" />
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {sessions.map((session) => (
                <div
                  key={session.session_id}
                  className={cn(
                    "group p-3 rounded-lg border cursor-pointer hover:bg-gray-50 transition-colors",
                    session.session_id === sessionId ? "bg-blue-50 border-blue-200" : "border-gray-200",
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <MessageCircle className="h-4 w-4 text-gray-400 flex-shrink-0" />
                        <span className="text-sm font-medium text-gray-900 truncate">
                          Session {session.session_id.slice(-8)}
                        </span>
                      </div>

                      <div className="flex items-center space-x-2 text-xs text-gray-500">
                        <Clock className="h-3 w-3" />
                        <span>{formatDate(session.last_activity)}</span>
                        <span>•</span>
                        <span>{session.message_count} messages</span>
                      </div>
                    </div>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteSession(session.session_id)
                      }}
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}

              {sessions.length === 0 && !loading && (
                <div className="text-center py-8 text-gray-500">
                  <MessageCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No conversations yet</p>
                  <p className="text-xs">Start a new chat to begin</p>
                </div>
              )}
            </div>
          )}
        </ScrollArea>
      </div>
    </>
  )
}
