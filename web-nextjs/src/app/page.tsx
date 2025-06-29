"use client"

import { Header } from "@/components/header"
import { FileUpload } from "@/components/file-upload"
import { MergeOptions } from "@/components/merge-options"
import { MergeControl } from "@/components/merge-control"
import { ProgressTracker } from "@/components/progress-tracker"
import { Footer } from "@/components/footer"

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <FileUpload />
        <MergeOptions />
        <MergeControl />
        <ProgressTracker />
      </main>

      <Footer />
    </div>
  )
}
