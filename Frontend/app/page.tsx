"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useRouter } from "next/navigation"

import { signIn, signUp, getCurrentUser, confirmSignUp } from 'aws-amplify/auth';
import { configureAmplify } from "@/lib/amplify-config"

configureAmplify();

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showConfirm, setShowConfirm] = useState(false)
  const [confirmationCode, setConfirmationCode] = useState("")
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [checkingAuth, setCheckingAuth] = useState(true)

  useEffect(() => {
    getCurrentUser()
      .then(() => {
        router.push("/dashboard")
      })
      .catch(() => { })
      .finally(() => setCheckingAuth(false))
  }, [router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    if (isLogin) {
      try {
        await signIn({ username: email, password })
        router.push("/dashboard")
      } catch (error: any) {
        alert("Login fallito: " + (error.message || error))
      } finally {
        setLoading(false)
      }
    } else {
      if (password !== confirmPassword) {
        alert("Le password non corrispondono")
        setLoading(false)
        return
      }
      try {
        await signUp({
          username: email,
          password,
          options: { userAttributes: { email } }
        })
        setShowConfirm(true)
        alert("Registrazione avvenuta! Controlla la mail per confermare l'account.")
      } catch (error: any) {
        alert("Registrazione fallita: " + (error.message || error))
      } finally {
        setLoading(false)
      }
    }
  }

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await confirmSignUp({ username: email, confirmationCode })
      alert("Account confermato! Ora puoi accedere.")
      setShowConfirm(false)
      setIsLogin(true)
    } catch (error: any) {
      alert("Errore nella conferma: " + (error.message || error))
    } finally {
      setLoading(false)
    }
  }

  if (checkingAuth) {
    return <div className="min-h-screen flex items-center justify-center">Caricamento...</div>
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">CVGram</CardTitle>
          <CardDescription>Gestisci e cerca curriculum vitae</CardDescription>
        </CardHeader>
        <CardContent>
          {showConfirm ? (
            <form onSubmit={handleConfirm} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="confirmationCode">Codice di conferma</Label>
                <Input
                  id="confirmationCode"
                  type="text"
                  value={confirmationCode}
                  onChange={(e) => setConfirmationCode(e.target.value)}
                  required
                />
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Conferma in corso..." : "Conferma account"}
              </Button>
            </form>
          ) : (
            <Tabs
              value={isLogin ? "login" : "register"}
              onValueChange={(value) => {
                setIsLogin(value === "login")
                setConfirmPassword("")
              }}
            >
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="login">Accedi</TabsTrigger>
                <TabsTrigger value="register">Registrati</TabsTrigger>
              </TabsList>

              <TabsContent value="login">
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={loading}>
                    {loading ? "Accesso in corso..." : "Accedi"}
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="register">
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword">Conferma Password</Label>
                    <Input
                      id="confirmPassword"
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={loading}>
                    {loading ? "Registrazione in corso..." : "Registrati"}
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
