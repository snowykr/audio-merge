"use client"

import { Play, Loader2 } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useAppStore, selectCanStartMerge, selectFiles, selectUploadOptions } from "@/lib/store"
import { uploadFiles, startMerge } from "@/lib/api"
import { toast } from "sonner"

export function MergeControl() {
  const canStartMerge = useAppStore(selectCanStartMerge)
  const files = useAppStore(selectFiles)
  const uploadOptions = useAppStore(selectUploadOptions)
  const {
    isUploading,
    isProcessing,
    setIsUploading,
    setIsProcessing,
    setUploadId,
    setTaskId
  } = useAppStore()

  const validFiles = files.filter(file => file.validationStatus === 'valid')

  const handleStartMerge = async () => {
    if (!canStartMerge || validFiles.length < 2) {
      toast.error("최소 2개의 유효한 오디오 파일이 필요합니다.")
      return
    }

    try {
      setIsUploading(true)

      // 1. 파일 업로드
      toast.info("파일을 서버에 업로드하고 있습니다...")

      const uploadResponse = await uploadFiles(
        validFiles.map(uploadedFile => uploadedFile.file),
        uploadOptions
      )

      setUploadId(uploadResponse.upload_id)

      // 업로드 검증 결과 확인
      const invalidFiles = uploadResponse.files.filter(file => !file.is_valid)
      if (invalidFiles.length > 0) {
        toast.error(`${invalidFiles.length}개 파일이 유효하지 않습니다.`)
        return
      }

      setIsUploading(false)
      setIsProcessing(true)

      // 2. 병합 작업 시작
      toast.info("오디오 파일 병합을 시작합니다...")

      const mergeResponse = await startMerge({
        upload_id: uploadResponse.upload_id,
        options: uploadOptions
      })

      setTaskId(mergeResponse.task_id)

      toast.success("병합 작업이 시작되었습니다. 진행률을 확인하세요.")

    } catch (error) {
      console.error('병합 시작 오류:', error)
      
      toast.error(error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다.")

      setIsUploading(false)
      setIsProcessing(false)
    }
  }

  if (validFiles.length < 2) {
    return null
  }

  return (
    <Card className="mb-8">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            <span className="font-medium">{validFiles.length}개</span>의 유효한 파일이 선택되었습니다
          </div>
          <Button
            onClick={handleStartMerge}
            disabled={!canStartMerge || isUploading || isProcessing}
            size="lg"
            className="min-w-[140px]"
          >
            {isUploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                업로드 중...
              </>
            ) : isProcessing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                처리 중...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                병합 시작
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}