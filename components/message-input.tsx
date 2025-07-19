"use client"

import type React from "react"

import { useState, useRef, type KeyboardEvent } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Send, Paperclip, Mic } from "lucide-react"
import { cn } from "@/lib/utils"

interface MessageInputProps {
  onSendMessage: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export function MessageInput({
  onSendMessage,
  disabled = false,
  placeholder = "Type your message...",
}: MessageInputProps) {
  const [message, setMessage] = useState("")
  const [isRecording, setIsRecording] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message)
      setMessage("")

      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto"
      }
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value)

    // Auto-resize textarea
    const textarea = e.target
    textarea.style.height = "auto"
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px"
  }

  const handleVoiceRecord = () => {
    // Placeholder for voice recording functionality
    setIsRecording(!isRecording)
    console.log("Voice recording:", !isRecording)
  }

  const handleFileAttach = () => {
    // Placeholder for file attachment functionality
    console.log("File attachment clicked")
  }

  return (
    <div className="flex items-end space-x-2">
      {/* Attachment Button */}
      <Button variant="ghost" size="sm" onClick={handleFileAttach} disabled={disabled} className="flex-shrink-0">
        <Paperclip className="h-4 w-4" />
      </Button>

      {/* Message Input */}
      <div className="flex-1 relative">
        <Textarea
          ref={textareaRef}
          value={message}
          onChange={handleTextareaChange}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          disabled={disabled}
          className="min-h-[44px] max-h-[120px] resize-none pr-12 py-3"
          rows={1}
        />

        {/* Voice Recording Button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={handleVoiceRecord}
          disabled={disabled}
          className={cn("absolute right-2 top-2 h-8 w-8 p-0", isRecording && "text-red-500")}
        >
          <Mic className="h-4 w-4" />
        </Button>
      </div>

      {/* Send Button */}
      <Button onClick={handleSend} disabled={disabled || !message.trim()} size="sm" className="flex-shrink-0">
        <Send className="h-4 w-4" />
      </Button>
    </div>
  )
}
