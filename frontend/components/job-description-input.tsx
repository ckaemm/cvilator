"use client";

import { useState } from "react";
import { FileSearch, Briefcase } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

interface JobDescriptionInputProps {
  onAnalyze: (jobDescription: string) => void;
  loading: boolean;
  disabled: boolean;
}

export function JobDescriptionInput({ onAnalyze, loading, disabled }: JobDescriptionInputProps) {
  const [text, setText] = useState("");
  const charCount = text.length;
  const hasMinLength = text.trim().length >= 10;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Briefcase className="h-5 w-5 text-accent" />
          <CardTitle>İş İlanı</CardTitle>
        </div>
        <CardDescription>
          İş ilanını yapıştırarak ilana özel analiz alabilirsiniz. Boş bırakırsanız genel analiz yapılır.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="relative">
          <Textarea
            placeholder="İş ilanı metnini buraya yapıştırın..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={6}
            disabled={loading || disabled}
          />
          <span className={`absolute bottom-2 right-3 text-xs ${
            charCount > 0 && !hasMinLength ? "text-amber-400" : "text-slate-600"
          }`}>
            {charCount > 0 && `${charCount} karakter`}
            {charCount > 0 && !hasMinLength && " (min. 10)"}
          </span>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Button
            onClick={() => onAnalyze(text)}
            loading={loading}
            disabled={disabled || loading}
          >
            <FileSearch className="h-4 w-4" />
            {text.trim().length >= 10 ? "İlanla Analiz Et" : "Genel Analiz Yap"}
          </Button>
          {text.length > 0 && (
            <Button
              variant="ghost"
              onClick={() => setText("")}
              disabled={loading}
            >
              Temizle
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
