"use client";

import { useState } from "react";
import { AlertCircle, Lightbulb, ArrowRight, ChevronDown } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { SectionFeedback as SectionFeedbackType } from "@/lib/types";

function QualityBadge({ quality }: { quality: string }) {
  switch (quality) {
    case "good":
      return <Badge variant="success">İyi</Badge>;
    case "medium":
      return <Badge variant="warning">Orta</Badge>;
    case "poor":
      return <Badge variant="danger">Zayıf</Badge>;
    default:
      return <Badge variant="outline">{quality}</Badge>;
  }
}

function BulletComparison({ original, improved }: { original: string; improved: string }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <div className="rounded-lg border border-red-900/30 bg-red-950/20 p-3">
        <p className="mb-1 text-xs font-medium text-red-400">Mevcut</p>
        <p className="text-sm text-slate-300">{original}</p>
      </div>
      <div className="rounded-lg border border-green-900/30 bg-green-950/20 p-3">
        <p className="mb-1 text-xs font-medium text-green-400">Önerilen</p>
        <p className="text-sm text-slate-300">{improved}</p>
      </div>
    </div>
  );
}

function SectionCard({ section, index }: { section: SectionFeedbackType; index: number }) {
  const [showRewrites, setShowRewrites] = useState(false);
  const hasRewrites = section.rewritten_bullets.length > 0;

  return (
    <Card
      className="animate-fade-in-up"
      style={{ animationDelay: `${index * 120}ms` }}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{section.section_name}</CardTitle>
          <QualityBadge quality={section.current_quality} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Issues */}
        {section.issues.length > 0 && (
          <div>
            <h4 className="mb-2 flex items-center gap-1.5 text-sm font-medium text-red-400">
              <AlertCircle className="h-3.5 w-3.5" />
              Sorunlar
            </h4>
            <ul className="space-y-1.5">
              {section.issues.map((issue, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-red-500" />
                  {issue}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Suggestions */}
        {section.suggestions.length > 0 && (
          <div>
            <h4 className="mb-2 flex items-center gap-1.5 text-sm font-medium text-green-400">
              <Lightbulb className="h-3.5 w-3.5" />
              Öneriler
            </h4>
            <ul className="space-y-1.5">
              {section.suggestions.map((suggestion, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-green-500" />
                  {suggestion}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Rewritten bullets toggle */}
        {hasRewrites && (
          <div>
            <button
              onClick={() => setShowRewrites(!showRewrites)}
              className="flex items-center gap-2 text-sm font-medium text-accent hover:text-blue-400 transition-colors"
            >
              <ArrowRight className={`h-3.5 w-3.5 transition-transform ${showRewrites ? "rotate-90" : ""}`} />
              Yeniden Yazılmış ({section.rewritten_bullets.length})
              <ChevronDown className={`h-3.5 w-3.5 transition-transform ${showRewrites ? "rotate-180" : ""}`} />
            </button>

            <div className="accordion-content mt-3" data-open={showRewrites}>
              <div className="accordion-inner space-y-3">
                {section.rewritten_bullets.map((bullet, i) => (
                  <BulletComparison
                    key={i}
                    original={bullet.original}
                    improved={bullet.improved}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Empty state */}
        {section.issues.length === 0 && section.suggestions.length === 0 && !hasRewrites && (
          <p className="text-sm text-slate-500 italic">Bu bölüm için ek geri bildirim yok.</p>
        )}
      </CardContent>
    </Card>
  );
}

interface SectionFeedbackProps {
  sections: SectionFeedbackType[];
  overallAssessment: string;
  actionItems: string[];
  atsTips: string[];
}

export function SectionFeedbackList({
  sections,
  overallAssessment,
  actionItems,
  atsTips,
}: SectionFeedbackProps) {
  return (
    <div className="space-y-6">
      {/* Overall assessment */}
      <Card className="animate-fade-in-up border-accent/30">
        <CardHeader>
          <CardTitle>AI Değerlendirmesi</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm leading-relaxed text-slate-300">{overallAssessment}</p>

          {/* Action items */}
          {actionItems.length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-amber-400">Öncelikli Aksiyonlar</h4>
              <ol className="list-decimal space-y-1 pl-5">
                {actionItems.map((item, i) => (
                  <li key={i} className="text-sm text-slate-400">{item}</li>
                ))}
              </ol>
            </div>
          )}

          {/* ATS tips */}
          {atsTips.length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-blue-400">ATS İpuçları</h4>
              <ul className="space-y-1">
                {atsTips.map((tip, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-500" />
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Per-section cards */}
      {sections.map((section, i) => (
        <SectionCard key={section.section_name} section={section} index={i} />
      ))}
    </div>
  );
}
