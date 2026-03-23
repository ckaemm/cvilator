"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileText, Calendar, AlertCircle, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { listCVs } from "@/lib/api";
import type { CVListItem } from "@/lib/types";

function getScoreBadgeVariant(score: number | null) {
  if (score === null) return "outline" as const;
  if (score >= 80) return "success" as const;
  if (score >= 60) return "default" as const;
  if (score >= 40) return "warning" as const;
  return "danger" as const;
}

export default function HistoryPage() {
  const [cvList, setCvList] = useState<CVListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCVs()
      .then(setCvList)
      .catch((err) => setError(err instanceof Error ? err.message : "Veriler yüklenemedi."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Geçmiş</h1>
        <p className="mt-1 text-sm text-slate-400">Daha önce yüklediğiniz CV&apos;ler</p>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-accent" />
        </div>
      )}

      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/10 px-4 py-3">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {!loading && !error && cvList.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-4 py-12">
            <FileText className="h-12 w-12 text-slate-600" />
            <p className="text-sm text-slate-400">Henüz yüklenmiş CV bulunmuyor.</p>
            <Link href="/analyze" className="text-sm text-accent hover:underline">
              İlk CV&apos;nizi yükleyin
            </Link>
          </CardContent>
        </Card>
      )}

      {!loading && cvList.length > 0 && (
        <div className="space-y-3">
          {cvList.map((cv) => (
            <Link key={cv.id} href={`/analyze?cvId=${cv.id}`}>
              <Card className="transition-all hover:border-slate-600 cursor-pointer">
                <CardContent className="flex items-center justify-between p-4">
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-accent/10 p-2">
                      <FileText className="h-5 w-5 text-accent" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-text-primary">{cv.filename}</p>
                      <p className="flex items-center gap-1 text-xs text-slate-500">
                        <Calendar className="h-3 w-3" />
                        {new Date(cv.created_at).toLocaleDateString("tr-TR", {
                          day: "numeric",
                          month: "long",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                  </div>
                  <Badge variant={getScoreBadgeVariant(cv.ats_score)}>
                    {cv.ats_score !== null ? `${cv.ats_score}/100` : "Analiz edilmedi"}
                  </Badge>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
