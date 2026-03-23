"use client";

import { useEffect, useRef, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { BadgeVariant } from "@/components/ui/badge";

interface ATSScoreCardProps {
  score: number;
  grade: string;
  summary: string;
}

function getScoreColor(score: number) {
  if (score >= 81) return { ring: "#16a34a", text: "text-green-400" };
  if (score >= 61) return { ring: "#eab308", text: "text-yellow-400" };
  if (score >= 41) return { ring: "#d97706", text: "text-amber-400" };
  return { ring: "#dc2626", text: "text-red-400" };
}

function getGradeLabel(score: number): { label: string; variant: BadgeVariant } {
  if (score >= 81) return { label: "Mükemmel", variant: "success" };
  if (score >= 61) return { label: "İyi", variant: "default" };
  if (score >= 41) return { label: "Orta", variant: "warning" };
  return { label: "Kritik", variant: "danger" };
}

export function ATSScoreCard({ score, grade, summary }: ATSScoreCardProps) {
  const [displayScore, setDisplayScore] = useState(0);
  const animationRef = useRef<number>(0);
  const startTimeRef = useRef<number>(0);

  const radius = 58;
  const circumference = 2 * Math.PI * radius;
  const targetOffset = circumference - (score / 100) * circumference;
  const { ring, text } = getScoreColor(score);
  const { label, variant } = getGradeLabel(score);

  useEffect(() => {
    startTimeRef.current = 0;

    function animate(timestamp: number) {
      if (!startTimeRef.current) startTimeRef.current = timestamp;
      const elapsed = timestamp - startTimeRef.current;
      const duration = 1500;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayScore(Math.round(eased * score));

      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      }
    }

    animationRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationRef.current);
  }, [score]);

  return (
    <Card className="animate-fade-in-up">
      <CardContent className="flex flex-col items-center gap-6 py-8 sm:flex-row sm:items-start sm:justify-around">
        {/* Score circle */}
        <div className="flex flex-col items-center gap-3">
          <div className="relative h-40 w-40">
            <svg className="h-full w-full -rotate-90" viewBox="0 0 128 128">
              {/* Background ring */}
              <circle
                cx="64"
                cy="64"
                r={radius}
                fill="none"
                stroke="#334155"
                strokeWidth="7"
              />
              {/* Score ring */}
              <circle
                cx="64"
                cy="64"
                r={radius}
                fill="none"
                stroke={ring}
                strokeWidth="7"
                strokeLinecap="round"
                strokeDasharray={circumference}
                className="score-ring-animated"
                style={{
                  "--ring-circumference": `${circumference}`,
                  "--ring-target": `${targetOffset}`,
                } as React.CSSProperties}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={`text-4xl font-bold tabular-nums ${text}`}>
                {displayScore}
              </span>
              <span className="text-xs text-slate-400">/100</span>
            </div>
          </div>
          <Badge variant={variant} className="text-sm px-3 py-1">
            {label}
          </Badge>
          {grade && grade !== label && (
            <span className="text-xs text-slate-500">{grade}</span>
          )}
        </div>

        {/* Summary */}
        <div className="flex-1 max-w-lg">
          <h3 className="mb-3 text-base font-semibold text-text-primary">Genel Değerlendirme</h3>
          <p className="text-sm leading-relaxed text-slate-300">{summary}</p>
        </div>
      </CardContent>
    </Card>
  );
}
