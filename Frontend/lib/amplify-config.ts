"use client";

import { Amplify } from "aws-amplify";
import {
  cognitoUserPoolId,
  cognitoClientId,
  cognitoIdentityPoolId,
} from "@/config";
import path from "path";

// S3 bucket e regione
export const s3BucketName = "cvgram-cv-bucket";
export const s3Region = "eu-west-2";

// Verifica se Amplify è già configurato
let isConfigured = false;

export function configureAmplify() {
  if (!isConfigured) {
    try {
      Amplify.configure({
        Auth: {
          Cognito: {
            userPoolId: cognitoUserPoolId,
            userPoolClientId: cognitoClientId,
            identityPoolId: cognitoIdentityPoolId,
            loginWith: { email: true },
          },
        },
        Storage: {
          S3: {
            bucket: s3BucketName,
            region: s3Region,
          },
        },
      });

      isConfigured = true;
    } catch (error) {
      console.error("Errore nella configurazione di Amplify:", error);
    }
  }
}

// Esporta i valori di configurazione per riferimento diretto
export { cognitoUserPoolId, cognitoClientId, cognitoIdentityPoolId };
