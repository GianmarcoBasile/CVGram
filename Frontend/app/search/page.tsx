"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, Search, User, Mail, Phone, Calendar, Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { getCurrentUser, fetchUserAttributes } from 'aws-amplify/auth'
import { configureAmplify } from "@/lib/amplify-config"

// Configurazione di Amplify
configureAmplify();

export default function SearchPage() {
  const [user, setUser] = useState<any>(null)
  const [email, setEmail] = useState<string>("")
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [keywords, setKeywords] = useState<string[]>([])
  const [cvs, setCvs] = useState<any[]>([])
  const [filteredCvs, setFilteredCvs] = useState<any[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [searchError, setSearchError] = useState("")
  const router = useRouter()

  useEffect(() => {
    const checkAuth = async () => {
      try {
        setIsLoading(true)
        const userData = await getCurrentUser()
        setUser(userData)

        // Recupera gli attributi dell'utente, inclusa l'email
        const attributes = await fetchUserAttributes()
        if (attributes.email) {
          setEmail(attributes.email)
        } else {
          setEmail(userData.username)
        }

        // Carica tutti i CV all'avvio (solo se non c'è filtro)
        try {
          const res = await fetch("/api/cvs")
          if (res.ok) {
            const data = await res.json()
            setCvs(data.cvs || [])
            setFilteredCvs(data.cvs || [])
          } else {
            setCvs([])
            setFilteredCvs([])
          }
        } catch {
          setCvs([])
          setFilteredCvs([])
        }
      } catch (error) {
        // L'utente non è autenticato, redirect alla pagina di login
        router.push("/")
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [router])

  // Effettua la ricerca ogni volta che searchTerm cambia (debounced)
  useEffect(() => {
    const fetchCVs = async () => {
      setIsSearching(true)
      setSearchError("")
      try {
        let url = "/api/cvs"
        if (keywords.length > 0) {
          url += `?keywords=${encodeURIComponent(keywords.join(","))}`
        }
        const res = await fetch(url)
        if (!res.ok) throw new Error("Errore nella ricerca dei CV")
        const data = await res.json()
        setCvs(data.cvs || [])
        setFilteredCvs(data.cvs || [])
      } catch (err: any) {
        setSearchError(err.message || "Errore generico nella ricerca")
        setCvs([])
        setFilteredCvs([])
      } finally {
        setIsSearching(false)
      }
    }
    // Debounce: attendi 400ms dopo l'ultimo cambiamento keywords
    const timeout = setTimeout(fetchCVs, 400)
    return () => clearTimeout(timeout)
  }, [keywords])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("it-IT")
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
            <h1 className="text-3xl font-bold text-gray-900">Cerca CV</h1>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="space-y-6">
          {/* Filtri di ricerca */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Search className="w-6 h-6 mr-2" />
                Filtri di Ricerca
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="search">Ricerca generale</Label>
                  <Input
                    id="search"
                    placeholder="Cerca per nome del file o parole chiave..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && searchTerm.trim()) {
                        e.preventDefault();
                        if (!keywords.includes(searchTerm.trim().toLowerCase())) {
                          setKeywords([...keywords, searchTerm.trim().toLowerCase()]);
                        }
                        setSearchTerm("");
                      }
                    }}
                  />
                  {/* Mostra i tag delle keyword */}
                  <div className="flex flex-wrap gap-2 mt-2">
                    {keywords.map((kw, idx) => (
                      <Badge key={kw} variant="secondary" className="flex items-center gap-1 pr-2">
                        {kw}
                        <button
                          type="button"
                          className="ml-1 text-xs text-gray-500 hover:text-red-600"
                          onClick={() => setKeywords(keywords.filter((k) => k !== kw))}
                          aria-label={`Rimuovi ${kw}`}
                        >
                          ×
                        </button>
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
              <div className="mt-4 flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    setSearchTerm("");
                    setKeywords([]);
                  }}
                >
                  Cancella filtri
                </Button>
                <Badge variant="secondary">{isSearching ? "..." : filteredCvs.length + " CV trovati"}</Badge>
              </div>
            </CardContent>
          </Card>

          {/* Risultati */}
          <div className="space-y-4">
            {searchError ? (
              <Card>
                <CardContent className="text-center py-8 text-red-600">
                  Errore: {searchError}
                </CardContent>
              </Card>
            ) : isSearching ? (
              <Card>
                <CardContent className="text-center py-8">
                  <Search className="w-12 h-12 mx-auto text-gray-400 mb-4 animate-pulse" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Ricerca in corso...</h3>
                </CardContent>
              </Card>
            ) : filteredCvs.length === 0 ? (
              <Card>
                <CardContent className="text-center py-8">
                  <Search className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Nessun CV trovato</h3>
                  <p className="text-gray-600">Prova a modificare i criteri di ricerca o carica nuovi CV.</p>
                </CardContent>
              </Card>
            ) : (
              filteredCvs.map((cv) => (
                <Card key={cv.cv_id || cv.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="flex items-center">
                          <User className="w-5 h-5 mr-2" />
                          {cv.original_filename || cv.fileName || "CV senza nome"}
                        </CardTitle>
                        <CardDescription className="flex items-center mt-1">
                          <Calendar className="w-4 h-4 mr-1" />
                          Caricato il {formatDate(cv.uploaded_at || cv.uploadDate)} da {cv.uploadedBy || cv.email || "-"}
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {cv.keywords && cv.keywords.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-2">Parole chiave estratte:</h4>
                          <div className="flex flex-wrap gap-2">
                            {cv.keywords.map((keyword: string, index: number) => (
                              <Badge key={index} variant="secondary">
                                {keyword}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      <div className="flex justify-end mt-4">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={async () => {
                            // Download tramite Amplify Storage (come in /my-cv)
                            try {
                              const { getUrl } = await import('aws-amplify/storage');
                              const { url } = await getUrl({ path: cv.s3_key, options: { expiresIn: 60 } });
                              window.open(url, '_blank');
                            } catch (err) {
                              alert('Errore nel download del file');
                            }
                          }}
                        >
                          Scarica CV
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
