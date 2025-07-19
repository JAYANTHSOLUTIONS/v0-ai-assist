"use client"

import { useState, useEffect, useRef } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { MessageInput } from "@/components/message-input"
import { MessageBubble } from "@/components/message-bubble"
import { TypingIndicator } from "@/components/typing-indicator"
import { useSession } from "@/contexts/session-context"
import { useToast } from "@/hooks/use-toast"

export interface Message {
  id: string
  type: "user" | "assistant"
  content: string
  timestamp: Date
  ui_elements?: UIElement[]
  intent?: string
  entities?: Record<string, any>
}

export interface UIElement {
  type: "button" | "link" | "card"
  text: string
  action: string
  data?: Record<string, any>
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const { sessionId, userId } = useSession()
  const { toast } = useToast()

  // Load conversation history when session changes
  useEffect(() => {
    if (sessionId) {
      loadConversationHistory()
    }
  }, [sessionId])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const loadConversationHistory = async () => {
    if (!sessionId) return

    setIsLoading(true)
    try {
      const response = await fetch(`/api/conversation/${sessionId}`)
      if (response.ok) {
        const data = await response.json()
        const formattedMessages: Message[] = data.messages.map((msg: any) => ({
          id: msg.id.toString(),
          type: msg.message_type,
          content: msg.content,
          timestamp: new Date(msg.timestamp),
          ui_elements: msg.metadata?.ui_elements || [],
          intent: msg.metadata?.intent,
          entities: msg.metadata?.entities,
        }))
        setMessages(formattedMessages)
      }
    } catch (error) {
      console.error("Failed to load conversation history:", error)
      toast({
        title: "Error",
        description: "Failed to load conversation history",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector("[data-radix-scroll-area-viewport]")
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }

  const sendMessage = async (content: string) => {
    if (!content.trim() || !sessionId) return

    // Add user message immediately
    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: content.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setIsTyping(true)

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: content.trim(),
          session_id: sessionId,
          user_id: userId,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()

      // Add assistant response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: data.message,
        timestamp: new Date(data.timestamp),
        ui_elements: data.ui_elements || [],
        intent: data.intent,
        entities: data.entities,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error("Failed to send message:", error)

      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: "Sorry, I encountered an error processing your request. Please try again.",
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, errorMessage])

      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsTyping(false)
    }
  }

  const handleUIElementClick = async (element: UIElement) => {
    console.log("UI Element clicked:", element)

    // Handle different UI element actions
    switch (element.action) {
      case "book_flight":
      case "book_hotel":
        await handleBooking(element)
        break
      case "view_details":
        await handleViewDetails(element)
        break
      case "search_again":
        await sendMessage("Search again with different criteria")
        break
      default:
        console.log("Unhandled action:", element.action)
    }
  }

  const handleBooking = async (element: UIElement) => {
    if (!element.data) return

    setIsTyping(true)
    try {
      const response = await fetch("/api/book-trip", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          booking_type: element.action.replace("book_", ""),
          booking_id: element.data.flight_id || element.data.hotel_id,
          passenger_details: {},
          payment_info: {},
        }),
      })

      if (response.ok) {
        const data = await response.json()
        await sendMessage(`Please confirm booking: ${element.text}`)
      } else {
        throw new Error("Booking failed")
      }
    } catch (error) {
      console.error("Booking error:", error)
      toast({
        title: "Booking Error",
        description: "Failed to process booking. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsTyping(false)
    }
  }

  const handleViewDetails = async (element: UIElement) => {
    await sendMessage(`Show me more details about: ${element.text}`)
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Loading conversation...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Messages Area */}
      <ScrollArea ref={scrollAreaRef} className="flex-1 p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <div className="mb-4">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">✈️</span>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Welcome to AI Travel Assistant</h3>
                <p className="text-gray-600 mb-6">
                  I can help you search for flights, hotels, and book your perfect trip!
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl mx-auto">
                <div
                  className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 cursor-pointer transition-colors"
                  onClick={() => sendMessage("I need a flight from New York to Los Angeles")}
                >
                  <div className="text-blue-600 mb-2">✈️</div>
                  <h4 className="font-medium mb-1">Search Flights</h4>
                  <p className="text-sm text-gray-600">Find the best flights for your trip</p>
                </div>

                <div
                  className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 cursor-pointer transition-colors"
                  onClick={() => sendMessage("I need a hotel in Paris for 3 nights")}
                >
                  <div className="text-blue-600 mb-2">🏨</div>
                  <h4 className="font-medium mb-1">Find Hotels</h4>
                  <p className="text-sm text-gray-600">Discover great places to stay</p>
                </div>

                <div
                  className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 cursor-pointer transition-colors"
                  onClick={() => sendMessage("Help me plan a trip to Japan")}
                >
                  <div className="text-blue-600 mb-2">🗺️</div>
                  <h4 className="font-medium mb-1">Plan Trip</h4>
                  <p className="text-sm text-gray-600">Get help planning your journey</p>
                </div>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <MessageBubble key={message.id} message={message} onUIElementClick={handleUIElementClick} />
            ))
          )}

          {isTyping && <TypingIndicator />}
        </div>
      </ScrollArea>

      {/* Message Input */}
      <div className="border-t border-gray-200 p-4">
        <div className="max-w-4xl mx-auto">
          <MessageInput
            onSendMessage={sendMessage}
            disabled={isTyping}
            placeholder="Ask me about flights, hotels, or travel plans..."
          />
        </div>
      </div>
    </div>
  )
}
