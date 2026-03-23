"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  FileText,
  BarChart3,
  Sparkles,
  Loader2,
  AlertCircle,
  FileSearch,
  Download,
  Trash2,
  Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/toast";
import { listCVs, deleteCV, downloadOptimizedCV } from "@/lib/api";
import type { CVListItem } from "@/lib/types";

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
  if (score === null) return { label: "Analiz edilmedi", variant: "outline" as const };
  if (score >= 80) return { label: `${score}/100`, variant: "success" as const };
  if (score >= 60) return { label: `${score}/100`, variant: "default" as const };
  if (score >= 40) return { label: `${score}/100`, variant: "warning" as const };
  return { label: `${score}/100`, variant: "danger" as const };
}

export default function DashboardPage() {
  const { toast } = useToast();
  const [cvList, setCvList] = useState<CVListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCVs = useCallback(async () => {
    try {
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

  // Stats
  const totalCVs = cvList.length;
  const scoredCVs = cvList.filter((cv) => cv.ats_score !== null);
  const avgScore =
    scoredCVs.length > 0
      ? Math.round(scoredCVs.reduce((sum, cv) => sum + (cv.ats_score || 0), 0) / scoredCVs.length)
      : 0;
  const optimizedCount = scoredCVs.length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Dashboard</h1>
          <p className="mt-1 text-sm text-slate-400">
            CV&apos;lerinizi yönetin ve ATS skorlarınızı takip edin
          </p>
        </div>
        <Link href="/analyze">
          <Button>
            <Plus className="h-4 w-4" />
            Yeni Analiz
          </Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="flex items-center gap-4 p-5">
            <div className="rounded-xl bg-accent/10 p-3">
              <FileText className="h-6 w-6 text-accent" />
            </div>
            <div>
              <p className="text-2xl font-bold text-text-primary">{totalCVs}</p>
              <p className="text-xs text-slate-400">Toplam CV</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-5">
            <div className="rounded-xl bg-yellow-500/10 p-3">
              <BarChart3 className="h-6 w-6 text-yellow-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-text-primary">
                {scoredCVs.length > 0 ? avgScore : "—"}
              </p>
              <p className="text-xs text-slate-400">Ortalama Skor</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-5">
            <div className="rounded-xl bg-purple-500/10 p-3">
              <Sparkles className="h-6 w-6 text-purple-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-text-primary">{optimizedCount}</p>
              <p className="text-xs text-slate-400">Optimize Edilen</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-accent" />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/10 px-4 py-3">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
          <div>
            <p className="text-sm text-red-300">{error}</p>
            <button onClick={fetchCVs} className="mt-1 text-xs text-red-400 underline hover:text-red-300">
              Tekrar dene
            </button>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && cvList.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-4 py-16">
            <div className="rounded-full bg-bg-primary p-6">
              <FileText className="h-12 w-12 text-slate-600" />
            </div>
            <div className="text-center">
              <h3 className="text-base font-semibold text-text-primary">
                Henüz CV yüklemediniz
              </h3>
              <p className="mt-1 text-sm text-slate-400">
                İlk CV&apos;nizi yükleyerek ATS analizine başlayın
              </p>
            </div>
            <Link href="/analyze">
              <Button size="lg">
                <Plus className="h-4 w-4" />
                Hemen Başla
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* CV List */}
      {!loading && cvList.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-base font-semibold text-text-primary">
            CV&apos;leriniz ({cvList.length})
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {cvList.map((cv) => {
              const { label, variant } = getScoreBadge(cv.ats_score);
              return (
                <Card key={cv.id} className="group transition-all hover:border-slate-600">
                  <CardContent className="p-4">
                    {/* Top row */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="shrink-0 rounded-lg bg-accent/10 p-2">
                          <FileText className="h-5 w-5 text-accent" />
                        </div>
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium text-text-primary">
                            {cv.filename}
                          </p>
                          <p className="text-xs text-slate-500">
                            {relativeTime(cv.created_at)}
                          </p>
                        </div>
                      </div>
                      <Badge variant={variant}>{label}</Badge>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      <Link href={`/analyze?cvId=${cv.id}`} className="flex-1">
                        <Button variant="ghost" size="sm" className="w-full justify-start">
                          <FileSearch className="h-3.5 w-3.5" />
                          Analiz Et
                        </Button>
                      </Link>
                      {cv.ats_score !== null && (
                        <Link href={`/optimize/${cv.id}`} className="flex-1">
                          <Button variant="ghost" size="sm" className="w-full justify-start">
                            <Sparkles className="h-3.5 w-3.5" />
                            Optimize Et
                          </Button>
                        </Link>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDownload(cv.id)}
                      >
                        <Download className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(cv.id, cv.filename)}
                        className="text-slate-500 hover:text-red-400"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
