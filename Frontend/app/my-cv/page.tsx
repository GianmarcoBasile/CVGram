"use client"

import { useState, useEffect } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { getCurrentUser } from 'aws-amplify/auth'
import { getUrl } from 'aws-amplify/storage'
import { useRouter } from "next/navigation"
import { configureAmplify } from "@/lib/amplify-config"
import Link from "next/link"
import { ArrowLeft, Loader2 } from "lucide-react"
import { Download } from "lucide-react"

configureAmplify()

export default function MyCVPage() {
  const [email, setEmail] = useState<string | null>(null)
  const [cvs, setCvs] = useState<any[]>([])
  const [isLoading, setLoading] = useState(true)
  const [error, setError] = useState<string>("")
  const router = useRouter()

  useEffect(() => {
    const fetchCVs = async () => {
      try {
        setLoading(true)
        // Recupera userId
        const userData = await getCurrentUser()
        const email = userData.signInDetails?.loginId || ""
        setEmail(email)
        console.log("User Email:", email)
        // Chiama l'API Flask
        const res = await fetch(`/api/cvs/user/${email}`)
        if (!res.ok) throw new Error("Errore nella fetch dei CV")
        const data = await res.json()
        setCvs(data.cvs || [])
      } catch (err: any) {
        setError(err.message || "Errore generico")
      } finally {
        setLoading(false)
      }
    }
    fetchCVs()
  }, [])


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
            <h1 className="text-3xl font-bold text-gray-900">I miei CV</h1>
          </div>
        </div>
      </header>
      <main className="max-w-4xl mx-auto py-8">
        {error ? (
          <div className="text-red-600">{error}</div>
        ) : cvs.length === 0 ? (
          <div className="text-gray-600">Nessun CV caricato.</div>
        ) : (
          <div className="w-full">
            {cvs.map((cv, idx) => (
              <Card key={cv.cv_id || idx}>
                <CardHeader className="flex flex-row items-center justify-between w-full">
                  <div className="w-full">
                    <CardTitle className="flex justify-between gap-2 w-full">
                      {cv.original_filename || cv.s3_key?.split("/").pop() || "CV"}
                      <Button
                        size="lg"
                        variant="outline"
                        title="Scarica PDF"
                        onClick={async () => {
                          try {
                            const { url } = await getUrl({ path: cv.s3_key, options: { expiresIn: 60 } });
                            window.open(url, '_blank');
                          } catch (err) {
                            alert('Errore nel download del file');
                          }
                        }}
                        className="mt-4"
                      >
                        <Download className="w-6 h-6" />
                        Scarica
                      </Button>
                    </CardTitle>
                    <CardDescription>
                      Caricato il: {new Date(cv.uploaded_at).toLocaleString() || "-"}
                    </CardDescription>
                  </div>
                </CardHeader>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
