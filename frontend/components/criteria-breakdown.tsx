"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { CriteriaDetail } from "@/lib/types";

function getBarColor(percentage: number) {
  if (percentage >= 80) return "bg-success";
  if (percentage >= 60) return "bg-yellow-500";
  if (percentage >= 40) return "bg-warning";
  return "bg-danger";
}

function CriteriaRow({ criteria, index }: { criteria: CriteriaDetail; index: number }) {
  const [open, setOpen] = useState(false);
  const percentage = Math.round((criteria.score / criteria.max_score) * 100);
  const barColor = getBarColor(percentage);

  return (
    <div
      className="animate-fade-in-up"
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left group"
      >
        <div className="space-y-2">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-slate-200">{criteria.name}</span>
              <ChevronDown
                className={`h-4 w-4 text-slate-500 transition-transform duration-200 ${
                  open ? "rotate-180" : ""
                }`}
              />
            </div>
            <span className="text-sm font-semibold tabular-nums text-slate-300">
              {criteria.score}/{criteria.max_score}
            </span>
          </div>

          {/* Progress bar */}
          <div className="h-2 overflow-hidden rounded-full bg-slate-700">
            <div
              className={`h-full rounded-full transition-all duration-700 ease-out ${barColor}`}
              style={{ width: `${percentage}%` }}
            />
          </div>

          {/* Feedback */}
          <p className="text-xs text-slate-500 group-hover:text-slate-400 transition-colors">
            {criteria.feedback}
          </p>
        </div>
      </button>

      {/* Accordion detail */}
      <div className="accordion-content" data-open={open}>
        <div className="accordion-inner">
          {criteria.details.length > 0 && (
            <ul className="mt-3 space-y-1.5 border-l-2 border-slate-700 pl-4">
              {criteria.details.map((detail, i) => (
                <li key={i} className="text-xs text-slate-400">
                  {detail}
                </li>
              ))}
            </ul>
          )}
          {criteria.details.length === 0 && (
            <p className="mt-3 text-xs text-slate-600 italic">Ek detay bulunmuyor.</p>
          )}
        </div>
      </div>
    </div>
  );
}

interface CriteriaBreakdownProps {
  criteria: CriteriaDetail[];
}

export function CriteriaBreakdown({ criteria }: CriteriaBreakdownProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Kriter Detayları</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        {criteria.map((c, i) => (
          <CriteriaRow key={c.name} criteria={c} index={i} />
        ))}
      </CardContent>
    </Card>
  );
}
