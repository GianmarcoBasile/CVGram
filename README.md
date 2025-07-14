# CVGram

CVGram è una piattaforma cloud per la gestione e la visualizzazione di CV, composta da un backend Flask/Python e un frontend Next.js, con deploy automatizzato su AWS tramite GitHub Actions.

## Struttura del progetto

- **Backend/**: API Flask, Dockerfile, requirements.txt
- **Frontend/**: App Next.js, componenti UI, configurazioni Tailwind
- **scripts/**: Script Python per deploy AWS (EC2, Cognito, DynamoDB, ecc.)
- **.github/workflows/**: Workflow GitHub Actions per build e deploy automatico

## Requisiti

- AWS CLI configurato
- Python 3.8+
- Node.js 18+
- Docker
- Chiave SSH per EC2
- Variabili d’ambiente AWS (vedi `.env.example`)

## Deploy automatico

Il deploy viene gestito tramite GitHub Actions:

- Build del frontend e backend
- Push dell’immagine Docker su Amazon ECR
- Notifica al master EC2 per aggiornare il servizio

## Script principali

- `start_instances.py`: Avvia tutte le istanze EC2 e lancia il webhook server sul master.
- `stop_instances.py`: Ferma tutte le istanze EC2.
- `deploy_script.sh/deploy_script.bat`: Effettua il deploy di tutti i servizi necessari

## Esempio di utilizzo

```bash
python start_instances.py
python stop_instances.py
```

## Workflow GitHub Actions

Il file `.github/workflows/deploy-backend-ecr.yml` gestisce:

- Build frontend e backend
- Deploy su ECR
- Notifica al master EC2 via webhook

## Note importanti

- Assicurati che le chiavi e le variabili d’ambiente siano correttamente configurate.
- Per modifiche infrastrutturali, aggiorna gli script in `scripts/`.

## Autori

- Gianmarco Basile
