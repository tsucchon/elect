import { useState, useRef } from 'react'
import './UploadPanel.css'

interface UploadPanelProps {
  onUploadSuccess?: () => void
}

export const UploadPanel = ({ onUploadSuccess }: UploadPanelProps) => {
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const formRef = useRef<HTMLFormElement>(null)

  const handleUpload = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const formData = new FormData(event.currentTarget)
    const generationFile = formData.get('generation_file') as File
    const priceFile = formData.get('price_file') as File

    if (!generationFile && !priceFile) {
      setError('少なくとも1つのファイルを選択してください')
      return
    }

    setUploading(true)
    setMessage(null)
    setError(null)

    try {
      const uploadFormData = new FormData()
      if (generationFile && generationFile.size > 0) {
        uploadFormData.append('generation_file', generationFile)
      }
      if (priceFile && priceFile.size > 0) {
        uploadFormData.append('price_file', priceFile)
      }

      const response = await fetch('/api/data/upload', {
        method: 'POST',
        body: uploadFormData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'アップロードに失敗しました')
      }

      const result = await response.json()
      setMessage(result.message)

      // フォームをリセット
      if (formRef.current) {
        formRef.current.reset()
      }

      // 成功コールバック
      if (onUploadSuccess) {
        onUploadSuccess()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'アップロードエラー')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="upload-panel">
      <h3>CSVデータアップロード</h3>
      <form ref={formRef} onSubmit={handleUpload}>
        <div className="file-input-group">
          <label>
            発電量データ (CSV):
            <input
              type="file"
              name="generation_file"
              accept=".csv"
              disabled={uploading}
            />
          </label>
        </div>

        <div className="file-input-group">
          <label>
            価格データ (CSV):
            <input
              type="file"
              name="price_file"
              accept=".csv"
              disabled={uploading}
            />
          </label>
        </div>

        <button type="submit" disabled={uploading}>
          {uploading ? 'アップロード中...' : 'アップロード'}
        </button>
      </form>

      {message && <div className="message success">{message}</div>}
      {error && <div className="message error">{error}</div>}
    </div>
  )
}
