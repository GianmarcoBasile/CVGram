"use client"

import { useState, useEffect } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Upload, Search, LogOut, FileText, Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { getCurrentUser, signOut, fetchUserAttributes } from 'aws-amplify/auth'
import { configureAmplify } from "@/lib/amplify-config"

// Configurazione di Amplify
configureAmplify()

export default function Dashboard() {
  const [user, setUser] = useState<any>(null)
  const [email, setEmail] = useState<string>("")
  const [isLoading, setIsLoading] = useState(true)
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
      } catch (error) {
        // L'utente non è autenticato, redirect alla pagina di login
        router.push("/")
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [router])

  const handleLogout = async () => {
    try {
      await signOut()
      router.push("/")
    } catch (error) {
      console.error("Errore durante il logout:", error)
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
          <div className="flex justify-between items-center py-6">
            <h1 className="text-3xl font-bold text-gray-900">CVGram</h1>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Ciao, {email}</span>
              <Button variant="outline" onClick={handleLogout}>
                <LogOut className="w-4 h-4 mr-2" />
                Esci
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <Link href="/upload">
                <CardHeader className="text-center">
                  <Upload className="w-12 h-12 mx-auto text-blue-600 mb-4" />
                  <CardTitle>Carica CV</CardTitle>
                  <CardDescription>Carica un nuovo curriculum vitae nel sistema</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button className="w-full">Vai al caricamento</Button>
                </CardContent>
              </Link>
            </Card>

            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <Link href="/search">
                <CardHeader className="text-center">
                  <Search className="w-12 h-12 mx-auto text-green-600 mb-4" />
                  <CardTitle>Cerca CV</CardTitle>
                  <CardDescription>Cerca e filtra i curriculum vitae caricati</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button className="w-full">Vai alla ricerca</Button>
                </CardContent>
              </Link>
            </Card>

            <Card className="hover:shadow-lg transition-shadow">
              <Link href="/my-cv">
                <CardHeader className="text-center">
                  <FileText className="w-12 h-12 mx-auto text-purple-600 mb-4" />
                  <CardTitle>I miei CV</CardTitle>
                  <CardDescription>Visualizza i CV che hai caricato</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button className="w-full bg-transparent" variant="outline">
                    Visualizza
                  </Button>
                </CardContent>
              </Link>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}
