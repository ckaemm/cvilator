"use client";

import { useState, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Loader2, CheckCircle2, Circle, Upload as UploadIcon, Sparkles } from "lucide-react";
import { CVUpload } from "@/components/cv-upload";
import { JobDescriptionInput } from "@/components/job-description-input";
import { ATSScoreCard } from "@/components/ats-score-card";
import { CriteriaBreakdown } from "@/components/criteria-breakdown";
import { SectionFeedbackList } from "@/components/section-feedback";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { analyzeCV, analyzeCVWithJob, optimizeCV } from "@/lib/api";
import type { ATSScoreResponse, OptimizationResponse } from "@/lib/types";

type Step = "upload" | "analyze" | "ai-feedback" | "done";

const steps: { key: Step; label: string }[] = [
  { key: "upload", label: "CV Yükle" },
  { key: "analyze", label: "ATS Analizi" },
  { key: "ai-feedback", label: "AI Feedback" },
  { key: "done", label: "Tamamlandı" },
];

function StepIndicator({ currentStep }: { currentStep: Step }) {
  const currentIndex = steps.findIndex((s) => s.key === currentStep);

  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-2 sm:gap-0">
      {steps.map((step, i) => {
        const isCompleted = i < currentIndex;
        const isCurrent = i === currentIndex;

        return (
          <div key={step.key} className="flex items-center">
            <div className="flex items-center gap-2">
              {isCompleted ? (
                <CheckCircle2 className="h-5 w-5 shrink-0 text-green-400" />
              ) : isCurrent ? (
                <div className="h-5 w-5 shrink-0 rounded-full border-2 border-accent bg-accent/20" />
              ) : (
                <Circle className="h-5 w-5 shrink-0 text-slate-600" />
              )}
              <span
                className={`whitespace-nowrap text-xs font-medium ${
                  isCompleted
                    ? "text-green-400"
                    : isCurrent
                    ? "text-accent"
                    : "text-slate-600"
                }`}
              >
                {step.label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div
                className={`mx-3 hidden h-px w-8 sm:block ${
                  isCompleted ? "bg-green-400" : "bg-slate-700"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function AnalysisSkeleton() {
  return (
    <div className="space-y-6">
      {/* Score skeleton */}
      <Card>
        <CardContent className="flex flex-col items-center gap-6 py-8 sm:flex-row sm:items-start sm:justify-around">
          <div className="skeleton h-40 w-40 rounded-full" />
          <div className="flex-1 max-w-lg space-y-3">
            <div className="skeleton h-5 w-40" />
            <div className="skeleton h-4 w-full" />
            <div className="skeleton h-4 w-4/5" />
            <div className="skeleton h-4 w-3/5" />
          </div>
        </CardContent>
      </Card>
      {/* Criteria skeleton */}
      <Card>
        <CardContent className="space-y-5 py-6">
          <div className="skeleton h-5 w-32" />
          {[...Array(4)].map((_, i) => (
            <div key={i} className="space-y-2">
              <div className="flex justify-between">
                <div className="skeleton h-4 w-28" />
                <div className="skeleton h-4 w-12" />
              </div>
              <div className="skeleton h-2 w-full" />
              <div className="skeleton h-3 w-3/4" />
            </div>
          ))}
        </CardContent>
      </Card>
      {/* Keyword skeleton */}
      <Card>
        <CardContent className="py-6">
          <div className="skeleton h-5 w-40 mb-4" />
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="skeleton h-6 w-20 rounded-full" />
              ))}
            </div>
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="skeleton h-6 w-20 rounded-full" />
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function AIFeedbackSkeleton() {
  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="py-6 space-y-4">
          <div className="skeleton h-5 w-36" />
          <div className="skeleton h-4 w-full" />
          <div className="skeleton h-4 w-5/6" />
          <div className="skeleton h-4 w-4/6" />
        </CardContent>
      </Card>
      {[...Array(3)].map((_, i) => (
        <Card key={i}>
          <CardContent className="py-6 space-y-3">
            <div className="flex justify-between">
              <div className="skeleton h-5 w-32" />
              <div className="skeleton h-5 w-16 rounded-full" />
            </div>
            <div className="skeleton h-3 w-full" />
            <div className="skeleton h-3 w-4/5" />
            <div className="skeleton h-3 w-3/5" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function AnalyzePageContent() {
  const searchParams = useSearchParams();
  const initialCvId = searchParams.get("cvId");

  const [cvId, setCvId] = useState<number | null>(
    initialCvId ? parseInt(initialCvId, 10) : null
  );
  const [currentStep, setCurrentStep] = useState<Step>(
    initialCvId ? "analyze" : "upload"
  );
  const [jobDescription, setJobDescription] = useState("");

  // Results
  const [atsResult, setAtsResult] = useState<ATSScoreResponse | null>(null);
  const [optimization, setOptimization] = useState<OptimizationResponse | null>(null);

  // Loading states
  const [analyzingATS, setAnalyzingATS] = useState(false);
  const [analyzingAI, setAnalyzingAI] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUploadSuccess = useCallback((id: number) => {
    setCvId(id);
    setCurrentStep("analyze");
    setAtsResult(null);
    setOptimization(null);
    setError(null);
  }, []);

  const handleAnalyze = useCallback(
    async (jobDesc: string) => {
      if (!cvId) return;
      setJobDescription(jobDesc);
      setError(null);
      setAtsResult(null);
      setOptimization(null);

      // Step 1: ATS Analysis
      setCurrentStep("analyze");
      setAnalyzingATS(true);
      try {
        let ats: ATSScoreResponse;
        if (jobDesc.trim().length >= 10) {
          ats = await analyzeCVWithJob(cvId, jobDesc.trim());
        } else {
          ats = await analyzeCV(cvId);
        }
        setAtsResult(ats);
        setAnalyzingATS(false);

        // Step 2: AI Feedback
        setCurrentStep("ai-feedback");
        setAnalyzingAI(true);
        const opt = await optimizeCV(cvId, jobDesc);
        setOptimization(opt);
        setAnalyzingAI(false);
        setCurrentStep("done");
      } catch (err) {
        setAnalyzingATS(false);
        setAnalyzingAI(false);
        setError(err instanceof Error ? err.message : "Analiz sırasında bir hata oluştu.");
      }
    },
    [cvId]
  );

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">CV Analizi</h1>
        <p className="mt-1 text-sm text-slate-400">
          CV&apos;nizi yükleyin, ATS uyumluluk analizini ve AI optimizasyonunu başlatın
        </p>
      </div>

      {/* Step indicator */}
      <StepIndicator currentStep={currentStep} />

      {/* Upload section */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <UploadIcon className="h-5 w-5 text-accent" />
            <h2 className="text-base font-semibold text-text-primary">CV Yükle</h2>
            {cvId && (
              <span className="text-xs text-green-400 ml-auto">CV #{cvId} yüklendi</span>
            )}
          </div>
          <CVUpload onUploadSuccess={handleUploadSuccess} />
        </CardContent>
      </Card>

      {/* Job description + analyze trigger */}
      {cvId && !analyzingATS && !analyzingAI && currentStep !== "done" && (
        <JobDescriptionInput
          onAnalyze={handleAnalyze}
          loading={analyzingATS || analyzingAI}
          disabled={!cvId}
        />
      )}

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-danger/30 bg-danger/10 px-4 py-3">
          <span className="mt-0.5 text-red-400 text-sm">!</span>
          <div>
            <p className="text-sm text-red-300">{error}</p>
            <button
              onClick={() => {
                setError(null);
                setCurrentStep("analyze");
              }}
              className="mt-1 text-xs text-red-400 underline hover:text-red-300"
            >
              Tekrar dene
            </button>
          </div>
        </div>
      )}

      {/* ATS Analysis loading */}
      {analyzingATS && (
        <div className="space-y-4">
          <div className="flex items-center gap-3 rounded-lg border border-accent/20 bg-accent/5 px-4 py-3">
            <Loader2 className="h-5 w-5 animate-spin text-accent" />
            <p className="text-sm text-slate-300">ATS analizi yapılıyor...</p>
          </div>
          <AnalysisSkeleton />
        </div>
      )}

      {/* ATS Results */}
      {atsResult && (
        <div className="space-y-6">
          <ATSScoreCard
            score={atsResult.total_score}
            grade={atsResult.grade}
            summary={atsResult.summary}
          />
          <CriteriaBreakdown criteria={atsResult.criteria} />
        </div>
      )}

      {/* AI Feedback loading */}
      {analyzingAI && (
        <div className="space-y-4">
          <div className="flex items-center gap-3 rounded-lg border border-accent/20 bg-accent/5 px-4 py-3">
            <Loader2 className="h-5 w-5 animate-spin text-accent" />
            <p className="text-sm text-slate-300">AI optimizasyonu yapılıyor... Bu biraz zaman alabilir.</p>
          </div>
          <AIFeedbackSkeleton />
        </div>
      )}

      {/* AI Feedback results */}
      {optimization && (
        <SectionFeedbackList
          sections={optimization.ai_feedback.section_feedback}
          overallAssessment={optimization.ai_feedback.overall_assessment}
          actionItems={optimization.ai_feedback.action_items}
          atsTips={optimization.ai_feedback.ats_tips}
        />
      )}

      {/* Done state - optimize button */}
      {currentStep === "done" && optimization && cvId && (
        <Card className="border-accent/30 animate-fade-in-up">
          <CardContent className="flex flex-col items-center gap-4 py-8">
            <CheckCircle2 className="h-10 w-10 text-green-400" />
            <p className="text-sm text-slate-300">Analiz tamamlandı!</p>
            <div className="flex items-center gap-3">
              <Link href={`/optimize/${cvId}`}>
                <Button size="lg">
                  <Sparkles className="h-4 w-4" />
                  Optimize Et
                </Button>
              </Link>
              <Button
                variant="outline"
                onClick={() => {
                  setAtsResult(null);
                  setOptimization(null);
                  setCurrentStep("analyze");
                  setError(null);
                }}
              >
                Yeniden Analiz Et
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function AnalyzePage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-accent" />
        </div>
      }
    >
      <AnalyzePageContent />
    </Suspense>
  );
}
