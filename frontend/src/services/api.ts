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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

// Fallback Mock Data if backend is disconnected
export const fallbackFacts: Fact[] = [
  {
    id: "f1",
    subject: "Delhivery Limited",
    predicate: "revenue_from_operations",
    object: "₹81,415.38 million",
    normalized_value: 81415380000,
    currency: "INR",
    unit: "million",
    period_start: "2023-04-01",
    period_end: "2024-03-31",
    fiscal_period: "FY24",
    scope: "consolidated",
    confidence: 0.98,
    doc_id: "02-delhivery-annual-report-fy24-excerpt.pdf",
    page: 22,
    quote: "The revenue from operations on consolidated basis for FY24 stood at ₹ 81,415.38 million",
    is_verified: true
  },
  {
    id: "f2",
    subject: "Delhivery Limited",
    predicate: "revenue_from_operations",
    object: "₹8,142 Cr",
    normalized_value: 81420000000,
    currency: "INR",
    unit: "crore",
    period_start: "2023-04-01",
    period_end: "2024-03-31",
    fiscal_period: "FY24",
    scope: "consolidated",
    confidence: 0.97,
    doc_id: "03-delhivery-q4-fy24-earnings-presentation.pdf",
    page: 23,
    quote: "Total revenue from customers ... FY24: 8,142 Cr",
    is_verified: true
  },
  {
    id: "f3",
    subject: "Delhivery Limited",
    predicate: "revenue_from_operations",
    object: "₹38,382.91 million",
    normalized_value: 38382910000,
    currency: "INR",
    unit: "million",
    period_start: "2020-04-01",
    period_end: "2021-03-31",
    fiscal_period: "FY21",
    scope: "consolidated",
    confidence: 0.96,
    doc_id: "01-delhivery-prospectus-2022-excerpt.pdf",
    page: 56,
    quote: "Our total income increased from ₹16,948.74 million in Fiscal 2019 to ₹29,886.29 million in Fiscal 2020 and to ₹38,382.91 million in Fiscal 2021",
    is_verified: true
  }
]

export const fallbackReconciliations: Reconciliation[] = [
  {
    id: "r1",
    type: "corroboration",
    factA: fallbackFacts[0],
    factB: fallbackFacts[1],
    reasoning: "Corroboration confirmed: Both documents report consistent normalized figures (~₹8,141.54 Cr) for FY24 (consolidated), despite differing document formatting ('₹81,415.38 million' vs '₹8,142 Cr').",
    axis_of_difference: "none",
    confidence: 0.98
  },
  {
    id: "r2",
    type: "reconciled",
    factA: fallbackFacts[2],
    factB: fallbackFacts[0],
    reasoning: "Apparent contradiction reconciled by TEMPORAL CONTEXT: '01-delhivery-prospectus-2022-excerpt.pdf' reports for FY21 (₹38,382.91 million), whereas '02-delhivery-annual-report-fy24-excerpt.pdf' reports for FY24 (₹81,415.38 million).",
    axis_of_difference: "temporal_period",
    confidence: 0.96
  }
]

export const api = {
  getFacts: async (): Promise<Fact[]> => {
    try {
      const res = await fetch(`${API_BASE_URL}/facts`)
      if (!res.ok) throw new Error("Backend response not ok")
      const data = await res.json()
      return data.length > 0 ? data : fallbackFacts
    } catch {
      return fallbackFacts
    }
  },

  getReconciliations: async (type?: string): Promise<Reconciliation[]> => {
    try {
      const url = type && type !== "all" ? `${API_BASE_URL}/reconciliations?type=${type}` : `${API_BASE_URL}/reconciliations`
      const res = await fetch(url)
      if (!res.ok) throw new Error("Backend response not ok")
      const data = await res.json()
      return data.length > 0 ? data : fallbackReconciliations
    } catch {
      return fallbackReconciliations
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
  }
}
