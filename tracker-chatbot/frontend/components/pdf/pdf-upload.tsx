'use client'

import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, CheckCircle, AlertCircle } from 'lucide-react'
import { uploadPDF } from '@/lib/api'
import { UploadStatus } from '@/lib/types'
import { cn, formatFileSize, isValidPDF } from '@/lib/utils'

interface PDFUploadProps {
  onUploadSuccess: (response: any) => void
  onUploadError: (error: string) => void
  className?: string
}

export default function PDFUpload({ onUploadSuccess, onUploadError, className }: PDFUploadProps) {
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({ status: 'idle' })
  const [dragActive, setDragActive] = useState(false)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    // Validate file
    if (!isValidPDF(file)) {
      setUploadStatus({
        status: 'error',
        error: 'Please upload a valid PDF file'
      })
      onUploadError('Please upload a valid PDF file')
      return
    }

    if (file.size > 100 * 1024 * 1024) { // 100MB
      setUploadStatus({
        status: 'error',
        error: 'File size must be less than 100MB'
      })
      onUploadError('File size must be less than 100MB')
      return
    }

    // Start upload
    setUploadStatus({
      status: 'uploading',
      filename: file.name,
      progress: 0
    })

    try {
      const response = await uploadPDF(file)
      
      setUploadStatus({
        status: 'success',
        filename: file.name,
        pageCount: response.page_count,
        chunkCount: response.chunk_count
      })

      onUploadSuccess(response)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed'
      setUploadStatus({
        status: 'error',
        filename: file.name,
        error: errorMessage
      })
      onUploadError(errorMessage)
    }
  }, [onUploadSuccess, onUploadError])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: false,
    disabled: uploadStatus.status === 'uploading'
  })

  const resetUpload = () => {
    setUploadStatus({ status: 'idle' })
  }

  if (uploadStatus.status === 'success') {
    return (
      <div className={cn(
        "rounded-lg border border-green-200 bg-green-50 p-6 dark:border-green-800 dark:bg-green-950",
        className
      )}>
        <div className="flex items-start space-x-3">
          <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-medium text-green-900 dark:text-green-100">
              Upload Successful
            </h3>
            <p className="text-sm text-green-700 dark:text-green-300 mt-1">
              {uploadStatus.filename}
            </p>
            <div className="flex items-center space-x-4 mt-2 text-xs text-green-600 dark:text-green-400">
              <span>{uploadStatus.pageCount} pages</span>
              <span>{uploadStatus.chunkCount} chunks</span>
            </div>
          </div>
          <button
            onClick={resetUpload}
            className="text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-200"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    )
  }

  if (uploadStatus.status === 'error') {
    return (
      <div className={cn(
        "rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-800 dark:bg-red-950",
        className
      )}>
        <div className="flex items-start space-x-3">
          <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-medium text-red-900 dark:text-red-100">
              Upload Failed
            </h3>
            <p className="text-sm text-red-700 dark:text-red-300 mt-1">
              {uploadStatus.error || 'An error occurred during upload'}
            </p>
            {uploadStatus.filename && (
              <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                File: {uploadStatus.filename}
              </p>
            )}
          </div>
          <button
            onClick={resetUpload}
            className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-200"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div
      {...getRootProps()}
      className={cn(
        "relative rounded-lg border-2 border-dashed transition-colors cursor-pointer",
        isDragActive || dragActive
          ? "border-primary bg-primary/5"
          : "border-gray-300 hover:border-gray-400 dark:border-gray-600 dark:hover:border-gray-500",
        uploadStatus.status === 'uploading' && "pointer-events-none opacity-50",
        className
      )}
      onDragEnter={() => setDragActive(true)}
      onDragLeave={() => setDragActive(false)}
    >
      <input {...getInputProps()} />
      
      <div className="p-8 text-center">
        {uploadStatus.status === 'uploading' ? (
          <div className="space-y-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto" />
            <div>
              <p className="text-sm font-medium">Uploading...</p>
              <p className="text-xs text-muted-foreground mt-1">
                {uploadStatus.filename}
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="mx-auto h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
              <Upload className="h-6 w-6 text-primary" />
            </div>
            
            <div>
              <p className="text-sm font-medium">
                {isDragActive
                  ? "Drop the PDF file here"
                  : "Drop PDF file here or click to browse"
                }
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Maximum file size: 100MB
              </p>
            </div>

            <div className="flex items-center justify-center space-x-2 text-xs text-muted-foreground">
              <FileText className="h-3 w-3" />
              <span>PDF files only</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
