"use client"

import { useEffect, useRef } from "react"
import { Activity, Download, AlertTriangle, CheckCircle, Trash2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { useAppStore } from "@/lib/store"
import { createProgressEventStream, downloadResult, cleanupTask } from "@/lib/api"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

export function ProgressTracker() {
  const eventSourceRef = useRef<EventSource | null>(null)
  
  const {
    currentTaskId,
    taskStatus,
    isProcessing,
    setTaskStatus,
    setIsProcessing,
    resetTask
  } = useAppStore()

  // SSE 연결 및 진행률 추적
  useEffect(() => {
    if (!currentTaskId || !isProcessing) return

    const eventSource = createProgressEventStream(
      currentTaskId,
      (event) => {
        // 진행률 업데이트
        setTaskStatus({
          task_id: currentTaskId,
          status: event.status,
          progress: event.progress,
          current_step: event.step,
          message: event.message,
          created_at: new Date(),
        })
      },
      (_error) => {
        console.error('진행률 스트림 오류:', _error)
        toast.error("진행률 추적 연결에 문제가 발생했습니다.")
      },
      () => {
        // 스트림 완료
        setIsProcessing(false)
        if (taskStatus?.status === 'completed') {
          toast.success("오디오 파일 병합이 성공적으로 완료되었습니다!")
        }
      }
    )

    eventSourceRef.current = eventSource

    return () => {
      eventSource.close()
    }
  }, [currentTaskId, isProcessing, setTaskStatus, setIsProcessing, taskStatus?.status])

  const handleDownload = async () => {
    if (!currentTaskId) return

    try {
      await downloadResult(currentTaskId)
      
      toast.success("파일 다운로드가 시작되었습니다.")
    } catch {
      toast.error("파일 다운로드 중 오류가 발생했습니다.")
    }
  }

  const handleCleanup = async () => {
    if (!currentTaskId) return

    try {
      await cleanupTask(currentTaskId)
      resetTask()
      
      toast.success("임시 파일들이 성공적으로 정리되었습니다.")
    } catch {
      toast.error("파일 정리 중 오류가 발생했습니다.")
    }
  }

  if (!currentTaskId) return null

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'pending':
        return <Badge variant="secondary">대기 중</Badge>
      case 'processing':
        return <Badge variant="default" className="bg-blue-500">처리 중</Badge>
      case 'completed':
        return <Badge variant="default" className="bg-green-500">완료</Badge>
      case 'failed':
        return <Badge variant="destructive">실패</Badge>
      default:
        return <Badge variant="secondary">알 수 없음</Badge>
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center">
            <Activity className="mr-2" />
            진행 상황
          </div>
          {getStatusBadge(taskStatus?.status)}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 진행률 바 */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">
              {taskStatus?.current_step || '대기 중'}
            </span>
            <span className="font-medium">
              {(taskStatus?.progress || 0)}%
            </span>
          </div>
          <Progress 
            value={taskStatus?.progress || 0} 
            className={cn(
              "w-full",
              taskStatus?.status === 'failed' && "bg-red-100 dark:bg-red-950"
            )}
          />
        </div>

        {/* 상태 메시지 */}
        <div className="text-sm text-muted-foreground">
          {taskStatus?.message || '작업을 준비하고 있습니다...'}
        </div>

        {/* 완료 상태 - 다운로드 버튼 */}
        {taskStatus?.status === 'completed' && (
          <div className="flex items-center space-x-2 pt-2">
            <Button onClick={handleDownload} className="flex-1">
              <Download className="mr-2 h-4 w-4" />
              결과 파일 다운로드
            </Button>
            <Button variant="outline" onClick={handleCleanup}>
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* 오류 상태 */}
        {taskStatus?.status === 'failed' && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              오류가 발생했습니다: {taskStatus.message}
            </AlertDescription>
          </Alert>
        )}

        {/* 성공 상태 알림 */}
        {taskStatus?.status === 'completed' && (
          <Alert className="border-green-500 bg-green-50 dark:bg-green-950/20">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <AlertDescription className="text-green-700 dark:text-green-400">
              오디오 파일 병합이 성공적으로 완료되었습니다!
            </AlertDescription>
          </Alert>
        )}

        {/* 작업 ID 표시 (디버깅용) */}
        <div className="text-xs text-muted-foreground border-t pt-2">
          작업 ID: {currentTaskId}
        </div>
      </CardContent>
    </Card>
  )
}