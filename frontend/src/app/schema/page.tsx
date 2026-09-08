"use client"

import { useEffect, useState } from "react"
import { api, SchemaResponse } from "@/services/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Sparkles, Network, RefreshCw, Layers, CheckCircle2, Info } from "lucide-react"

export default function SchemaPage() {
  const [schema, setSchema] = useState<SchemaResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [inducing, setInducing] = useState(false)

  const loadSchema = () => {
    setLoading(true)
    api.getSchema().then(data => {
      setSchema(data)
      setLoading(false)
    })
  }

  useEffect(() => {
    loadSchema()
  }, [])

  const handleInduce = async () => {
    setInducing(true)
    try {
      const data = await api.induceSchema()
      setSchema(data)
    } finally {
      setInducing(false)
    }
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dynamic Schema Induction</h2>
          <p className="text-muted-foreground mt-2">
            Eliminates rigid predefined schemas. As new documents are ingested, open-schema predicates are automatically clustered into evolving canonical concepts.
          </p>
        </div>
        <Button onClick={handleInduce} disabled={inducing} className="gap-2 shadow-sm">
          <RefreshCw className={`w-4 h-4 ${inducing ? 'animate-spin' : ''}`} />
          {inducing ? "Clustering..." : "Run Schema Induction"}
        </Button>
      </div>

      {schema && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-5 border bg-muted/20">
            <p className="text-xs text-muted-foreground uppercase font-semibold">Open Predicates Discovered</p>
            <p className="text-3xl font-bold mt-2 text-primary">{schema.total_open_predicates}</p>
            <p className="text-xs text-muted-foreground mt-1">Discovered dynamically across filings</p>
          </Card>
          <Card className="p-5 border bg-muted/20">
            <p className="text-xs text-muted-foreground uppercase font-semibold">Canonical Concepts Induced</p>
            <p className="text-3xl font-bold mt-2 text-foreground">{schema.canonical_concepts.length}</p>
            <p className="text-xs text-muted-foreground mt-1">AutoSchemaKG-style clustering</p>
          </Card>
          <Card className="p-5 border bg-muted/20">
            <p className="text-xs text-muted-foreground uppercase font-semibold">Semantic Alignment Score</p>
            <p className="text-3xl font-bold mt-2 text-green-500">{schema.semantic_alignment_score}</p>
            <p className="text-xs text-muted-foreground mt-1">Ontological coherence metric</p>
          </Card>
        </div>
      )}

      {schema && (
        <div className="space-y-6">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Network className="w-5 h-5 text-primary" />
            Evolving Semantic Concept Clusters
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {schema.canonical_concepts.map((concept) => (
              <Card key={concept.concept} className="border shadow-sm overflow-hidden flex flex-col justify-between">
                <CardHeader className="bg-muted/30 border-b pb-4">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base font-semibold text-foreground">
                      {concept.concept.replace(/_/g, " ")}
                    </CardTitle>
                    <Badge variant="outline" className="bg-background text-xs">
                      {concept.predicates_count} Predicates
                    </Badge>
                  </div>
                  <CardDescription className="text-xs mt-1">
                    {concept.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-5 space-y-3">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Associated Predicates & Assertions:
                  </span>
                  <div className="space-y-2">
                    {concept.predicates.map((p) => (
                      <div
                        key={p.predicate}
                        className="p-2.5 rounded-md border bg-muted/10 text-xs flex items-center justify-between"
                      >
                        <div>
                          <p className="font-mono font-semibold text-foreground">{p.predicate}</p>
                          {p.sample_object && (
                            <p className="text-[11px] text-muted-foreground mt-0.5">
                              Sample: <span className="italic font-medium">{p.sample_object}</span>
                            </p>
                          )}
                        </div>
                        <Badge variant="secondary" className="text-[10px]">
                          {p.occurrences} facts
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
