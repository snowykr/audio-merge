"use client"

import { Settings } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { useAppStore, selectFiles, selectUploadOptions } from "@/lib/store"

export function MergeOptions() {
  const files = useAppStore(selectFiles)
  const uploadOptions = useAppStore(selectUploadOptions)
  const updateOptions = useAppStore(state => state.updateOptions)

  const validFiles = files.filter(file => file.validationStatus === 'valid')

  if (validFiles.length === 0) {
    return null
  }

  return (
    <Card className="mb-8">
      <CardHeader>
        <CardTitle className="flex items-center">
          <Settings className="mr-2" />
          병합 옵션
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Cross-fade 길이 */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">
              Cross-fade 길이 (ms)
            </Label>
            <Slider
              value={[uploadOptions.fade_duration_ms]}
              onValueChange={(value) => updateOptions({ fade_duration_ms: value[0] })}
              max={5000}
              min={0}
              step={100}
              className="w-full"
            />
            <div className="text-sm text-muted-foreground">
              {uploadOptions.fade_duration_ms}ms
            </div>
          </div>

          {/* 버퍼 크기 */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">
              버퍼 크기
            </Label>
            <Select
              value={uploadOptions.buffer_size.toString()}
              onValueChange={(value) => updateOptions({ buffer_size: parseInt(value) })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="32768">32KB (빠름)</SelectItem>
                <SelectItem value="65536">64KB (권장)</SelectItem>
                <SelectItem value="131072">128KB (안정)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* 자동 변환 옵션 */}
        <div className="mt-6">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="auto-convert"
              checked={uploadOptions.auto_convert}
              onCheckedChange={(checked) => 
                updateOptions({ auto_convert: checked === true })
              }
            />
            <Label htmlFor="auto-convert" className="text-sm">
              포맷 불일치 시 자동 변환
            </Label>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            오디오 파일들의 샘플링 레이트나 채널 수가 다를 때 자동으로 변환합니다.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}