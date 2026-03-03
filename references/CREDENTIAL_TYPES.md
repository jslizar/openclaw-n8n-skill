# n8n Credential Type Registry

Exact credential type strings and required fields for every common service.
Use these when attaching credentials to nodes — no guessing.

---

## How Credentials Work in n8n

### In Node JSON
```json
{
  "credentials": {
    "credentialTypeName": {
      "id": "credential-id-from-n8n",
      "name": "Display Name"
    }
  }
}
```

### Creating via API
```javascript
// 1. Get the schema to see required fields
GET /api/v1/credentials/schema/{credentialType}

// 2. Create the credential
POST /api/v1/credentials
{
  "name": "My Slack Bot",
  "type": "slackApi",
  "data": { "accessToken": "xoxb-..." }
}
```

### Listing Existing Credentials
```javascript
GET /api/v1/credentials
// Returns: [{ id, name, type, createdAt, updatedAt }]
// Does NOT return secret data (tokens, keys)
```

---

## Communication & Messaging

| Service | Credential Type | Auth Method | Required Fields |
|---------|----------------|-------------|-----------------|
| **Slack** (Bot Token) | `slackApi` | API Token | `accessToken` (xoxb-...) |
| **Slack** (OAuth2) | `slackOAuth2Api` | OAuth2 | `clientId`, `clientSecret` + OAuth flow |
| **Discord** (Bot) | `discordApi` | Bot Token | `botToken` |
| **Discord** (Webhook) | `discordWebhookApi` | Webhook URL | `webhookUri` |
| **Telegram** | `telegramApi` | Bot Token | `accessToken` |
| **Microsoft Teams** | `microsoftTeamsOAuth2Api` | OAuth2 | `clientId`, `clientSecret`, `tenantId` |
| **Twilio** | `twilioApi` | API Key | `accountSid`, `authToken` |
| **SendGrid** | `sendGridApi` | API Key | `apiKey` |
| **Mailchimp** | `mailchimpApi` | API Key | `apiKey` |

### Slack Node Example
```json
{
  "name": "Slack",
  "type": "n8n-nodes-base.slack",
  "typeVersion": 2.2,
  "credentials": {
    "slackApi": { "id": "CRED_ID", "name": "Slack Bot" }
  }
}
```

---

## Email

| Service | Credential Type | Auth Method | Required Fields |
|---------|----------------|-------------|-----------------|
| **Gmail** | `gmailOAuth2` | OAuth2 | `clientId`, `clientSecret` + OAuth flow |
| **Microsoft Outlook** | `microsoftOutlookOAuth2Api` | OAuth2 | `clientId`, `clientSecret` |
| **SMTP** (generic) | `smtp` | SMTP Auth | `host`, `port`, `user`, `password`, `secure` |
| **IMAP** (generic) | `imap` | IMAP Auth | `host`, `port`, `user`, `password`, `secure` |

### Gmail Node Example
```json
{
  "name": "Gmail",
  "type": "n8n-nodes-base.gmail",
  "typeVersion": 2.1,
  "credentials": {
    "gmailOAuth2": { "id": "CRED_ID", "name": "Gmail" }
  }
}
```

---

## Google Services

| Service | Credential Type | Auth Method | Required Fields |
|---------|----------------|-------------|-----------------|
| **Google Sheets** | `googleSheetsOAuth2Api` | OAuth2 | `clientId`, `clientSecret` + OAuth |
| **Google Drive** | `googleDriveOAuth2Api` | OAuth2 | `clientId`, `clientSecret` + OAuth |
| **Google Calendar** | `googleCalendarOAuth2Api` | OAuth2 | `clientId`, `clientSecret` + OAuth |
| **Google Docs** | `googleDocsOAuth2Api` | OAuth2 | `clientId`, `clientSecret` + OAuth |
| **Google BigQuery** | `googleBigQueryOAuth2Api` | OAuth2 | `clientId`, `clientSecret` + OAuth |
| **Google (Service Account)** | `googleApi` | Service Account | `email`, `privateKey`, `scopes` |

### Google Sheets Node Example
```json
{
  "name": "Google Sheets",
  "type": "n8n-nodes-base.googleSheets",
  "typeVersion": 4.5,
  "credentials": {
    "googleSheetsOAuth2Api": { "id": "CRED_ID", "name": "Google Sheets" }
  }
}
```

---

## CRM & Sales

| Service | Credential Type | Auth Method | Required Fields |
|---------|----------------|-------------|-----------------|
| **HubSpot** (API Key) | `hubspotApi` | API Key | `apiKey` |
| **HubSpot** (OAuth2) | `hubspotOAuth2Api` | OAuth2 | `clientId`, `clientSecret` + OAuth |
| **HubSpot** (App Token) | `hubspotAppToken` | App Token | `appToken` |
| **Salesforce** | `salesforceOAuth2Api` | OAuth2 | `clientId`, `clientSecret`, `instanceUrl` |
| **Pipedrive** | `pipedriveApi` | API Token | `apiToken` |
| **Zoho CRM** | `zohoCrmOAuth2Api` | OAuth2 | `clientId`, `clientSecret` + OAuth |
| **Monday.com** | `mondayComApi` | API Token | `apiToken` |

### HubSpot Node Example
```json
{
  "name": "HubSpot",
  "type": "n8n-nodes-base.hubspot",
  "typeVersion": 2,
  "credentials": {
    "hubspotAppToken": { "id": "CRED_ID", "name": "HubSpot" }
  }
}
```

---

## Project Management

| Service | Credential Type | Auth Method | Required Fields |
|---------|----------------|-------------|-----------------|
| **Notion** | `notionApi` | Integration Token | `apiKey` |
| **Airtable** | `airtableTokenApi` | Personal Token | `accessToken` |
| **Asana** | `asanaApi` | Personal Token | `accessToken` |
| **Asana** (OAuth2) | `asanaOAuth2Api` | OAuth2 | `clientId`, `clientSecret` + OAuth |
| **Jira** | `jiraSoftwareCloudApi` | API Token | `email`, `apiToken`, `domain` |
| **Trello** | `trelloApi` | API Key + Token | `apiKey`, `apiToken` |
| **ClickUp** | `clickUpApi` | API Token | `accessToken` |
| **Linear** | `linearApi` | API Key | `apiKey` |
| **Todoist** | `todoistApi` | API Token | `apiKey` |

### Notion Node Example
```json
{
  "name": "Notion",
  "type": "n8n-nodes-base.notion",
  "typeVersion": 2.2,
  "credentials": {
    "notionApi": { "id": "CRED_ID", "name": "Notion" }
  }
}
```

---

## Databases

| Service | Credential Type | Auth Method | Required Fields |
|---------|----------------|-------------|-----------------|
| **PostgreSQL** | `postgres` | Connection | `host`, `port`, `database`, `user`, `password` |
| **MySQL** | `mySql` | Connection | `host`, `port`, `database`, `user`, `password` |
| **MongoDB** | `mongoDb` | Connection String | `connectionString` |
| **Redis** | `redis` | Connection | `host`, `port`, `password` (optional) |
| **Microsoft SQL** | `microsoftSql` | Connection | `server`, `port`, `database`, `user`, `password` |
| **Supabase** | `supabaseApi` | API Key | `host`, `serviceRole` |
| **Elasticsearch** | `elasticsearchApi` | Basic Auth | `baseUrl`, `username`, `password` |

### PostgreSQL Node Example
```json
{
  "name": "Postgres",
  "type": "n8n-nodes-base.postgres",
  "typeVersion": 2.5,
  "credentials": {
    "postgres": { "id": "CRED_ID", "name": "Production DB" }
  }
}
```

---

## AI & Language Models

| Service | Credential Type | Auth Method | Required Fields |
|---------|----------------|-------------|-----------------|
| **OpenAI** | `openAiApi` | API Key | `apiKey` |
| **Anthropic** | `anthropicApi` | API Key | `apiKey` |
| **Google Gemini** | `googlePalmApi` | API Key | `apiKey` |
| **Azure OpenAI** | `azureOpenAiApi` | API Key | `apiKey`, `resourceName`, `apiVersion` |
| **Groq** | `groqApi` | API Key | `apiKey` |
| **Mistral** | `mistralCloudApi` | API Key | `apiKey` |
| **Ollama** | `ollamaApi` | URL | `baseUrl` |
| **DeepSeek** | `deepSeekApi` | API Key | `apiKey` |
| **Pinecone** | `pineconeApi` | API Key | `apiKey`, `environment` |

### OpenAI Model Node Example
```json
{
  "name": "OpenAI Model",
  "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
  "typeVersion": 1.2,
  "credentials": {
    "openAiApi": { "id": "CRED_ID", "name": "OpenAI" }
  }
}
```

### Anthropic Model Node Example
```json
{
  "name": "Anthropic Model",
  "type": "@n8n/n8n-nodes-langchain.lmChatAnthropic",
  "typeVersion": 1.3,
  "credentials": {
    "anthropicApi": { "id": "CRED_ID", "name": "Anthropic" }
  }
}
```

---

## Cloud & DevOps

| Service | Credential Type | Auth Method | Required Fields |
|---------|----------------|-------------|-----------------|
| **AWS** | `aws` | Access Keys | `accessKeyId`, `secretAccessKey`, `region` |
| **GitHub** | `githubApi` | Personal Token | `accessToken` |
| **GitHub** (OAuth2) | `githubOAuth2Api` | OAuth2 | `clientId`, `clientSecret` + OAuth |
| **GitLab** | `gitlabApi` | Personal Token | `accessToken`, `server` |
| **Cloudflare** | `cloudflareApi` | API Token | `apiToken` |

---

## HTTP & Generic Auth

| Credential Type | Use When | Required Fields |
|----------------|----------|-----------------|
| `httpHeaderAuth` | API key in custom header | `name` (header name), `value` (key) |
| `httpBasicAuth` | Basic auth (user:pass) | `user`, `password` |
| `httpDigestAuth` | Digest auth | `user`, `password` |
| `httpQueryAuth` | API key in query param | `name` (param name), `value` (key) |
| `oAuth2Api` | Generic OAuth2 | `clientId`, `clientSecret`, `accessTokenUrl`, `authUrl` |
| `oAuth1Api` | Generic OAuth1 | `consumerKey`, `consumerSecret`, `requestTokenUrl`, ... |

### HTTP Request with Header Auth Example
```json
{
  "name": "HTTP Request",
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4.2,
  "parameters": {
    "url": "https://api.example.com/data",
    "authentication": "predefinedCredentialType",
    "nodeCredentialType": "httpHeaderAuth"
  },
  "credentials": {
    "httpHeaderAuth": { "id": "CRED_ID", "name": "API Key" }
  }
}
```

### HTTP Request with Generic OAuth2 Example
```json
{
  "name": "HTTP Request",
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4.2,
  "parameters": {
    "url": "https://api.example.com/data",
    "authentication": "predefinedCredentialType",
    "nodeCredentialType": "oAuth2Api"
  },
  "credentials": {
    "oAuth2Api": { "id": "CRED_ID", "name": "OAuth2 Service" }
  }
}
```

---

## Payments & E-Commerce

| Service | Credential Type | Auth Method | Required Fields |
|---------|----------------|-------------|-----------------|
| **Stripe** | `stripeApi` | Secret Key | `secretKey` |
| **Shopify** | `shopifyApi` | API Key + Password | `apiKey`, `password`, `shopSubdomain` |
| **WooCommerce** | `wooCommerceApi` | API Key | `consumerKey`, `consumerSecret`, `url` |
| **PayPal** | `payPalApi` | Client ID + Secret | `clientId`, `secret`, `env` (sandbox/live) |

---

## Storage & Files

| Service | Credential Type | Auth Method | Required Fields |
|---------|----------------|-------------|-----------------|
| **AWS S3** | `aws` | Access Keys | `accessKeyId`, `secretAccessKey`, `region` |
| **Dropbox** | `dropboxOAuth2Api` | OAuth2 | `clientId`, `clientSecret` + OAuth |
| **FTP** | `ftp` | FTP Auth | `host`, `port`, `username`, `password` |
| **SFTP** | `sftp` | SFTP Auth | `host`, `port`, `username`, `password`/`privateKey` |
| **SSH** | `sshPassword` or `sshPrivateKey` | Password/Key | `host`, `port`, `username`, + auth |

---

## Quick Lookup: Node → Credential Type

| Node Type | Credential Key in JSON |
|-----------|----------------------|
| `n8n-nodes-base.slack` | `slackApi` or `slackOAuth2Api` |
| `n8n-nodes-base.gmail` | `gmailOAuth2` |
| `n8n-nodes-base.googleSheets` | `googleSheetsOAuth2Api` |
| `n8n-nodes-base.notion` | `notionApi` |
| `n8n-nodes-base.airtable` | `airtableTokenApi` |
| `n8n-nodes-base.hubspot` | `hubspotAppToken` or `hubspotOAuth2Api` |
| `n8n-nodes-base.postgres` | `postgres` |
| `n8n-nodes-base.mysql` | `mySql` |
| `n8n-nodes-base.mongodb` | `mongoDb` |
| `n8n-nodes-base.redis` | `redis` |
| `n8n-nodes-base.httpRequest` | varies: `httpHeaderAuth`, `httpBasicAuth`, `oAuth2Api` |
| `n8n-nodes-base.stripe` | `stripeApi` |
| `n8n-nodes-base.telegram` | `telegramApi` |
| `n8n-nodes-base.discord` | `discordApi` or `discordWebhookApi` |
| `@n8n/n8n-nodes-langchain.lmChatOpenAi` | `openAiApi` |
| `@n8n/n8n-nodes-langchain.lmChatAnthropic` | `anthropicApi` |
| `@n8n/n8n-nodes-langchain.lmChatGoogleGemini` | `googlePalmApi` |
| `@n8n/n8n-nodes-langchain.lmChatGroq` | `groqApi` |
| `@n8n/n8n-nodes-langchain.lmChatOllama` | `ollamaApi` |
| `@n8n/n8n-nodes-langchain.lmChatAzureOpenAi` | `azureOpenAiApi` |
| `@n8n/n8n-nodes-langchain.lmChatMistralCloud` | `mistralCloudApi` |
| `@n8n/n8n-nodes-langchain.memoryPostgresChat` | `postgres` |
| `@n8n/n8n-nodes-langchain.memoryRedisChat` | `redis` |
| `@n8n/n8n-nodes-langchain.vectorStorePinecone` | `pineconeApi` |
