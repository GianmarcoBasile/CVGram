"use client";

import { Amplify } from "aws-amplify";
import {
  cognitoUserPoolId,
  cognitoClientId,
  cognitoIdentityPoolId,
} from "@/config";

export const s3BucketName = "cvgram-cv-bucket";
export const s3Region = "eu-west-2";

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

export { cognitoUserPoolId, cognitoClientId, cognitoIdentityPoolId };
