"use client";

import { useState, useRef, useCallback, type DragEvent } from "react";
import { useRouter } from "next/navigation";
import { Upload, FileText, AlertCircle, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { uploadCV } from "@/lib/api";

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];
const ACCEPTED_EXTENSIONS = [".pdf", ".docx"];
const MAX_SIZE_MB = 10;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

interface CVUploadProps {
  onUploadSuccess?: (cvId: number) => void;
}

export function CVUpload({ onUploadSuccess }: CVUploadProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const validateFile = useCallback((file: File): string | null => {
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      return `Desteklenmeyen dosya formatı. Sadece ${ACCEPTED_EXTENSIONS.join(", ")} kabul edilir.`;
    }
    if (file.size > MAX_SIZE_BYTES) {
      return `Dosya boyutu çok büyük (${(file.size / 1024 / 1024).toFixed(1)}MB). Maksimum ${MAX_SIZE_MB}MB.`;
    }
    return null;
  }, []);

  const handleUpload = useCallback(
    async (file: File) => {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }

      setError(null);
      setSuccess(null);
      setUploading(true);
      setProgress(0);

      // Simüle edilmiş progress (gerçek upload fetch API progress desteklemiyor)
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 150);

      try {
        const result = await uploadCV(file);
        clearInterval(progressInterval);
        setProgress(100);
        setSuccess(`"${result.filename}" başarıyla yüklendi.`);

        setTimeout(() => {
          if (onUploadSuccess) {
            onUploadSuccess(result.id);
          } else {
            router.push(`/analyze?cvId=${result.id}`);
          }
        }, 800);
      } catch (err) {
        clearInterval(progressInterval);
        setProgress(0);
        setError(err instanceof Error ? err.message : "Yükleme sırasında bir hata oluştu.");
      } finally {
        setUploading(false);
      }
    },
    [validateFile, onUploadSuccess, router]
  );

  const handleDrag = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      const file = e.dataTransfer.files?.[0];
      if (file) handleUpload(file);
    },
    [handleUpload]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleUpload(file);
      // Reset input
      if (inputRef.current) inputRef.current.value = "";
    },
    [handleUpload]
  );

  return (
    <div className="w-full">
      {/* Drop zone */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => !uploading && inputRef.current?.click()}
        className={`relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-all
          ${
            dragActive
              ? "border-accent bg-accent/5 scale-[1.01]"
              : "border-slate-600 hover:border-slate-500 hover:bg-bg-surface/50"
          }
          ${uploading ? "pointer-events-none opacity-70" : ""}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(",")}
          onChange={handleFileSelect}
          className="hidden"
        />

        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-slate-600 border-t-accent" />
            <p className="text-sm text-slate-300">Yükleniyor... %{progress}</p>
            <div className="h-2 w-48 overflow-hidden rounded-full bg-slate-700">
              <div
                className="h-full rounded-full bg-accent transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        ) : (
          <>
            <div className="mb-4 rounded-full bg-accent/10 p-4">
              <Upload className="h-8 w-8 text-accent" />
            </div>
            <p className="mb-1 text-base font-medium text-text-primary">
              CV dosyanızı sürükleyip bırakın
            </p>
            <p className="mb-4 text-sm text-slate-400">veya dosya seçmek için tıklayın</p>
            <div className="flex items-center gap-4 text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <FileText className="h-3.5 w-3.5" />
                PDF, DOCX
              </span>
              <span>Maks. {MAX_SIZE_MB}MB</span>
            </div>
          </>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="mt-3 flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/10 px-4 py-3">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {/* Success */}
      {success && (
        <div className="mt-3 flex items-start gap-2 rounded-lg border border-success/30 bg-success/10 px-4 py-3">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-green-400" />
          <p className="text-sm text-green-300">{success}</p>
        </div>
      )}
    </div>
  );
}
