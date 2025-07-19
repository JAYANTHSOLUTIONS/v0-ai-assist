"use client"

import { useState } from "react"
import { ChatInterface } from "@/components/chat-interface"
import { Header } from "@/components/header"
import { Sidebar } from "@/components/sidebar"
import { SessionProvider } from "@/contexts/session-context"
import { Toaster } from "@/components/ui/toaster"

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <SessionProvider>
      <div className="flex h-screen bg-gray-50">
        {/* Sidebar */}
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          <Header onMenuClick={() => setSidebarOpen(true)} />
          <ChatInterface />
        </div>

        <Toaster />
      </div>
    </SessionProvider>
  )
}
