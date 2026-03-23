import type {
  CVUploadResponse,
  CVListItem,
  CVDetail,
  ATSScoreResponse,
} from "./types";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail || `İstek başarısız: ${res.status}`;
    throw new ApiError(message, res.status);
  }
  return res.json();
}

export async function uploadCV(file: File): Promise<CVUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return request<CVUploadResponse>("/api/cv/upload", {
    method: "POST",
    body: formData,
  });
}

export async function listCVs(): Promise<CVListItem[]> {
  return request<CVListItem[]>("/api/cv/list");
}

export async function getCVDetail(id: number): Promise<CVDetail> {
  return request<CVDetail>(`/api/cv/${id}`);
}

export async function analyzeCV(id: number): Promise<ATSScoreResponse> {
  return request<ATSScoreResponse>(`/api/analyze/${id}`, {
    method: "POST",
  });
}

export async function analyzeCVWithJob(
  id: number,
  jobDescription: string
): Promise<ATSScoreResponse> {
  return request<ATSScoreResponse>(`/api/analyze/${id}/with-job`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_description: jobDescription }),
  });
}
