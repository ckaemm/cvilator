"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { KeywordMatch } from "@/lib/types";

interface KeywordAnalysisProps {
  keywordMatch: KeywordMatch;
  hasJobDescription: boolean;
}

export function KeywordAnalysis({ keywordMatch, hasJobDescription }: KeywordAnalysisProps) {
  const matchPercent = Math.round(keywordMatch.match_rate * 100);

  return (
    <Card className="animate-fade-in-up" style={{ animationDelay: "200ms" }}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Anahtar Kelime Analizi</CardTitle>
          <span className="text-xs text-slate-500">
            {hasJobDescription ? "İlana özel analiz" : "Genel analiz"}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Match rate bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">Eşleşme Oranı</span>
            <span className={`font-semibold tabular-nums ${
              matchPercent >= 60 ? "text-green-400" : matchPercent >= 40 ? "text-amber-400" : "text-red-400"
            }`}>
              %{matchPercent}
            </span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-slate-700">
            <div
              className={`h-full rounded-full transition-all duration-1000 ease-out ${
                matchPercent >= 60 ? "bg-success" : matchPercent >= 40 ? "bg-warning" : "bg-danger"
              }`}
              style={{ width: `${matchPercent}%` }}
            />
          </div>
        </div>

        {/* Two-column keyword layout */}
        <div className="grid gap-6 sm:grid-cols-2">
          {/* Found */}
          <div>
            <h4 className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-300">
              <span className="h-2 w-2 rounded-full bg-success" />
              Bulunan Kelimeler
              <span className="text-xs text-slate-500">({keywordMatch.found.length})</span>
            </h4>
            {keywordMatch.found.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {keywordMatch.found.map((kw) => (
                  <Badge key={kw} variant="success">{kw}</Badge>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-600 italic">Eşleşen kelime bulunamadı.</p>
            )}
          </div>

          {/* Missing */}
          <div>
            <h4 className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-300">
              <span className="h-2 w-2 rounded-full bg-danger" />
              Eksik Kelimeler
              <span className="text-xs text-slate-500">({keywordMatch.missing.length})</span>
            </h4>
            {keywordMatch.missing.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {keywordMatch.missing.map((kw) => (
                  <Badge key={kw} variant="danger">{kw}</Badge>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-600 italic">Eksik kelime yok, harika!</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
