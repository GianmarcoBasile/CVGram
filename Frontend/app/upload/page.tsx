"use client"


import { Skeleton } from "@/components/ui/skeleton"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft, Loader2, Upload } from "lucide-react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { getCurrentUser, fetchUserAttributes } from 'aws-amplify/auth'
import { uploadData } from 'aws-amplify/storage'
import { configureAmplify } from "@/lib/amplify-config"

// Configurazione di Amplify
configureAmplify();

export default function UploadPage() {
  const [user, setUser] = useState<any>(null)
  const [email, setEmail] = useState<string>("")
  const [isLoading, setIsLoading] = useState(true)
  const [file, setFile] = useState<File | null>(null)
  const [fileName, setFileName] = useState<string>("")
  const [uploadStatus, setUploadStatus] = useState<string>("")
  const [isUploading, setIsUploading] = useState(false)
  const router = useRouter()

  useEffect(() => {
    const checkAuth = async () => {
      try {
        setIsLoading(true)
        const userData = await getCurrentUser()
        setUser(userData.userId)

        // Recupera gli attributi dell'utente, inclusa l'email
        const attributes = await fetchUserAttributes()
        if (attributes.email) {
          setEmail(attributes.email)
        }
      } catch (error) {
        // L'utente non è autenticato, redirect alla pagina di login
        console.log("Errore di autenticazione:", error);
        router.push("/")
      } finally {
        setIsLoading(false)
      }
    }
    checkAuth()
  }, [router])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]

      // Verifica che il file sia un PDF
      if (selectedFile.type !== 'application/pdf') {
        alert('Per favore, carica solo file in formato PDF')
        return
      }

      // Verifica che la dimensione del file sia minore di 5MB
      if (selectedFile.size > 5 * 1024 * 1024) {
        alert('Il file è troppo grande. La dimensione massima è 5MB')
        return
      }

      setFile(selectedFile)
      setFileName(selectedFile.name)
    }
  }
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!file) {
      alert('Per favore, seleziona un file PDF da caricare')
      return
    }

    setIsUploading(true)
    setUploadStatus('Caricamento in corso...')

    try {
      const timestamp = Date.now()
      const fileKey = `cvs/${user}/${timestamp}-${fileName}`

      const uploadResult = await uploadData({
        key: fileKey,
        data: file,
        options: {
          contentType: 'application/pdf',
          metadata: {
            email: email,
            originalName: fileName,
            uploadDate: new Date().toISOString()
          }
        }
      }).result

      console.log('File caricato con successo su S3:', uploadResult)

      setUploadStatus('CV caricato con successo! Il sistema sta elaborando il documento...')
      setTimeout(() => {
        setFile(null)
        setFileName("")
        setUploadStatus("Caricamento completato! Puoi caricare un altro CV o tornare alla dashboard.")
        setIsUploading(false)

        // router.push('/dashboard')
      }, 2000)

    } catch (error) {
      console.error('Errore durante il caricamento:', error)
      setUploadStatus('Errore durante il caricamento. Riprova più tardi.')
      setIsUploading(false)
    }
  }

  if (isLoading) return (
    <div className="min-h-screen flex items-center justify-center">
      <Loader2 className="w-12 h-12 text-gray-400 animate-spin" />
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center py-6">
            <Link href="/dashboard">
              <Button variant="ghost" className="mr-4">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Torna alla Dashboard
              </Button>
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">Carica CV</h1>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Upload className="w-6 h-6 mr-2" />
              Carica il tuo Curriculum Vitae
            </CardTitle>
            <CardDescription>
              Carica il tuo CV in formato PDF. Il sistema analizzerà automaticamente il documento
              per estrarre le informazioni rilevanti e le parole chiave.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-4">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
                  <Upload className="w-12 h-12 mx-auto text-gray-400 mb-2" />
                  <p className="text-lg font-medium text-gray-700 mb-1">
                    {fileName ? fileName : "Trascina qui il tuo CV o clicca per selezionarlo"}
                  </p>
                  <p className="text-sm text-gray-500 mb-4">
                    Supporta solo file PDF (max 5MB)
                  </p>
                  <Input
                    id="cv-upload"
                    type="file"
                    accept=".pdf"
                    className="hidden"
                    onChange={handleInputChange}
                  />
                  <Label
                    htmlFor="cv-upload"
                    className="px-4 py-2 rounded-md bg-blue-500 text-white cursor-pointer hover:bg-blue-600 inline-block"
                  >
                    Seleziona File
                  </Label>
                </div>

                {file && (
                  <div className="mt-4 bg-blue-50 p-4 rounded-md">
                    <p className="font-medium text-blue-700">File selezionato:</p>
                    <p className="text-sm text-blue-600">{fileName}</p>
                  </div>
                )}

                {uploadStatus && (
                  <div className="mt-4 bg-green-50 p-4 rounded-md">
                    <p className="text-sm text-green-700">{uploadStatus}</p>
                  </div>
                )}
              </div>

              <div className="flex gap-4">
                <Button type="submit" className="flex-1" disabled={!file || isUploading}>
                  <Upload className="w-4 h-4 mr-2" />
                  {isUploading ? "Caricamento in corso..." : "Carica CV"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setFile(null)
                    setFileName("")
                    setUploadStatus("")
                  }}
                  disabled={isUploading}
                >
                  Cancella
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
