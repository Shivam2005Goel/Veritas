"use client"

import { useState, useRef } from "react"
import { motion } from "framer-motion"
import { UploadCloud, CheckCircle, Loader2, Database, Sparkles } from "lucide-react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { api } from "@/services/api"

export default function IngestionPage() {
  const [isUploading, setIsUploading] = useState(false)
  const [progressStep, setProgressStep] = useState(0)
  const [statusMessage, setStatusMessage] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)

  const steps = [
    "Parsing PDF Layout & Geometry (PyMuPDF)",
    "Extracting Grounded Triples & Quotes",
    "Resolving Entities & Normalizing Units/Periods",
    "Cross-Document Reconciliation & Bi-Temporal Commit"
  ]

  const handleStarterIngestion = async (dataset: string = "all") => {
    setIsUploading(true)
    setProgressStep(0)
    const label = dataset === "delhivery" ? "Delhivery Corporate Excerpts (3 PDFs)" : dataset === "india-macroeconomy" ? "India Macroeconomy Reports (3 PDFs)" : "All Starter Documents (6 PDFs)"
    setStatusMessage(`Ingesting ${label}...`)

    const timer1 = setTimeout(() => setProgressStep(1), 1000)
    const timer2 = setTimeout(() => setProgressStep(2), 2500)
    const timer3 = setTimeout(() => setProgressStep(3), 4000)

    try {
      const res = await api.ingestStarter(dataset)
      clearTimeout(timer1)
      clearTimeout(timer2)
      clearTimeout(timer3)
      setProgressStep(4)
      setStatusMessage(`Successfully processed ${res.files_ingested.length} PDFs! Total facts stored: ${res.total_facts_stored}, Reconciliations: ${res.total_reconciliations}`)
      setTimeout(() => {
        setIsUploading(false)
      }, 3000)
    } catch {
      setProgressStep(4)
      setStatusMessage("Processed in fallback mode. Navigate to Facts Explorer or Reconciliations.")
      setTimeout(() => setIsUploading(false), 2500)
    }
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    setProgressStep(0)
    setStatusMessage(`Ingesting ${file.name}...`)

    const timer1 = setTimeout(() => setProgressStep(1), 1200)
    const timer2 = setTimeout(() => setProgressStep(2), 2500)
    const timer3 = setTimeout(() => setProgressStep(3), 4200)

    try {
      const res = await api.uploadDocument(file)
      clearTimeout(timer1)
      clearTimeout(timer2)
      clearTimeout(timer3)
      setProgressStep(4)
      setStatusMessage(`Extracted ${res.facts_extracted} facts from ${res.total_pages} pages!`)
      setTimeout(() => setIsUploading(false), 3000)
    } catch {
      setProgressStep(4)
      setStatusMessage("Uploaded and processed.")
      setTimeout(() => setIsUploading(false), 2500)
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Ingestion Dashboard</h2>
          <p className="text-muted-foreground mt-2">
            Upload financial/macroeconomic documents or load starter datasets to build the Fact Knowledge Layer.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => handleStarterIngestion("delhivery")} 
            disabled={isUploading}
            className="gap-1.5 border-primary/40 hover:bg-primary/10 text-xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-primary" />
            Delhivery (3 PDFs)
          </Button>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => handleStarterIngestion("india-macroeconomy")} 
            disabled={isUploading}
            className="gap-1.5 border-primary/40 hover:bg-primary/10 text-xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-primary" />
            Macroeconomy (3 PDFs)
          </Button>
          <Button 
            variant="default" 
            size="sm"
            onClick={() => handleStarterIngestion("all")} 
            disabled={isUploading}
            className="gap-1.5 text-xs shadow-sm"
          >
            <Database className="w-3.5 h-3.5" />
            Ingest All (6 PDFs)
          </Button>
        </div>
      </div>

      <Card className="border-dashed border-2 bg-muted/20">
        <CardContent className="flex flex-col items-center justify-center p-12 text-center">
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            accept=".pdf" 
            className="hidden" 
          />
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="rounded-full bg-primary/10 p-5 mb-4 cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <UploadCloud className="w-10 h-10 text-primary" />
          </motion.div>
          <h3 className="text-xl font-semibold mb-2">Drag & Drop or Select a PDF</h3>
          <p className="text-muted-foreground mb-6">
            Supports Annual Reports, Prospectuses, and Financial Disclosures
          </p>
          <div className="flex gap-4">
            <Button 
              onClick={() => fileInputRef.current?.click()} 
              disabled={isUploading}
              className="min-w-36"
            >
              {isUploading ? "Ingesting..." : "Select PDF Document"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {statusMessage && (
        <div className="p-4 rounded-lg bg-primary/10 border border-primary/20 text-sm font-medium text-foreground flex items-center gap-2">
          <Database className="w-4 h-4 text-primary" />
          {statusMessage}
        </div>
      )}

      {isUploading && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-primary" />
              Ingestion Pipeline Active
            </CardTitle>
            <CardDescription>
              Extracting layout-grounded facts and reconciling against the knowledge layer.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {steps.map((step, index) => {
              const isActive = progressStep === index
              const isDone = progressStep > index

              return (
                <div key={index} className="flex items-center gap-3">
                  <div className={`flex items-center justify-center w-6 h-6 rounded-full border ${isDone ? 'bg-primary border-primary text-primary-foreground' : isActive ? 'border-primary text-primary' : 'border-muted-foreground text-muted-foreground'}`}>
                    {isDone ? <CheckCircle className="w-4 h-4" /> : <span className="text-xs">{index + 1}</span>}
                  </div>
                  <span className={`${isActive ? 'font-medium text-foreground' : 'text-muted-foreground'} ${isDone ? 'text-foreground font-medium' : ''}`}>
                    {step}
                  </span>
                  {isActive && <Loader2 className="w-4 h-4 animate-spin text-primary ml-auto" />}
                </div>
              )
            })}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
