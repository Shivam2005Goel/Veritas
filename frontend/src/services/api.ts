export interface Fact {
  id: string
  subject: string
  predicate: string
  object: string
  value?: string
  normalized_value?: number
  unit?: string
  currency?: string
  period_start?: string
  period_end?: string
  fiscal_period?: string
  scope?: string
  confidence: number
  doc_id: string
  page: number
  quote: string
  bbox?: number[]
  is_verified?: boolean
  fact_type?: string
  is_superseded?: boolean
  valid_from?: string
  valid_to?: string
}

export interface Reconciliation {
  id: string
  type: 'corroboration' | 'contradiction' | 'reconciled' | 'failure'
  factA: Fact
  factB: Fact
  reasoning: string
  axis_of_difference?: string
  confidence?: number
}

export interface SchemaConcept {
  concept: string
  description: string
  predicates_count: number
  total_assertions: number
  predicates: Array<{
    predicate: string
    occurrences: number
    sample_object?: string
    sample_unit?: string
  }>
}

export interface SchemaResponse {
  status: string
  total_open_predicates: number
  canonical_concepts: SchemaConcept[]
  unclustered_predicates: string[]
  semantic_alignment_score: string
}

export interface QAResponse {
  query: string
  answer: string
  confidence: number
  cited_facts: Array<{
    id: string
    subject: string
    predicate: string
    object: string
    doc_id: string
    page: number
    quote: string
    fiscal_period?: string
    scope?: string
    is_verified?: boolean
  }>
  reconciliations: Array<{
    id: string
    type: string
    reasoning: string
    doc_a: string
    doc_b: string
  }>
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

export const api = {
  getFacts: async (): Promise<Fact[]> => {
    try {
      const res = await fetch(`${API_BASE_URL}/facts`)
      if (!res.ok) throw new Error("Backend response not ok")
      return await res.json()
    } catch {
      return []
    }
  },

  getReconciliations: async (type?: string): Promise<Reconciliation[]> => {
    try {
      const url = type && type !== "all" ? `${API_BASE_URL}/reconciliations?type=${type}` : `${API_BASE_URL}/reconciliations`
      const res = await fetch(url)
      if (!res.ok) throw new Error("Backend response not ok")
      return await res.json()
    } catch {
      return []
    }
  },

  ingestStarter: async (dataset: string = "all") => {
    const res = await fetch(`${API_BASE_URL}/ingest-starter?dataset=${dataset}`, {
      method: "POST"
    })
    if (!res.ok) throw new Error("Failed to trigger starter ingestion")
    return await res.json()
  },

  uploadDocument: async (file: File) => {
    const formData = new FormData()
    formData.append("file", file)
    const res = await fetch(`${API_BASE_URL}/documents`, {
      method: "POST",
      body: formData
    })
    if (!res.ok) throw new Error("Failed to upload document")
    return await res.json()
  },

  getPagePreviewUrl: (docId: string, pageNum: number, bbox?: number[]): string => {
    const bboxParam = bbox && bbox.length === 4 ? `?bbox=${bbox.join(",")}` : ""
    return `${API_BASE_URL}/documents/${encodeURIComponent(docId)}/pages/${pageNum}/preview${bboxParam}`
  },

  getSchema: async (): Promise<SchemaResponse> => {
    const res = await fetch(`${API_BASE_URL}/schema`)
    if (!res.ok) throw new Error("Failed to fetch schema")
    return await res.json()
  },

  induceSchema: async (): Promise<SchemaResponse> => {
    const res = await fetch(`${API_BASE_URL}/schema/induce`, { method: "POST" })
    if (!res.ok) throw new Error("Failed to induce schema")
    return await res.json()
  },

  queryKnowledgeLayer: async (query: string): Promise<QAResponse> => {
    const res = await fetch(`${API_BASE_URL}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    })
    if (!res.ok) throw new Error("Failed to query knowledge layer")
    return await res.json()
  },

  getSettings: async () => {
    const res = await fetch(`${API_BASE_URL}/settings`)
    if (!res.ok) throw new Error("Failed to fetch settings")
    return await res.json()
  },

  updateApiKey: async (apiKey: string, provider: string = "gemini") => {
    const res = await fetch(`${API_BASE_URL}/settings/api-key`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: apiKey, provider })
    })
    if (!res.ok) throw new Error("Failed to update API key")
    return await res.json()
  },

  resetKnowledgeBase: async () => {
    const res = await fetch(`${API_BASE_URL}/reset`, { method: "POST" })
    if (!res.ok) throw new Error("Failed to reset knowledge base")
    return await res.json()
  }
}
