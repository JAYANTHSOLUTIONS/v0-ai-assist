"use client"

import type { Message, UIElement } from "@/components/chat-interface"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { User, Bot, ExternalLink, CreditCard, Eye, Plane, Hotel, MapPin, Clock, Star, DollarSign } from "lucide-react"
import { cn } from "@/lib/utils"

interface MessageBubbleProps {
  message: Message
  onUIElementClick: (element: UIElement) => void
}

export function MessageBubble({ message, onUIElementClick }: MessageBubbleProps) {
  const isUser = message.type === "user"

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  }

  const renderUIElement = (element: UIElement, index: number) => {
    const getIcon = () => {
      switch (element.action) {
        case "book_flight":
          return <Plane className="h-4 w-4" />
        case "book_hotel":
          return <Hotel className="h-4 w-4" />
        case "view_details":
          return <Eye className="h-4 w-4" />
        case "view_all_flights":
        case "view_all_hotels":
          return <ExternalLink className="h-4 w-4" />
        default:
          return <CreditCard className="h-4 w-4" />
      }
    }

    const getVariant = () => {
      if (element.action.startsWith("book_")) return "default"
      if (element.action.startsWith("view_")) return "outline"
      return "secondary"
    }

    switch (element.type) {
      case "button":
        return (
          <Button
            key={index}
            variant={getVariant()}
            size="sm"
            onClick={() => onUIElementClick(element)}
            className="flex items-center space-x-2"
          >
            {getIcon()}
            <span>{element.text}</span>
            {element.data?.price && (
              <Badge variant="secondary" className="ml-2">
                ${element.data.price}
              </Badge>
            )}
          </Button>
        )

      case "card":
        return (
          <Card
            key={index}
            className="cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => onUIElementClick(element)}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 mb-1">{element.text}</h4>

                  {element.data && (
                    <div className="space-y-2">
                      {element.data.rating && (
                        <div className="flex items-center space-x-1">
                          <Star className="h-4 w-4 text-yellow-400 fill-current" />
                          <span className="text-sm text-gray-600">{element.data.rating}</span>
                        </div>
                      )}

                      {element.data.location && (
                        <div className="flex items-center space-x-1">
                          <MapPin className="h-4 w-4 text-gray-400" />
                          <span className="text-sm text-gray-600">{element.data.location}</span>
                        </div>
                      )}

                      {element.data.duration && (
                        <div className="flex items-center space-x-1">
                          <Clock className="h-4 w-4 text-gray-400" />
                          <span className="text-sm text-gray-600">{element.data.duration}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {element.data?.price && (
                  <div className="text-right">
                    <div className="flex items-center space-x-1">
                      <DollarSign className="h-4 w-4 text-green-600" />
                      <span className="font-semibold text-green-600">${element.data.price}</span>
                    </div>
                    {element.data.per_night && <span className="text-xs text-gray-500">/night</span>}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )

      case "link":
        return (
          <Button
            key={index}
            variant="link"
            size="sm"
            onClick={() => onUIElementClick(element)}
            className="p-0 h-auto text-blue-600 hover:text-blue-800"
          >
            <ExternalLink className="h-3 w-3 mr-1" />
            {element.text}
          </Button>
        )

      default:
        return null
    }
  }

  return (
    <div className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}>
      <div className={cn("flex max-w-[80%] space-x-3", isUser ? "flex-row-reverse space-x-reverse" : "flex-row")}>
        {/* Avatar */}
        <div
          className={cn(
            "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
            isUser ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600",
          )}
        >
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </div>

        {/* Message Content */}
        <div className="flex-1 space-y-2">
          <div
            className={cn(
              "rounded-lg px-4 py-2 max-w-none",
              isUser ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-900",
            )}
          >
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          </div>

          {/* UI Elements */}
          {message.ui_elements && message.ui_elements.length > 0 && (
            <div className="space-y-2">
              <div className="flex flex-wrap gap-2">
                {message.ui_elements.map((element, index) => renderUIElement(element, index))}
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <span>{formatTime(message.timestamp)}</span>
            {message.intent && (
              <>
                <span>•</span>
                <Badge variant="outline" className="text-xs">
                  {message.intent.replace("_", " ")}
                </Badge>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
