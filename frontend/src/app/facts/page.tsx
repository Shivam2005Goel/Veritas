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
import { FileText, Loader2 } from "lucide-react"

export default function FactsPage() {
  const [facts, setFacts] = useState<Fact[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getFacts().then(data => {
      setFacts(data)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Facts Explorer</h2>
        <p className="text-muted-foreground mt-2">
          Browse grounded fact triples extracted from all ingested documents.
        </p>
      </div>

      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Subject</TableHead>
              <TableHead>Predicate</TableHead>
              <TableHead>Object/Value</TableHead>
              <TableHead>Context (Period/Scope)</TableHead>
              <TableHead>Confidence</TableHead>
              <TableHead className="text-right">Evidence</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {facts.map((fact) => (
              <TableRow key={fact.id}>
                <TableCell className="font-medium">{fact.subject}</TableCell>
                <TableCell>
                  <Badge variant="outline" className="font-mono bg-muted/50">{fact.predicate}</Badge>
                </TableCell>
                <TableCell>{fact.object}</TableCell>
                <TableCell className="text-muted-foreground text-sm">
                  {fact.period_start && fact.period_end ? `FY24` /* hardcoded for mock brevity */ : ''} 
                  {fact.scope && ` (${fact.scope})`}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-primary" 
                        style={{ width: `${fact.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-xs">{Math.round(fact.confidence * 100)}%</span>
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <Dialog>
                    <DialogTrigger render={<Button variant="ghost" size="sm" />}>
                      <FileText className="w-4 h-4 mr-2" />
                      View
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl">
                      <DialogHeader>
                        <DialogTitle>Fact Evidence</DialogTitle>
                        <DialogDescription>
                          Source verification and verbatim extraction quote.
                        </DialogDescription>
                      </DialogHeader>
                      
                      <div className="space-y-4 pt-4">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="text-muted-foreground">Document</p>
                            <p className="font-medium">{fact.doc_id}</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Page</p>
                            <p className="font-medium">{fact.page}</p>
                          </div>
                        </div>
                        
                        <div>
                          <p className="text-muted-foreground text-sm mb-2">Verbatim Quote</p>
                          <ScrollArea className="h-[100px] w-full rounded-md border p-4 bg-muted/50">
                            <p className="text-sm italic">&quot;{fact.quote}&quot;</p>
                          </ScrollArea>
                        </div>
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
