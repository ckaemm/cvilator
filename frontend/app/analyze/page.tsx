"use client";

import { useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { Loader2, FileSearch, AlertCircle } from "lucide-react";
import { CVUpload } from "@/components/cv-upload";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { analyzeCV, analyzeCVWithJob } from "@/lib/api";
import type { ATSScoreResponse, CriteriaDetail } from "@/lib/types";

function ScoreCircle({ score, grade }: { score: number; grade: string }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  let color = "text-danger";
  if (score >= 80) color = "text-green-400";
  else if (score >= 60) color = "text-accent";
  else if (score >= 40) color = "text-warning";

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative h-36 w-36">
        <svg className="h-full w-full -rotate-90" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r={radius} fill="none" stroke="#334155" strokeWidth="8" />
          <circle
            cx="60"
            cy="60"
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className={`transition-all duration-1000 ${color}`}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-3xl font-bold ${color}`}>{score}</span>
          <span className="text-xs text-slate-400">/100</span>
        </div>
      </div>
      <Badge
        variant={score >= 80 ? "success" : score >= 60 ? "default" : score >= 40 ? "warning" : "danger"}
      >
        {grade}
      </Badge>
    </div>
  );
}

function CriteriaRow({ criteria }: { criteria: CriteriaDetail }) {
  const percentage = Math.round((criteria.score / criteria.max_score) * 100);
  let barColor = "bg-danger";
  if (percentage >= 80) barColor = "bg-success";
  else if (percentage >= 60) barColor = "bg-accent";
  else if (percentage >= 40) barColor = "bg-warning";

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-300">{criteria.name}</span>
        <span className="text-slate-400">
          {criteria.score}/{criteria.max_score}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-700">
        <div
          className={`h-full rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-slate-500">{criteria.feedback}</p>
    </div>
  );
}

export default function AnalyzePage() {
  const searchParams = useSearchParams();
  const initialCvId = searchParams.get("cvId");

  const [cvId, setCvId] = useState<number | null>(
    initialCvId ? parseInt(initialCvId, 10) : null
  );
  const [jobDescription, setJobDescription] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<ATSScoreResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUploadSuccess = useCallback((id: number) => {
    setCvId(id);
    setResult(null);
    setError(null);
  }, []);

  const handleAnalyze = useCallback(async () => {
    if (!cvId) return;

    setAnalyzing(true);
    setError(null);
    setResult(null);

    try {
      let data: ATSScoreResponse;
      if (jobDescription.trim().length >= 10) {
        data = await analyzeCVWithJob(cvId, jobDescription.trim());
      } else {
        data = await analyzeCV(cvId);
      }
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analiz sırasında bir hata oluştu.");
    } finally {
      setAnalyzing(false);
    }
  }, [cvId, jobDescription]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">CV Analizi</h1>
        <p className="mt-1 text-sm text-slate-400">
          CV&apos;nizi yükleyin ve ATS uyumluluk analizini başlatın
        </p>
      </div>

      {/* Upload */}
      <Card>
        <CardHeader>
          <CardTitle>CV Yükle</CardTitle>
        </CardHeader>
        <CardContent>
          <CVUpload onUploadSuccess={handleUploadSuccess} />
        </CardContent>
      </Card>

      {/* Job description (optional) */}
      {cvId && (
        <Card>
          <CardHeader>
            <CardTitle>İş İlanı (Opsiyonel)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="İş ilanı metnini buraya yapıştırın (en az 10 karakter). Boş bırakırsanız genel analiz yapılır."
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              rows={5}
            />
            <Button onClick={handleAnalyze} loading={analyzing} disabled={analyzing}>
              <FileSearch className="h-4 w-4" />
              {analyzing ? "Analiz Ediliyor..." : "Analizi Başlat"}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/10 px-4 py-3">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {/* Loading skeleton */}
      {analyzing && (
        <Card>
          <CardContent className="flex flex-col items-center gap-4 py-12">
            <Loader2 className="h-10 w-10 animate-spin text-accent" />
            <p className="text-sm text-slate-400">CV analiz ediliyor...</p>
            <div className="w-full max-w-md space-y-3">
              <div className="skeleton h-4 w-full" />
              <div className="skeleton h-4 w-3/4" />
              <div className="skeleton h-4 w-5/6" />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {result && !analyzing && (
        <div className="space-y-6">
          {/* Score overview */}
          <Card>
            <CardContent className="flex flex-col items-center gap-6 py-8 sm:flex-row sm:items-start sm:justify-around">
              <ScoreCircle score={result.total_score} grade={result.grade} />
              <div className="flex-1 max-w-lg">
                <h3 className="mb-3 text-base font-semibold text-text-primary">Özet</h3>
                <p className="text-sm leading-relaxed text-slate-300">{result.summary}</p>
              </div>
            </CardContent>
          </Card>

          {/* Criteria breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Kriter Detayları</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {result.criteria.map((c) => (
                <CriteriaRow key={c.name} criteria={c} />
              ))}
            </CardContent>
          </Card>

          {/* Keywords */}
          <Card>
            <CardHeader>
              <CardTitle>Anahtar Kelime Analizi</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <span className="text-sm text-slate-400">Eşleşme Oranı:</span>
                <Badge variant={result.keyword_match.match_rate >= 0.6 ? "success" : "warning"}>
                  %{Math.round(result.keyword_match.match_rate * 100)}
                </Badge>
              </div>

              {result.keyword_match.found.length > 0 && (
                <div>
                  <p className="mb-2 text-sm font-medium text-slate-300">Bulunan Kelimeler</p>
                  <div className="flex flex-wrap gap-2">
                    {result.keyword_match.found.map((kw) => (
                      <Badge key={kw} variant="success">{kw}</Badge>
                    ))}
                  </div>
                </div>
              )}

              {result.keyword_match.missing.length > 0 && (
                <div>
                  <p className="mb-2 text-sm font-medium text-slate-300">Eksik Kelimeler</p>
                  <div className="flex flex-wrap gap-2">
                    {result.keyword_match.missing.map((kw) => (
                      <Badge key={kw} variant="danger">{kw}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
