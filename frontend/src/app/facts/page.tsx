"use client"

import { useEffect, useState } from "react"
import { api, Fact } from "@/services/api"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { FileText, Loader2, CheckCircle2, AlertTriangle, Eye, History, Layers } from "lucide-react"

export default function FactsPage() {
  const [facts, setFacts] = useState<Fact[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedFact, setSelectedFact] = useState<Fact | null>(null)
  const [showSuperseded, setShowSuperseded] = useState(false)

  useEffect(() => {
    api.getFacts().then(data => {
      setFacts(data)
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

  const displayedFacts = showSuperseded ? facts : facts.filter(f => !f.is_superseded)

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Facts Explorer</h2>
          <p className="text-muted-foreground mt-2">
            Browse grounded fact triples extracted across documents with verifiable bounding-box coordinates.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant={showSuperseded ? "secondary" : "outline"}
            size="sm"
            onClick={() => setShowSuperseded(!showSuperseded)}
            className="gap-2 text-xs"
          >
            <History className="w-3.5 h-3.5" />
            {showSuperseded ? "Showing Bi-Temporal History" : "Show Superseded Facts"}
          </Button>
          <Badge variant="outline" className="px-3 py-1 font-mono text-xs">
            {displayedFacts.length} Facts Loaded
          </Badge>
        </div>
      </div>

      <div className="rounded-md border bg-card shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/30">
              <TableHead className="font-semibold">Subject / Entity</TableHead>
              <TableHead className="font-semibold">Predicate</TableHead>
              <TableHead className="font-semibold">Object / Assertion</TableHead>
              <TableHead className="font-semibold">Temporal & Scope</TableHead>
              <TableHead className="font-semibold">Confidence</TableHead>
              <TableHead className="font-semibold text-right">Evidence</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {displayedFacts.map((fact) => (
              <TableRow key={fact.id} className={fact.is_superseded ? "opacity-60 bg-muted/20" : ""}>
                <TableCell className="font-medium">
                  <div className="flex items-center gap-2">
                    <span>{fact.subject}</span>
                    {fact.is_superseded && (
                      <Badge variant="destructive" className="text-[10px] py-0 px-1.5">
                        Superseded
                      </Badge>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="font-mono text-xs bg-muted/40">
                    {fact.predicate}
                  </Badge>
                </TableCell>
                <TableCell className="font-semibold text-foreground">
                  {fact.object}
                </TableCell>
                <TableCell className="text-muted-foreground text-xs">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {fact.fiscal_period && (
                      <Badge variant="secondary" className="text-[11px]">
                        {fact.fiscal_period}
                      </Badge>
                    )}
                    {fact.scope && (
                      <span className="text-[11px] text-muted-foreground capitalize">
                        ({fact.scope})
                      </span>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${fact.confidence >= 0.9 ? 'bg-primary' : fact.confidence >= 0.7 ? 'bg-amber-500' : 'bg-destructive'}`} 
                        style={{ width: `${fact.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono">{Math.round(fact.confidence * 100)}%</span>
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <Dialog>
                    <DialogTrigger 
                      render={<Button variant="ghost" size="sm" onClick={() => setSelectedFact(fact)} />}
                    >
                      <Eye className="w-4 h-4 mr-1.5 text-primary" />
                      View
                    </DialogTrigger>
                    <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
                      <DialogHeader>
                        <DialogTitle className="flex items-center gap-2 text-lg">
                          <Layers className="w-5 h-5 text-primary" />
                          Source Evidence & Visual Verification
                        </DialogTitle>
                        <DialogDescription>
                          Inspect the verbatim text quote and the actual illuminated bounding box on the original PDF page.
                        </DialogDescription>
                      </DialogHeader>
                      
                      <div className="flex-1 overflow-y-auto space-y-4 pt-2">
                        <div className="grid grid-cols-3 gap-3 text-xs bg-muted/30 p-3 rounded-lg border">
                          <div>
                            <p className="text-muted-foreground">Document Provenance</p>
                            <p className="font-medium text-foreground truncate mt-0.5" title={fact.doc_id}>
                              {fact.doc_id}
                            </p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Page Number</p>
                            <p className="font-medium text-foreground mt-0.5">Page {fact.page}</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Quote Grounding Status</p>
                            <div className="flex items-center gap-1.5 mt-0.5">
                              {fact.is_verified ? (
                                <>
                                  <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                                  <span className="font-medium text-green-500">Verified on Page</span>
                                </>
                              ) : (
                                <>
                                  <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                                  <span className="font-medium text-amber-500">Unverified / Caveat</span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>

                        <Tabs defaultValue="visual" className="w-full">
                          <TabsList className="grid grid-cols-2 w-full">
                            <TabsTrigger value="visual">Illuminated Page Preview</TabsTrigger>
                            <TabsTrigger value="quote">Verbatim Quote Snippet</TabsTrigger>
                          </TabsList>
                          
                          <TabsContent value="visual" className="pt-2">
                            <div className="rounded-lg border bg-muted/20 p-2 flex flex-col items-center justify-center">
                              <div className="w-full flex justify-between items-center text-xs text-muted-foreground mb-2 px-1">
                                <span>High-Resolution Rendering with Bounding Box Overlay</span>
                                {fact.bbox && <span>Coordinates: [{fact.bbox.join(", ")}]</span>}
                              </div>
                              <div className="max-h-[380px] overflow-auto border rounded bg-background shadow-inner w-full flex justify-center">
                                <img
                                  src={api.getPagePreviewUrl(fact.doc_id, fact.page, fact.bbox)}
                                  alt={`Document Preview Page ${fact.page}`}
                                  className="w-auto h-auto max-w-full object-contain"
                                  loading="lazy"
                                />
                              </div>
                            </div>
                          </TabsContent>

                          <TabsContent value="quote" className="pt-2 space-y-3">
                            <ScrollArea className="h-[180px] w-full rounded-md border p-4 bg-muted/20">
                              <p className="text-sm italic leading-relaxed text-foreground">
                                &quot;{fact.quote}&quot;
                              </p>
                            </ScrollArea>
                            {fact.is_superseded && (
                              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md text-xs text-destructive">
                                <strong>Bi-Temporal Note:</strong> This assertion was later contradicted or superseded by subsequent filings. Its validity period was automatically closed.
                              </div>
                            )}
                          </TabsContent>
                        </Tabs>
                      </div>
                    </DialogContent>
                  </Dialog>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
