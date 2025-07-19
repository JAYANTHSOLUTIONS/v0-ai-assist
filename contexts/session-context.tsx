"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import { v4 as uuidv4 } from "uuid"

interface SessionContextType {
  sessionId: string
  userId?: string
  createNewSession: () => void
  setUserId: (userId: string) => void
}

const SessionContext = createContext<SessionContextType | undefined>(undefined)

export function SessionProvider({ children }: { children: ReactNode }) {
  const [sessionId, setSessionId] = useState<string>("")
  const [userId, setUserIdState] = useState<string>()

  useEffect(() => {
    // Initialize session on mount
    const storedSessionId = localStorage.getItem("travel_session_id")
    const storedUserId = localStorage.getItem("travel_user_id")

    if (storedSessionId) {
      setSessionId(storedSessionId)
    } else {
      createNewSession()
    }

    if (storedUserId) {
      setUserIdState(storedUserId)
    }
  }, [])

  const createNewSession = () => {
    const newSessionId = uuidv4()
    setSessionId(newSessionId)
    localStorage.setItem("travel_session_id", newSessionId)
  }

  const setUserId = (newUserId: string) => {
    setUserIdState(newUserId)
    localStorage.setItem("travel_user_id", newUserId)
  }

  return (
    <SessionContext.Provider
      value={{
        sessionId,
        userId,
        createNewSession,
        setUserId,
      }}
    >
      {children}
    </SessionContext.Provider>
  )
}

export function useSession() {
  const context = useContext(SessionContext)
  if (context === undefined) {
    throw new Error("useSession must be used within a SessionProvider")
  }
  return context
}
