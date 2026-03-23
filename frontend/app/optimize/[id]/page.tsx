"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Loader2,
  CheckSquare,
  Square,
  Download,
  Sparkles,
  AlertCircle,
  ArrowLeft,
  CheckCheck,
  XSquare,
  Eye,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { OptimizedPreview } from "@/components/optimized-preview";
import { getCVDetail, applySuggestions, downloadOptimizedCV } from "@/lib/api";
import type { CVDetail, AIFeedback, SectionFeedback, RewrittenBullet } from "@/lib/types";

interface Suggestion {
  id: number;
  sectionName: string;
  type: "issue" | "suggestion" | "rewrite";
  original: string;
  improved: string;
}

function extractSuggestions(feedback: AIFeedback): Suggestion[] {
  const suggestions: Suggestion[] = [];
  let id = 0;

  for (const section of feedback.section_feedback) {
    // Issues as suggestions
    for (const issue of section.issues) {
      suggestions.push({
        id: id++,
        sectionName: section.section_name,
        type: "issue",
        original: issue,
        improved: `[Düzelt] ${issue}`,
      });
    }

    // Suggestions
    for (const sug of section.suggestions) {
      suggestions.push({
        id: id++,
        sectionName: section.section_name,
        type: "suggestion",
        original: "",
        improved: sug,
      });
    }

    // Rewritten bullets
    for (const bullet of section.rewritten_bullets) {
      suggestions.push({
        id: id++,
        sectionName: section.section_name,
        type: "rewrite",
        original: bullet.original,
        improved: bullet.improved,
      });
    }
  }

  // Keyword placements
  for (const kp of feedback.keyword_placement) {
    suggestions.push({
      id: id++,
      sectionName: "Anahtar Kelimeler",
      type: "suggestion",
      original: "",
      improved: `"${kp.keyword}": ${kp.suggestion}`,
    });
  }

  return suggestions;
}

function SuggestionCard({
  suggestion,
  checked,
  onToggle,
}: {
  suggestion: Suggestion;
  checked: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      className={`w-full text-left rounded-lg border p-4 transition-all ${
        checked
          ? "border-accent/50 bg-accent/5"
          : "border-slate-700/50 bg-bg-surface hover:border-slate-600"
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Checkbox */}
        <div className="mt-0.5 shrink-0">
          {checked ? (
            <CheckSquare className="h-5 w-5 text-accent" />
          ) : (
            <Square className="h-5 w-5 text-slate-500" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          {/* Section + type badges */}
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="text-[10px]">
              {suggestion.sectionName}
            </Badge>
            <Badge
              variant={
                suggestion.type === "rewrite"
                  ? "default"
                  : suggestion.type === "issue"
                  ? "danger"
                  : "success"
              }
              className="text-[10px]"
            >
              {suggestion.type === "rewrite"
                ? "Yeniden Yaz"
                : suggestion.type === "issue"
                ? "Sorun"
                : "Öneri"}
            </Badge>
          </div>

          {/* Diff view for rewrites */}
          {suggestion.type === "rewrite" && suggestion.original && (
            <div className="space-y-2">
              <div className="rounded border border-red-900/20 bg-red-950/10 px-3 py-2">
                <p className="text-[10px] font-medium text-red-400 mb-1">Mevcut</p>
                <p className="text-sm text-slate-300">{suggestion.original}</p>
              </div>
              <div className="rounded border border-green-900/20 bg-green-950/10 px-3 py-2">
                <p className="text-[10px] font-medium text-green-400 mb-1">Önerilen</p>
                <p className="text-sm text-slate-300">{suggestion.improved}</p>
              </div>
            </div>
          )}

          {/* Simple text for suggestions and issues */}
          {suggestion.type !== "rewrite" && (
            <p className="text-sm text-slate-300">{suggestion.improved}</p>
          )}

          {/* Issue with original text */}
          {suggestion.type === "issue" && suggestion.original && (
            <p className="mt-1 text-xs text-slate-500">{suggestion.original}</p>
          )}
        </div>
      </div>
    </button>
  );
}

export default function OptimizePage() {
  const params = useParams();
  const router = useRouter();
  const cvId = Number(params.id);

  const [cv, setCv] = useState<CVDetail | null>(null);
  const [feedback, setFeedback] = useState<AIFeedback | null>(null);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());

  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [applied, setApplied] = useState(false);
  const [optimizedText, setOptimizedText] = useState<string>("");
  const [optimizedSections, setOptimizedSections] = useState<Record<string, string>>({});

  // Load CV detail and AI feedback
  useEffect(() => {
    async function load() {
      try {
        const detail = await getCVDetail(cvId);
        setCv(detail);

        if (detail.ats_score === null) {
          setError("Bu CV henüz analiz edilmemiş. Önce analiz sayfasından analiz edin.");
          setLoading(false);
          return;
        }

        if (!detail.ai_feedback) {
          setError("Bu CV için AI analizi yapılmamış. Önce analiz sayfasından optimizasyon yapın.");
          setLoading(false);
          return;
        }

        const fb = detail.ai_feedback;
        setFeedback(fb);

        const extracted = extractSuggestions(fb);
        setSuggestions(extracted);

        // Default: select all
        setSelected(new Set(extracted.map((s) => s.id)));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Veri yüklenirken hata oluştu.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [cvId]);

  const toggleSuggestion = useCallback((id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const selectAll = useCallback(() => {
    setSelected(new Set(suggestions.map((s) => s.id)));
  }, [suggestions]);

  const deselectAll = useCallback(() => {
    setSelected(new Set());
  }, []);

  // Compute preview highlights
  const highlightedTexts = useMemo(() => {
    const set = new Set<string>();
    for (const s of suggestions) {
      if (selected.has(s.id) && s.improved) {
        set.add(s.improved);
      }
    }
    return set;
  }, [suggestions, selected]);

  const handleApplyAndDownload = useCallback(async () => {
    if (selected.size === 0) return;

    setApplying(true);
    setError(null);

    try {
      const acceptedIndices = Array.from(selected);
      const result = await applySuggestions(cvId, acceptedIndices);
      setOptimizedText(result.optimized_text);
      setOptimizedSections(result.optimized_sections);
      setApplied(true);

      // Auto-download PDF
      setDownloading(true);
      await downloadOptimizedCV(cvId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Uygulama sırasında hata oluştu.");
    } finally {
      setApplying(false);
      setDownloading(false);
    }
  }, [cvId, selected]);

  const handleDownloadOnly = useCallback(async () => {
    setDownloading(true);
    setError(null);
    try {
      await downloadOptimizedCV(cvId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "İndirme sırasında hata oluştu.");
    } finally {
      setDownloading(false);
    }
  }, [cvId]);

  // Loading state
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20">
        <Loader2 className="h-10 w-10 animate-spin text-accent" />
        <p className="text-sm text-slate-400">CV verileri yükleniyor...</p>
      </div>
    );
  }

  // Error with no data
  if (error && !feedback) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
          Geri
        </Button>
        <div className="flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/10 px-4 py-3">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
          <p className="text-sm text-red-300">{error}</p>
        </div>
      </div>
    );
  }

  const previewText = applied && optimizedText ? optimizedText : cv?.raw_text || "";
  const previewSections =
    applied && Object.keys(optimizedSections).length > 0
      ? optimizedSections
      : cv?.sections || {};

  return (
    <div className="space-y-6 pb-24">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={() => router.back()}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-2xl font-bold text-text-primary">Optimizasyon</h1>
          </div>
          <p className="mt-1 ml-11 text-sm text-slate-400">
            {cv?.filename} — {suggestions.length} öneri bulundu
          </p>
        </div>
        {applied && (
          <Badge variant="success" className="text-sm px-3 py-1">
            Uygulandı
          </Badge>
        )}
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/10 px-4 py-3">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {/* Main layout: suggestions + preview */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Left: Suggestions (60%) */}
        <div className="lg:col-span-3 space-y-4">
          {/* Toolbar */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={selectAll}>
                <CheckCheck className="h-4 w-4" />
                Tümünü Seç
              </Button>
              <Button variant="ghost" size="sm" onClick={deselectAll}>
                <XSquare className="h-4 w-4" />
                Tümünü Kaldır
              </Button>
            </div>
            <Badge variant={selected.size > 0 ? "default" : "outline"}>
              {selected.size} / {suggestions.length} seçili
            </Badge>
          </div>

          {/* Suggestion cards */}
          <div className="space-y-3">
            {suggestions.map((s) => (
              <SuggestionCard
                key={s.id}
                suggestion={s}
                checked={selected.has(s.id)}
                onToggle={() => toggleSuggestion(s.id)}
              />
            ))}
          </div>

          {suggestions.length === 0 && (
            <Card>
              <CardContent className="flex flex-col items-center gap-3 py-10">
                <Sparkles className="h-8 w-8 text-slate-600" />
                <p className="text-sm text-slate-400">Henüz öneri bulunmuyor.</p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right: Preview (40%) */}
        <div className="lg:col-span-2">
          <div className="sticky top-8">
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <Eye className="h-4 w-4 text-accent" />
                  <CardTitle className="text-base">Canlı Önizleme</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="p-3">
                <OptimizedPreview
                  text={previewText}
                  sections={previewSections}
                  highlights={highlightedTexts}
                />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Sticky bottom bar */}
      <div className="fixed bottom-0 left-0 right-0 z-30 border-t border-slate-700/50 bg-bg-primary/95 backdrop-blur-sm lg:left-64">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <span className="text-sm text-slate-400">
            <span className="font-medium text-text-primary">{selected.size}</span> öneri seçildi
          </span>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              onClick={handleDownloadOnly}
              loading={downloading}
              disabled={downloading || applying}
            >
              <Download className="h-4 w-4" />
              PDF İndir
            </Button>
            <Button
              size="lg"
              onClick={handleApplyAndDownload}
              loading={applying}
              disabled={applying || downloading || selected.size === 0}
            >
              <Sparkles className="h-4 w-4" />
              Önerileri Uygula &amp; İndir
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
