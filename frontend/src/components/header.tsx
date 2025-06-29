"use client"

import { Music } from "lucide-react"
import { ThemeToggle } from "./theme-toggle"

export function Header() {
  return (
    <header className="bg-background border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <div className="flex items-center">
            <Music className="text-blue-600 dark:text-blue-400 text-2xl mr-3" />
            <h1 className="text-2xl font-bold text-foreground">Audio Merge</h1>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-sm text-muted-foreground">
              오디오 파일 병합 도구
            </div>
            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  )
}