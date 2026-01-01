# Identity & Access Management Service (`auth-service`)

## 📖 Overview
The **Auth Service** is the security backbone of Anomalyze. It has two distinct responsibilities:
1.  **Identity Synchronization**: Syncing human user identities from **Clerk** to our local database via webhooks.
2.  **Machine Access Control**: Managing the lifecycle of **API Keys** for programmatic access (Ingestion API).

It strictly separates **Identity** (Who you are - handled by Clerk) from **Access** (What you can do - handled by API Keys & Roles).

## 🏗 Architecture
- **Identity Provider**: Clerk (Handles Login, Signup, MFA, Session Management).
- **Database**: Postgres (`users`, `api_keys`, `audit_logs`).
- **Security**:
    - API Keys are stored as **bcrypt hashes**.
    - Keys are never shown again after creation.
    - Scoped permissions (`ingest:write`, `analytics:read`).

## 🔌 API Reference

### 1. Clerk Webhooks (Identity Sync)
**Endpoint**: `POST /webhooks/clerk`
- **Security**: Verifies `Svix` signature headers.
- **Description**: Receives events from Clerk to keep local `users` table in sync.
- **Handled Events**:
    - `user.created`: Insert into `users` table.
    - `user.updated`: Update email/name.
    - `user.deleted`: Soft delete user & revoke all API keys.

### 2. API Key Management (Machine Access)

#### Create API Key
**Endpoint**: `POST /v1/api-keys`
- **Auth**: Clerk JWT (User must be logged in).
- **Body**:
  ```json
  {
    "name": "Production Server 1",
    "scopes": ["ingest:write", "alerts:read"],
    "expires_in_days": 90
  }
  ```
- **Response**:
  ```json
  {
    "key_id": "key_12345",
    "secret": "sk_live_8374...", // ⚠️ SHOWN ONLY ONCE
    "prefix": "sk_live_8374",
    "scopes": ["ingest:write"]
  }
  ```

#### List API Keys
**Endpoint**: `GET /v1/api-keys`
- **Response**: Returns metadata (ID, name, prefix, created_at, last_used_at). **No secrets.**

#### Rotate API Key
**Endpoint**: `POST /v1/api-keys/:id/rotate`
- **Description**: Invalidates the old key and generates a new secret for the same ID/Scopes.
- **Use Case**: Key compromise or routine security rotation.

#### Revoke API Key
**Endpoint**: `DELETE /v1/api-keys/:id`
- **Description**: Immediately blocks access for this key.

### 3. Internal Validation (Middleware Support)
**Endpoint**: `POST /internal/validate-key`
- **Description**: Used by Ingestion Service to validate an incoming `x-api-key`.
- **Body**: `{ "key": "sk_live_..." }`
- **Response**:
  ```json
  {
    "valid": true,
    "user_id": "user_abc",
    "scopes": ["ingest:write"],
    "rate_limit_tier": "PRO"
  }
  ```

## 🗄 Database Schema (Prisma Snippet)
```prisma
model ApiKey {
  id          String   @id @default(uuid())
  userId      String
  name        String
  keyPrefix   String   // First 7 chars for identification
  keyHash     String   // Bcrypt hash of the full key
  scopes      String[] // ["ingest:write", "read:all"]
  lastUsedAt  DateTime?
  expiresAt   DateTime?
  createdAt   DateTime @default(now())
  isRevoked   Boolean  @default(false)
}
```

## 🛡 Security Best Practices
1.  **Hashing**: We store `bcrypt(api_key)`, never the plain text.
2.  **Prefixing**: Keys look like `sk_live_...` to make them detectable by secret scanners.
3.  **Least Privilege**: Scopes restrict what a key can do.
