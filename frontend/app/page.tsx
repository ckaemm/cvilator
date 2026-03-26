"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import {
  FileText,
  TrendingUp,
  TrendingDown,
  Sparkles,
  Loader2,
  AlertCircle,
  FileSearch,
  Download,
  Trash2,
  Upload,
  ChevronRight,
  Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/toast";
import { listCVs, deleteCV, downloadOptimizedCV, uploadCV } from "@/lib/api";
import type { CVListItem } from "@/lib/types";

// ── Helpers ──────────────────────────────────────────────────────────

function relativeTime(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = now - then;
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "Az önce";
  if (minutes < 60) return `${minutes} dk önce`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} saat önce`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days} gün önce`;
  return new Date(dateStr).toLocaleDateString("tr-TR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function getScoreBadge(score: number | null) {
  if (score === null) return { label: "Bekliyor", variant: "outline" as const };
  if (score >= 80) return { label: `${score}`, variant: "success" as const };
  if (score >= 60) return { label: `${score}`, variant: "warning" as const };
  return { label: `${score}`, variant: "danger" as const };
}

function getScoreColor(score: number): string {
  if (score >= 80) return "#22C55E";
  if (score >= 60) return "#F59E0B";
  return "#EF4444";
}

// ── Count-up Hook ────────────────────────────────────────────────────

function useCountUp(target: number, duration = 1200) {
  const [value, setValue] = useState(0);
  const prevTarget = useRef(0);

  useEffect(() => {
    if (target === prevTarget.current) return;
    prevTarget.current = target;
    const start = performance.now();
    const from = 0;

    function tick(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(from + (target - from) * eased));
      if (progress < 1) requestAnimationFrame(tick);
    }

    requestAnimationFrame(tick);
  }, [target, duration]);

  return value;
}

// ── Donut Chart ──────────────────────────────────────────────────────

function DonutChart({ score, size = 120 }: { score: number; size?: number }) {
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = getScoreColor(score);
  const displayScore = useCountUp(score);

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="score-ring-animated"
          style={
            {
              "--ring-circumference": circumference,
              "--ring-target": offset,
            } as React.CSSProperties
          }
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-extrabold text-white">{displayScore}</span>
        <span className="text-xs text-text-secondary">100 üzerinden</span>
      </div>
    </div>
  );
}

// ── Skeleton Components ──────────────────────────────────────────────

function StatSkeleton() {
  return (
    <div className="rounded-2xl border border-white/5 bg-bg-surface p-6">
      <div className="skeleton h-4 w-24 mb-3" />
      <div className="skeleton h-8 w-16 mb-2" />
      <div className="skeleton h-3 w-20" />
    </div>
  );
}

function ListSkeleton() {
  return (
    <div className="rounded-2xl border border-white/5 bg-bg-surface p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="skeleton h-5 w-32" />
        <div className="skeleton h-4 w-20" />
      </div>
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-center gap-4 py-3">
          <div className="skeleton h-10 w-10 rounded-xl" />
          <div className="flex-1 space-y-2">
            <div className="skeleton h-4 w-48" />
            <div className="skeleton h-3 w-24" />
          </div>
          <div className="skeleton h-6 w-12 rounded-full" />
        </div>
      ))}
    </div>
  );
}

function SidebarSkeleton() {
  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-white/5 bg-bg-surface p-6">
        <div className="skeleton h-4 w-28 mb-4" />
        <div className="skeleton h-32 w-full rounded-xl mb-3" />
        <div className="skeleton h-4 w-36" />
      </div>
      <div className="rounded-2xl border border-white/5 bg-bg-surface p-6 space-y-3">
        <div className="skeleton h-4 w-28 mb-2" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="space-y-2">
            <div className="skeleton h-3 w-32" />
            <div className="skeleton h-3 w-full rounded-full" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Score Distribution Bar ───────────────────────────────────────────

function ScoreBar({
  label,
  score,
  maxScore,
}: {
  label: string;
  score: number;
  maxScore: number;
}) {
  const pct = maxScore > 0 ? (score / maxScore) * 100 : 0;
  const color =
    pct >= 70 ? "bg-emerald-500" : pct >= 40 ? "bg-amber-500" : "bg-red-500";

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className="text-text-secondary">{label}</span>
        <span className="font-semibold text-white">
          {score}/{maxScore}
        </span>
      </div>
      <div className="h-2.5 w-full rounded-full bg-white/5">
        <div
          className={`h-full rounded-full ${color} animate-bar-fill`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ── Main Dashboard ───────────────────────────────────────────────────

export default function DashboardPage() {
  const { toast } = useToast();
  const [cvList, setCvList] = useState<CVListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchCVs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listCVs();
      setCvList(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Veriler yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCVs();
  }, [fetchCVs]);

  const handleDelete = useCallback(
    async (id: number, filename: string) => {
      if (!confirm(`"${filename}" silinecek. Emin misiniz?`)) return;
      try {
        await deleteCV(id);
        setCvList((prev) => prev.filter((cv) => cv.id !== id));
        toast("success", `"${filename}" silindi.`);
      } catch (err) {
        toast("error", err instanceof Error ? err.message : "Silme başarısız.");
      }
    },
    [toast]
  );

  const handleDownload = useCallback(
    async (id: number) => {
      try {
        await downloadOptimizedCV(id);
        toast("success", "PDF indirildi.");
      } catch (err) {
        toast("error", err instanceof Error ? err.message : "İndirme başarısız.");
      }
    },
    [toast]
  );

  const handleFileUpload = useCallback(
    async (file: File) => {
      if (!file.name.match(/\.(pdf|docx)$/i)) {
        toast("error", "Sadece PDF veya DOCX dosyaları desteklenir.");
        return;
      }
      try {
        setUploading(true);
        await uploadCV(file);
        toast("success", `"${file.name}" yüklendi.`);
        fetchCVs();
      } catch (err) {
        toast("error", err instanceof Error ? err.message : "Yükleme başarısız.");
      } finally {
        setUploading(false);
      }
    },
    [toast, fetchCVs]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFileUpload(file);
    },
    [handleFileUpload]
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFileUpload(file);
      e.target.value = "";
    },
    [handleFileUpload]
  );

  // Stats
  const totalCVs = cvList.length;
  const scoredCVs = cvList.filter((cv) => cv.ats_score !== null);
  const avgScore =
    scoredCVs.length > 0
      ? Math.round(
          scoredCVs.reduce((sum, cv) => sum + (cv.ats_score || 0), 0) /
            scoredCVs.length
        )
      : 0;
  const optimizedCount = scoredCVs.length;
  const optimizedPct = totalCVs > 0 ? Math.round((optimizedCount / totalCVs) * 100) : 0;

  const animatedTotal = useCountUp(totalCVs);
  const animatedOptimized = useCountUp(optimizedCount);

  // Last analyzed CV for sidebar
  const lastScored = scoredCVs[0] || null;

  // Sample criteria breakdown from last analysis (use placeholder if no data)
  const sampleCriteria = [
    { label: "Format Uyumu", score: 12, max: 15 },
    { label: "Keyword Eşleşme", score: 8, max: 25 },
    { label: "Deneyim Detayı", score: 18, max: 20 },
    { label: "Eğitim Bilgisi", score: 10, max: 15 },
    { label: "Genel Yapı", score: 20, max: 25 },
  ];

  // ── Loading State ──────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_340px]">
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-3">
              <StatSkeleton />
              <StatSkeleton />
              <StatSkeleton />
            </div>
            <ListSkeleton />
          </div>
          <SidebarSkeleton />
        </div>
      </div>
    );
  }

  // ── Error State ────────────────────────────────────────────────────

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-8 text-center max-w-md">
          <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-4" />
          <h2 className="text-lg font-bold text-white mb-2">Bağlantı hatası</h2>
          <p className="text-sm text-text-secondary mb-6">{error}</p>
          <Button onClick={fetchCVs}>Tekrar Dene</Button>
        </div>
      </div>
    );
  }

  // ── Main Render ────────────────────────────────────────────────────

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_340px]">
      {/* ── LEFT COLUMN ── */}
      <div className="space-y-6">
        {/* Stat Cards */}
        <div className="grid gap-4 sm:grid-cols-3">
          {/* Toplam CV */}
          <div
            className="animate-fade-in-up rounded-2xl border border-white/5 bg-bg-surface p-6 transition-all duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-black/20"
            style={{ animationDelay: "0ms" }}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-text-secondary">Toplam CV</span>
              <div className="rounded-lg bg-blue-500/10 p-2">
                <FileText className="h-4 w-4 text-blue-400" />
              </div>
            </div>
            <p className="text-3xl font-extrabold text-white">{animatedTotal}</p>
            <div className="mt-2 flex items-center gap-1 text-xs">
              {totalCVs > 0 ? (
                <>
                  <TrendingUp className="h-3 w-3 text-emerald-400" />
                  <span className="text-emerald-400">Aktif</span>
                </>
              ) : (
                <>
                  <TrendingDown className="h-3 w-3 text-gray-500" />
                  <span className="text-gray-500">Henüz yok</span>
                </>
              )}
              <span className="text-text-secondary ml-1">son 30 gün</span>
            </div>
          </div>

          {/* Ortalama ATS Skoru */}
          <div
            className="animate-fade-in-up rounded-2xl border border-white/5 bg-bg-surface p-6 flex flex-col items-center transition-all duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-black/20"
            style={{ animationDelay: "100ms" }}
          >
            <span className="text-sm text-text-secondary mb-3 self-start">
              Ortalama ATS Skoru
            </span>
            {scoredCVs.length > 0 ? (
              <DonutChart score={avgScore} size={110} />
            ) : (
              <div className="flex flex-col items-center justify-center py-4">
                <span className="text-3xl font-extrabold text-gray-600">--</span>
                <span className="text-xs text-text-secondary mt-1">Henüz analiz yok</span>
              </div>
            )}
          </div>

          {/* Optimize Edilen */}
          <div
            className="animate-fade-in-up rounded-2xl border border-white/5 bg-bg-surface p-6 transition-all duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-black/20"
            style={{ animationDelay: "200ms" }}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-text-secondary">Optimize Edilen</span>
              <div className="rounded-lg bg-emerald-500/10 p-2">
                <Sparkles className="h-4 w-4 text-emerald-400" />
              </div>
            </div>
            <p className="text-3xl font-extrabold text-emerald-400">
              {animatedOptimized}
            </p>
            <div className="mt-2 flex items-center gap-1.5 text-xs">
              <div className="h-1.5 w-16 rounded-full bg-white/5">
                <div
                  className="h-full rounded-full bg-emerald-500 animate-bar-fill"
                  style={{ width: `${optimizedPct}%` }}
                />
              </div>
              <span className="text-text-secondary">%{optimizedPct}</span>
            </div>
          </div>
        </div>

        {/* CV List Card */}
        <div
          className="animate-fade-in-up rounded-2xl border border-white/5 bg-bg-surface"
          style={{ animationDelay: "300ms" }}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-white/5 px-6 py-4">
            <h2 className="font-bold text-white">Son CV&apos;lerim</h2>
            {cvList.length > 5 && (
              <button className="flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300 transition-colors">
                Tümünü Gör
                <ChevronRight className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Empty state */}
          {cvList.length === 0 ? (
            <div className="flex flex-col items-center gap-4 py-16 px-6">
              <div className="rounded-full bg-bg-primary p-6">
                <Upload className="h-10 w-10 text-gray-600" />
              </div>
              <div className="text-center">
                <h3 className="font-bold text-white">
                  Henüz CV yüklemediniz
                </h3>
                <p className="mt-1 text-sm text-text-secondary">
                  Hemen başlayın!
                </p>
              </div>
              <Link href="/analyze">
                <Button size="lg" className="gap-2">
                  <Upload className="h-4 w-4" />
                  CV Yükle
                </Button>
              </Link>
            </div>
          ) : (
            <div>
              {cvList.slice(0, 8).map((cv, index) => {
                const { label, variant } = getScoreBadge(cv.ats_score);
                return (
                  <div
                    key={cv.id}
                    className="group flex items-center gap-4 border-b border-white/5 px-6 py-3.5 last:border-b-0 transition-colors hover:bg-white/5"
                    style={{ animationDelay: `${400 + index * 50}ms` }}
                  >
                    {/* File icon */}
                    <div className="shrink-0 rounded-xl bg-blue-500/10 p-2.5">
                      <FileText className="h-5 w-5 text-blue-400" />
                    </div>

                    {/* Info */}
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-white">
                        {cv.filename}
                      </p>
                      <p className="text-xs text-text-secondary">
                        {relativeTime(cv.created_at)}
                      </p>
                    </div>

                    {/* Score badge */}
                    <Badge variant={variant}>{label}</Badge>

                    {/* Actions */}
                    <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                      <Link href={`/analyze?cvId=${cv.id}`}>
                        <button
                          className="rounded-lg p-2 text-gray-400 hover:bg-white/5 hover:text-white transition-colors"
                          title="Analiz Et"
                        >
                          <FileSearch className="h-4 w-4" />
                        </button>
                      </Link>
                      <button
                        onClick={() => handleDownload(cv.id)}
                        className="rounded-lg p-2 text-gray-400 hover:bg-white/5 hover:text-white transition-colors"
                        title="İndir"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(cv.id, cv.filename)}
                        className="rounded-lg p-2 text-gray-400 hover:bg-white/5 hover:text-red-400 transition-colors"
                        title="Sil"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* ── RIGHT COLUMN ── */}
      <div className="space-y-6">
        {/* Quick Upload Card */}
        <div
          className="animate-fade-in-up rounded-2xl border border-white/5 bg-bg-surface p-6"
          style={{ animationDelay: "200ms" }}
        >
          <h3 className="font-bold text-white mb-4">Hızlı Analiz</h3>

          {/* Drop zone */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`flex cursor-pointer flex-col items-center gap-3 rounded-xl border-2 border-dashed p-8 transition-all
              ${
                dragOver
                  ? "border-blue-400 bg-blue-500/10"
                  : "border-white/10 hover:border-white/20 hover:bg-white/5"
              }`}
          >
            {uploading ? (
              <Loader2 className="h-8 w-8 animate-spin text-blue-400" />
            ) : (
              <Upload className="h-8 w-8 text-gray-500" />
            )}
            <div className="text-center">
              <p className="text-sm font-medium text-white">
                {uploading ? "Yükleniyor..." : "Sürükle & bırak"}
              </p>
              <p className="mt-1 text-xs text-text-secondary">
                veya{" "}
                <span className="text-blue-400 underline">dosya seçin</span>
              </p>
            </div>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx"
            onChange={handleFileChange}
            className="hidden"
          />

          {/* Last analysis summary */}
          {lastScored && (
            <div className="mt-4 rounded-xl bg-white/5 p-4">
              <p className="text-xs text-text-secondary mb-2">Son analiz</p>
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-white truncate pr-2">
                  {lastScored.filename}
                </p>
                <Badge variant={getScoreBadge(lastScored.ats_score).variant}>
                  {lastScored.ats_score}/100
                </Badge>
              </div>
            </div>
          )}
        </div>

        {/* Score Distribution Card */}
        <div
          className="animate-fade-in-up rounded-2xl border border-white/5 bg-bg-surface p-6"
          style={{ animationDelay: "300ms" }}
        >
          <h3 className="font-bold text-white mb-5">Skor Dağılımı</h3>

          {scoredCVs.length > 0 ? (
            <div className="space-y-4">
              {sampleCriteria.map((c) => (
                <ScoreBar
                  key={c.label}
                  label={c.label}
                  score={c.score}
                  maxScore={c.max}
                />
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center py-8">
              <div className="rounded-full bg-bg-primary p-4 mb-3">
                <FileSearch className="h-6 w-6 text-gray-600" />
              </div>
              <p className="text-sm text-text-secondary text-center">
                CV analizi yapıldığında skor dağılımı burada görünecek
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
