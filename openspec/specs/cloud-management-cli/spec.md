# Cloud Management (CLI + SDK)

## Purpose
With a `cloud` profile, `sinx` manages Sinapsis Cloud resources through the SDK:
- saved agents and their versions
- the template registry
- files
- secrets
- API keys
- webhooks
- authenticated access to private package indexes

Citation prefixes:
- `cli:` is `packages/python/cli/sinapsis-cli/src/sinapsis_cli/commands/cloud/`
- `sdk:` is `packages/python/sdk/sinapsis-sdk/src/sinapsis_sdk/cloud_api/resources/`
- `contracts:` is `packages/python/sdk/sinapsis-contracts/src/sinapsis_contracts/cloud_api/`

## Requirements

### Requirement: Saved agents and versions
`sinx cloud agents` SHALL provide `register FILE --version LABEL [--name]`, `publish AGENT_ID FILE --version`, `list [--all]`, `versions [AGENT_ID] [--all]` and `version [AGENT_ID] [VERSION_ID]`. Each of these SHALL update the profile's remembered agent selection. (src: cli:agents.py:32-135)

#### Scenario: Register an agent
- **WHEN** a user runs `sinx cloud agents register agent.yml --version v1`
- **THEN** the CLI SHALL print "Agent ID:" and "Version ID: … (v1)"
- **AND** it SHALL remember the pair for later schedule creation

#### Scenario: Listing
- **WHEN** a user runs `sinx cloud agents list --all`
- **THEN** agents SHALL be fetched in pages of 200
- **AND** each line SHALL be printed as `id | name | registration_source | created=`

### Requirement: Saved agent endpoints
The SDK SHALL manage saved agents under `/api/v1/management/agents`, and each agent version SHALL carry a sha256 checksum. (src: sdk:agents.py; contracts:saved_agent.py)

#### Scenario: Endpoint mapping
- **WHEN** an agent is registered
- **THEN** the SDK SHALL call `POST /register`
- **AND** publishing a version SHALL call `POST /{id}/versions`
- **AND** listing SHALL call `GET ""`, and fetching SHALL call `GET /{id}`, `GET /{id}/versions` and `GET /{id}/versions/{vid}`
- **AND** each version `checksum` SHALL match `^[0-9a-f]{64}$`

### Requirement: Template registry search
`sinx cloud templates` SHALL provide `search QUERY [--category] [--package] [--tag] [--limit] [--offset]`, `list`, `show TEMPLATE_UUID` and `packages`, and every listing SHALL end with a pagination footer. (src: cli:templates.py:14-21)

#### Scenario: Search by tag
- **WHEN** a user runs `sinx cloud templates search ocr --tag vision`
- **THEN** the matching templates SHALL be printed
- **AND** the output SHALL end with "Showing N of TOTAL results (offset O)"
- **AND** `--limit` SHALL default to 50 (range 1..200) and `--offset` to 0

### Requirement: Files
`sinx cloud files` SHALL provide `upload FILE`, `get PATH -o FILE`, `list [ROOT=/]`, `fetch AGENT_ID FILE_ID -o FILE` and `search NAME`, all backed by the SDK under `/api/v1/files`. (src: cli:files.py; sdk:files.py)

#### Scenario: Download a file
- **WHEN** a user runs `sinx cloud files get data/in.png -o in.png`
- **THEN** the file SHALL be saved
- **AND** the CLI SHALL print "File saved to in.png"

#### Scenario: Endpoint mapping
- **WHEN** the SDK files resource is used
- **THEN** upload SHALL call `POST /upload/{path}` as multipart
- **AND** list SHALL call `GET /ls/{prefix}`, and search SHALL call `POST /search`
- **AND** download SHALL call `GET /get/{path}` or `GET /fetch/{agent_id}/{file_id}`, and delete SHALL call `DELETE /{path}`

### Requirement: Secrets
`sinx cloud secrets` SHALL provide `create [LABEL] [--label] [--value]`, `list`, `get UUID` and `delete UUID`. When no value is supplied, it SHALL prompt for the secret value as hidden input with confirmation. (src: cli:secrets.py; contracts:secrets/payloads.py:5-6)

#### Scenario: Short label rejected
- **WHEN** a user creates a secret with label `ab`
- **THEN** validation SHALL fail, because label and value must each be 3–64 characters

#### Scenario: Missing label
- **WHEN** `create` is run without a label
- **THEN** the CLI SHALL fail with "Label is required. Use `create LABEL` or `create --label LABEL`."

#### Scenario: Delete confirmation
- **WHEN** `delete UUID` is run
- **THEN** the CLI SHALL always ask for confirmation

### Requirement: API keys
`sinx cloud api-keys` SHALL create scoped keys limited to the 16 `ApiKeyPermission` values, and SHALL provide `permissions`, `list`, `delete` and `copy`. (src: cli:api_keys.py:15-121; contracts:api_key_permissions.py)

#### Scenario: Default scope
- **WHEN** `api-keys create --name ci` is run with no `--scope`
- **THEN** the SDK SHALL request the scope `["files:read"]`

#### Scenario: Permission set
- **WHEN** `api-keys permissions` is run
- **THEN** it SHALL list `agents:{read,execute,results:read,manage}`, `jobs:{create,read,cancel,delete,results:read,stream}`, `files:{read,write}`, `webhooks:{read,manage}` and `packages:{read,write}`

#### Scenario: Naive timestamp
- **WHEN** a user passes `--expire 2026-12-01T00:00:00`
- **THEN** the CLI SHALL fail with "Absolute expiration must include a timezone offset"
- **AND** relative durations such as 7d, 12h and 30m SHALL be accepted

#### Scenario: Copy is unsupported
- **WHEN** `api-keys copy` is run
- **THEN** it SHALL exit with code 1 and print "API key values are only shown at creation. Create a replacement key and revoke the old one."

### Requirement: Webhooks
`sinx cloud webhooks` SHALL provide `register NAME --provider [--credential-id] [--enforce-schema] [--expected-schema JSON]`, `list`, `show`, `delete`, `toggle UUID --active/--inactive` and `public-url UUID`. (src: cli:webhooks.py; sdk:webhooks.py:27-29)

#### Scenario: Deactivate webhook
- **WHEN** a user runs `sinx cloud webhooks toggle <id> --inactive`
- **THEN** the SDK SHALL send `PATCH /api/v1/webhook_integrations/{id}` with `{is_active: false}`

#### Scenario: Public URL
- **WHEN** `public-url <id>` is run
- **THEN** it currently prints only the relative path `/api/v1/public/webhooks/{id}`, with no host

### Requirement: Webhook trigger signing
Public webhook triggers SHALL be signed with HMAC-SHA256 over `"{ts}." + body`, sent in a header of the form `t=..,v1=..`. (src: sdk:webhooks.py:88-110)

#### Scenario: Signed trigger
- **WHEN** `PublicWebhooksResource.trigger_webhook` sends a payload
- **THEN** the signature header SHALL contain the timestamp and the HMAC-SHA256 digest

### Requirement: Private package index login
`sinx cloud packages login [--registry] [--key-env VAR] [--cloud-url]` SHALL authenticate uv against an allow-listed Sinapsis registry using uv native credential storage, with no plaintext fallback. It SHALL also provide `logout` and `indexes`. (src: cli:packages.py:26-135)

#### Scenario: Allowed registries
- **WHEN** a registry is chosen
- **THEN** `sinapsis-dependencies` SHALL map to https://pypi.sinapsis.tech
- **AND** `sinapsis-community` (the default) SHALL map to https://community.pypi.sinapsis.tech
- **AND** `sinapsis-internal` SHALL map to https://internal.pypi.sinapsis.tech

#### Scenario: Key issuance and storage
- **WHEN** no `--key-env` is given
- **THEN** a key named `uv:{registry}` with scope `packages:read` SHALL be issued
- **AND** the key SHALL match `sk_[A-Za-z0-9_-]{8,192}` and SHALL be verified with an 8 s timeout
- **AND** it SHALL be stored with `uv auth login <host> --token -`, with a 30 s timeout

#### Scenario: Unknown registry
- **WHEN** a user runs `sinx cloud packages login --registry other`
- **THEN** the CLI SHALL fail with "Unknown Sinapsis registry"
