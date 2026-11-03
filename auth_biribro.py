import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CLIENT_SECRETS_FILE = '/Users/tim/youtube-uploader/client_secrets.json'
OUT_TOKEN = '/Users/tim/youtube-uploader/channels/biribro/token.json'

flow = InstalledAppFlow.from_client_secrets_file(
    CLIENT_SECRETS_FILE,
    SCOPES,
    redirect_uri='http://localhost:8080/'
)

auth_url, _ = flow.authorization_url(prompt='select_account')
print("AUTH_URL:", auth_url)
sys.stdout.flush()

creds = flow.run_local_server(port=8080, open_browser=False)

os.makedirs(os.path.dirname(OUT_TOKEN), exist_ok=True)
with open(OUT_TOKEN, 'w') as f:
    f.write(creds.to_json())
print("SAVED_TOKEN:", OUT_TOKEN)
