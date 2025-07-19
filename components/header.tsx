"use client"

import { Button } from "@/components/ui/button"
import { Menu, Plane, Settings, User } from "lucide-react"
import { useSession } from "@/contexts/session-context"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"

interface HeaderProps {
  onMenuClick: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  const { createNewSession, userId } = useSession()

  return (
    <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <Button variant="ghost" size="sm" onClick={onMenuClick} className="md:hidden">
          <Menu className="h-5 w-5" />
        </Button>

        <div className="flex items-center space-x-2">
          <Plane className="h-6 w-6 text-blue-600" />
          <h1 className="text-xl font-semibold text-gray-900">AI Travel Assistant</h1>
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <Button variant="outline" size="sm" onClick={createNewSession}>
          New Chat
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm">
              <User className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuItem>Profile</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
