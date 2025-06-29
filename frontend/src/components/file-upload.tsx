"use client"

import { useCallback, useRef } from "react"
import { Upload, FileAudio, X, AlertCircle, CheckCircle } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useAppStore } from "@/lib/store"
import { validateFile, formatFileSize } from "@/lib/api"
import { cn } from "@/lib/utils"

export function FileUpload() {
  const {
    files,
    isDragging,
    addFiles,
    addFilesWithValidation,
    removeFile,
    setIsDragging,
    updateFileValidation
  } = useAppStore()
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFiles = useCallback((newFiles: File[]) => {
    // 클라이언트 사이드 유효성 검사
    const validatedFiles = newFiles.map(file => {
      const validation = validateFile(file)
      return { file, validation }
    })

    // 파일과 검증 결과를 한 번에 추가
    addFilesWithValidation(validatedFiles)
  }, [addFilesWithValidation])

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [setIsDragging])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.currentTarget === e.target) {
      setIsDragging(false)
    }
  }, [setIsDragging])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const droppedFiles = Array.from(e.dataTransfer.files)
    handleFiles(droppedFiles)
  }, [handleFiles, setIsDragging])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || [])
    handleFiles(selectedFiles)
    
    // 입력 필드 초기화 (같은 파일을 다시 선택할 수 있도록)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [handleFiles])

  const handleClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  return (
    <Card className="mb-8">
      <CardHeader>
        <CardTitle className="flex items-center">
          <Upload className="mr-2" />
          파일 업로드
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* 드롭존 */}
        <div
          className={cn(
            "border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer",
            isDragging
              ? "border-blue-400 bg-blue-50 dark:bg-blue-950/20"
              : "border-muted-foreground/25 hover:border-blue-400 hover:bg-muted/50"
          )}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={handleClick}
        >
          <Upload className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <div className="mb-4">
            <span className="text-lg font-medium text-foreground">
              파일을 드래그하거나 클릭하여 업로드
            </span>
          </div>
          <p className="text-sm text-muted-foreground">
            WAV, MP3 파일만 지원 (최대 500MB/파일, 2GB 총합, 20개 파일)
          </p>
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            multiple
            accept=".wav,.mp3,audio/wav,audio/mpeg,audio/mp3"
            onChange={handleFileSelect}
          />
        </div>

        {/* 파일 목록 */}
        {files.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-medium text-foreground mb-3">
              업로드된 파일 ({files.length}개)
            </h3>
            <div className="space-y-2">
              {files.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <FileAudio className="text-blue-500 dark:text-blue-400 h-5 w-5" />
                    <div>
                      <div className="font-medium text-foreground flex items-center space-x-2">
                        <span>{file.name}</span>
                        {file.validationStatus === 'valid' && (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        )}
                        {file.validationStatus === 'invalid' && (
                          <AlertCircle className="h-4 w-4 text-red-500" />
                        )}
                        {file.validationStatus === 'pending' && (
                          <Badge variant="secondary">검증 중</Badge>
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {formatFileSize(file.size)}
                        {file.validationMessage && file.validationStatus === 'invalid' && (
                          <span className="ml-2 text-red-500">
                            - {file.validationMessage}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(file.id)}
                    className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/20"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}