"use client"

import { useEffect, useState } from "react"
import { api, Reconciliation } from "@/services/api"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { AlertCircle, CheckCircle2, Loader2, Repeat2, AlertTriangle } from "lucide-react"

export default function ReconciliationsPage() {
  const [reconciliations, setReconciliations] = useState<Reconciliation[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getReconciliations().then(data => {
      setReconciliations(data)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center p-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'corroboration': return <CheckCircle2 className="w-5 h-5 text-green-500" />
      case 'contradiction': return <AlertCircle className="w-5 h-5 text-red-500" />
      case 'reconciled': return <Repeat2 className="w-5 h-5 text-blue-500" />
      case 'failure': return <AlertTriangle className="w-5 h-5 text-amber-500" />
      default: return null
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'corroboration': return "bg-green-500/10 text-green-500 border-green-500/20"
      case 'contradiction': return "bg-red-500/10 text-red-500 border-red-500/20"
      case 'reconciled': return "bg-blue-500/10 text-blue-500 border-blue-500/20"
      case 'failure': return "bg-amber-500/10 text-amber-500 border-amber-500/20"
      default: return ""
    }
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'corroboration': return "Case 1: Corroboration"
      case 'contradiction': return "Case 2: Contradiction"
      case 'reconciled': return "Case 3: Reconciled by Context"
      case 'failure': return "Case 4: Failure & Ambiguity Analysis"
      default: return type
    }
  }

  const renderCase = (rec: Reconciliation) => (
    <Card key={rec.id} className="overflow-hidden border shadow-sm">
      <CardHeader className={`${getTypeColor(rec.type)} border-b py-3 px-6`}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle className="flex items-center gap-2 text-base font-semibold">
            {getTypeIcon(rec.type)}
            <span>{getTypeLabel(rec.type)}</span>
          </CardTitle>
          <div className="flex items-center gap-2">
            {rec.axis_of_difference && (
              <Badge variant="outline" className="bg-background text-xs">
                Axis: {rec.axis_of_difference}
              </Badge>
            )}
            <Badge variant="outline" className="bg-background text-xs font-mono">
              {rec.factA.predicate}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x">
          <div className="p-6 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Source Document A</span>
              <Badge variant="secondary" className="text-xs">Page {rec.factA.page}</Badge>
            </div>
            <div>
              <p className="font-semibold text-lg text-foreground">{rec.factA.object}</p>
              <p className="text-xs text-muted-foreground font-mono mt-0.5 truncate">{rec.factA.doc_id}</p>
            </div>
            <div className="space-y-1">
              <span className="text-xs text-muted-foreground font-medium">Verbatim Source Quote:</span>
              <ScrollArea className="h-24 w-full rounded-md border p-3 bg-muted/20 text-xs">
                <p className="italic leading-relaxed">&quot;{rec.factA.quote}&quot;</p>
              </ScrollArea>
            </div>
          </div>

          <div className="p-6 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Source Document B</span>
              <Badge variant="secondary" className="text-xs">Page {rec.factB.page}</Badge>
            </div>
            <div>
              <p className="font-semibold text-lg text-foreground">{rec.factB.object}</p>
              <p className="text-xs text-muted-foreground font-mono mt-0.5 truncate">{rec.factB.doc_id}</p>
            </div>
            <div className="space-y-1">
              <span className="text-xs text-muted-foreground font-medium">Verbatim Source Quote:</span>
              <ScrollArea className="h-24 w-full rounded-md border p-3 bg-muted/20 text-xs">
                <p className="italic leading-relaxed">&quot;{rec.factB.quote}&quot;</p>
              </ScrollArea>
            </div>
          </div>
        </div>
        <Separator />
        <div className="p-6 bg-muted/10 space-y-2">
          <h4 className="font-semibold text-xs text-muted-foreground uppercase tracking-wider">
            Automated Reconciliation Reasoning & Evidence
          </h4>
          <p className="text-sm leading-relaxed text-foreground">{rec.reasoning}</p>
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Reconciliations Dashboard</h2>
        <p className="text-muted-foreground mt-2">
          Cross-document verification layer classifying relationships into Corroborations, Contradictions, Reconciled Context, and Failure analysis.
        </p>
      </div>

      <Tabs defaultValue="all" className="w-full">
        <TabsList className="mb-6 grid grid-cols-2 md:grid-cols-5 w-full">
          <TabsTrigger value="all">All Cases ({reconciliations.length})</TabsTrigger>
          <TabsTrigger value="corroboration">
            Corroboration ({reconciliations.filter(r => r.type === 'corroboration').length})
          </TabsTrigger>
          <TabsTrigger value="reconciled">
            Reconciled ({reconciliations.filter(r => r.type === 'reconciled').length})
          </TabsTrigger>
          <TabsTrigger value="contradiction">
            Contradiction ({reconciliations.filter(r => r.type === 'contradiction').length})
          </TabsTrigger>
          <TabsTrigger value="failure">
            Case 4 Failure ({reconciliations.filter(r => r.type === 'failure').length})
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="all" className="space-y-6">
          {reconciliations.map(renderCase)}
        </TabsContent>
        <TabsContent value="corroboration" className="space-y-6">
          {reconciliations.filter(r => r.type === 'corroboration').map(renderCase)}
        </TabsContent>
        <TabsContent value="reconciled" className="space-y-6">
          {reconciliations.filter(r => r.type === 'reconciled').map(renderCase)}
        </TabsContent>
        <TabsContent value="contradiction" className="space-y-6">
          {reconciliations.filter(r => r.type === 'contradiction').map(renderCase)}
        </TabsContent>
        <TabsContent value="failure" className="space-y-6">
          {reconciliations.filter(r => r.type === 'failure').map(renderCase)}
        </TabsContent>
      </Tabs>
    </div>
  )
}
