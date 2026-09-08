"use client"

import { useState } from "react"
import { api, QAResponse } from "@/services/api"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Search, Sparkles, Loader2, CheckCircle2, AlertCircle, FileText, ArrowRight } from "lucide-react"

export default function SearchQAPage() {
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<QAResponse | null>(null)

  const sampleQueries = [
    "What was Delhivery's FY24 revenue and are there any conflicting statements?",
    "What is India's GDP growth rate according to macroeconomic reports?",
    "What is the headline CPI inflation rate for FY25?",
    "How many pin codes does Delhivery service?",
    "What was Delhivery's revenue in the 2022 Prospectus vs 2024 Annual Report?"
  ]

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return
    setQuery(searchQuery)
    setLoading(true)
    try {
      const data = await api.queryKnowledgeLayer(searchQuery)
      setResult(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Fact Search & Synthesis</h2>
        <p className="text-muted-foreground mt-2">
          Ask questions across all ingested filings. The knowledge layer synthesizes answers directly from verified fact triples and cross-document reconciliations.
        </p>
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-3.5 w-4 h-4 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch(query)}
            placeholder="Ask anything (e.g. Delhivery FY24 revenue, conflicts, GDP growth)..."
            className="pl-10 h-11 text-sm bg-card"
          />
        </div>
        <Button onClick={() => handleSearch(query)} disabled={loading} className="min-w-28 h-11 gap-2">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          {loading ? "Searching..." : "Search"}
        </Button>
      </div>

      <div className="flex flex-wrap gap-2 items-center">
        <span className="text-xs text-muted-foreground font-medium flex items-center gap-1">
          <Sparkles className="w-3.5 h-3.5 text-primary" /> Suggested Inquiries:
        </span>
        {sampleQueries.map((sq, i) => (
          <Button
            key={i}
            variant="outline"
            size="sm"
            onClick={() => handleSearch(sq)}
            className="text-xs h-7 hover:bg-primary/10 border-muted-foreground/30"
          >
            {sq}
          </Button>
        ))}
      </div>

      {result && (
        <div className="space-y-6 animate-in fade-in-50 duration-300">
          <Card className="border-primary/30 shadow-sm bg-card">
            <CardHeader className="bg-primary/5 border-b pb-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-primary" />
                  Grounded Knowledge Synthesis
                </CardTitle>
                <Badge variant="outline" className="bg-background font-mono text-xs">
                  Confidence: {Math.round(result.confidence * 100)}%
                </Badge>
              </div>
              <CardDescription className="text-xs mt-1">
                Synthesized directly from verified assertions across source documents.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <p className="text-base leading-relaxed text-foreground font-normal">
                {result.answer}
              </p>

              {result.reconciliations.length > 0 && (
                <div className="mt-4 pt-4 border-t space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Cross-Document Reconciliation Insights
                  </h4>
                  <div className="space-y-2">
                    {result.reconciliations.map((rec) => (
                      <div
                        key={rec.id}
                        className={`p-3 rounded-lg border text-xs leading-relaxed flex items-start gap-2.5 ${
                          rec.type === 'corroboration'
                            ? 'bg-green-500/10 border-green-500/20 text-green-700 dark:text-green-300'
                            : rec.type === 'contradiction'
                            ? 'bg-red-500/10 border-red-500/20 text-red-700 dark:text-red-300'
                            : 'bg-blue-500/10 border-blue-500/20 text-blue-700 dark:text-blue-300'
                        }`}
                      >
                        <Badge variant="outline" className="uppercase text-[10px] py-0 px-1 bg-background shrink-0 mt-0.5">
                          {rec.type}
                        </Badge>
                        <div>
                          <p className="font-medium">{rec.reasoning}</p>
                          <p className="text-[11px] opacity-75 mt-1 font-mono">
                            Between: {rec.doc_a} ↔ {rec.doc_b}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Cited Evidence Triples ({result.cited_facts.length})
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.cited_facts.map((fact) => (
                <Card key={fact.id} className="p-4 space-y-2 bg-muted/20 border">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-foreground">{fact.subject}</span>
                    <Badge variant="secondary" className="text-[10px]">
                      Page {fact.page}
                    </Badge>
                  </div>
                  <div className="text-sm font-medium">
                    <span className="text-muted-foreground">{fact.predicate}: </span>
                    <span className="font-bold text-primary">{fact.object}</span>
                  </div>
                  <p className="text-xs italic text-muted-foreground line-clamp-2 border-l-2 pl-2 border-primary/40">
                    &quot;{fact.quote}&quot;
                  </p>
                  <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1">
                    <span className="font-mono truncate max-w-[200px]">{fact.doc_id}</span>
                    {fact.fiscal_period && <Badge variant="outline" className="text-[10px]">{fact.fiscal_period}</Badge>}
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
