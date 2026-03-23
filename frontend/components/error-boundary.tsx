"use client";

import { Component, type ReactNode } from "react";
import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <Card className="border-danger/30">
          <CardContent className="flex flex-col items-center gap-4 py-10">
            <AlertCircle className="h-10 w-10 text-red-400" />
            <div className="text-center">
              <h3 className="text-base font-semibold text-text-primary">Bir hata oluştu</h3>
              <p className="mt-1 text-sm text-slate-400">
                {this.state.error?.message || "Beklenmeyen bir hata meydana geldi."}
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              <RefreshCw className="h-4 w-4" />
              Tekrar Dene
            </Button>
          </CardContent>
        </Card>
      );
    }

    return this.props.children;
  }
}
