from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import boto3
from boto3.dynamodb.conditions import Attr, Key
import os

# Definisci il percorso della build del frontend
FRONTEND_BUILD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

print(FRONTEND_BUILD_PATH)

app = Flask(__name__, static_folder=FRONTEND_BUILD_PATH)
# Abilita CORS per tutte le route con supporto per credenziali
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Inizializza il client DynamoDB
dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
cv_table = dynamodb.Table("CVs")


# Endpoint per servire l'app frontend
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """
    Serve i file statici del frontend costruito con Next.js.
    """
    print(f"Path richiesto: {path}")  # Log per debug

    # Se è una richiesta API, lascia che vengano gestite dagli altri endpoint
    if path.startswith("api/"):
        print(f"Richiesta API, ignorata dal serve_frontend: {path}")  # Log per debug
        return {"error": "Not Found"}, 404

    # Controlla se il percorso esiste direttamente come file
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        print(f"Servendo file diretto: {file_path}")  # Log per debug
        return send_from_directory(app.static_folder, path)

    # Controlla se il percorso è una directory contenente un index.html
    dir_index = os.path.join(app.static_folder, path, "index.html")
    if os.path.isfile(dir_index):
        print(f"Servendo index.html dalla directory: {dir_index}")  # Log per debug
        # Questo gestirà percorsi come /dashboard che puntano a /dashboard/index.html
        return send_from_directory(os.path.join(app.static_folder, path), "index.html")

    # Gestisci percorsi che terminano con /
    if path.endswith("/"):
        adjusted_path = path[:-1]  # Rimuovi lo slash finale
        dir_index = os.path.join(app.static_folder, adjusted_path, "index.html")
        if os.path.isfile(dir_index):
            print(
                f"Servendo index.html dopo aver rimosso lo slash finale: {dir_index}"
            )  # Log per debug
            return send_from_directory(
                os.path.join(app.static_folder, adjusted_path), "index.html"
            )

    # Per SPA, servi index.html dalla radice per tutte le altre richieste
    # Next.js gestirà il routing lato client
    print(
        f"Fallback: servendo index.html dalla root per il percorso: {path}"
    )  # Log per debug
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/cvs", methods=["GET"])
def get_cvs():
    """
    Recupera i CV dal database.
    Supporta il filtraggio tramite query parameter 'keywords'.
    Esempio: /api/cvs?keywords=python,aws,react
    """
    try:
        # Controlla se sono state fornite parole chiave
        keywords = request.args.get("keywords", "")

        if keywords:
            # Dividi le parole chiave per virgola
            keyword_list = keywords.lower().split(",")
            keyword_list = [k.strip() for k in keyword_list if k.strip()]

            # Inizializza una lista vuota per i risultati
            results = []
            if keyword_list:
                from functools import reduce
                from operator import or_

                filters = [Attr("text").contains(k) for k in keyword_list]
                keyword_filter = reduce(or_, filters)
                response = cv_table.scan(FilterExpression=keyword_filter)
                results = response["Items"]
                # Gestione della paginazione per grandi set di dati
                while "LastEvaluatedKey" in response:
                    response = cv_table.scan(
                        FilterExpression=keyword_filter,
                        ExclusiveStartKey=response["LastEvaluatedKey"],
                    )
                    results.extend(response["Items"])
                return (
                    jsonify(
                        {
                            "message": "CVs filtrati recuperati con successo",
                            "count": len(results),
                            "cvs": results,
                        }
                    ),
                    200,
                )

        # Se non ci sono parole chiave, recupera tutti i CV
        response = cv_table.scan()
        results = response["Items"]

        # Gestione della paginazione per grandi set di dati
        while "LastEvaluatedKey" in response:
            response = cv_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            results.extend(response["Items"])

        return (
            jsonify(
                {
                    "message": "Tutti i CV recuperati con successo",
                    "count": len(results),
                    "cvs": results,
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "error": str(e),
                    "message": "Si è verificato un errore durante il recupero dei CV",
                }
            ),
            500,
        )


@app.route("/api/cvs/user/<string:email>", methods=["GET"])
def get_user_cvs(email):
    """
    Recupera tutti i CV di un utente specifico dal database utilizzando l'indice secondario globale.
    """
    try:
        # Esegui una query sull'indice secondario globale EmailIndex
        response = cv_table.query(
            IndexName="EmailIndex", KeyConditionExpression=Key("email").eq(email)
        )
        results = response["Items"]

        # Gestione della paginazione per grandi set di dati
        while "LastEvaluatedKey" in response:
            response = cv_table.query(
                IndexName="EmailIndex",
                KeyConditionExpression=Key("email").eq(email),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            results.extend(response["Items"])

        if results:
            return (
                jsonify(
                    {
                        "message": f"CV dell'utente {email} recuperati con successo",
                        "count": len(results),
                        "cvs": results,
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "message": f"Nessun CV trovato per l'utente {email}",
                        "count": 0,
                        "cvs": [],
                    }
                ),
                200,
            )

    except Exception as e:
        print(
            f"Errore durante il recupero dei CV per l'utente {email}: {str(e)}"
        )  # Log per debug
        return (
            jsonify(
                {
                    "error": str(e),
                    "message": "Si è verificato un errore durante il recupero dei CV dell'utente",
                }
            ),
            500,
        )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 80)))
