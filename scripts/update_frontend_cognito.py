import json

cognito_config_path = "../cognito_config.json"
index_ts_path = "../Frontend/config/index.ts"

with open(cognito_config_path) as f:
    conf = json.load(f)

new_content = f'''export const cognitoUserPoolId: string = "{conf["userPoolId"]}";
export const cognitoClientId: string = "{conf["clientId"]}";
export const cognitoIdentityPoolId: string = "{conf["identityPoolId"]}";
'''

with open(index_ts_path, "w") as f:
    f.write(new_content)

print("index.ts aggiornato con i valori di cognito_config.json")