# Secure-Coding-Task
a simple web application API with user authentication and role-based access

***** REQUIREMENTS****
fastapi==0.115.0
uvicorn[standard]==0.30.6
SQLAlchemy==2.0.36
pydantic==2.9.1
python-jose==3.3.0
bcrypt==4.2.0
***********************

# Secure Transactions API (FastAPI + SQLite + SQLAlchemy)

A production-minded, security-hardened REST API that implements authentication, RBAC, and full CRUD for **transactions**.

## Features
- **FastAPI** with Pydantic v2 for strict input validation
- **bcrypt** password hashing
- **JWT** Bearer authentication (OAuth2 Password flow)
- **RBAC** with two roles: `user` and `admin`
- **SQLite** via **SQLAlchemy ORM** (easily swappable to PostgreSQL/MySQL)
- **Global error handling** with server-side logging
- **XSS-safe** responses (JSON by default; explicit plain text on `/health`)

---

## Quickstart

### 1) Install
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Run
```bash
uvicorn app.main:app --reload
```

On first start, the app seeds a default admin user:
- Email: `admin@example.com`
- Password: `admin123`

**Change these via environment variables before deploying:**
```bash
export ADMIN_EMAIL="secure-admin@yourdomain.com"
export ADMIN_PASSWORD="long-random-password"
export JWT_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 3) Authenticate
Request a token (OAuth2 Password form) at `POST /token`:
```bash
curl -X POST http://127.0.0.1:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"
```
Response:
```json
{"access_token":"<JWT>","token_type":"bearer"}
```
Use this token with `Authorization: Bearer <JWT>` on subsequent requests.

---

## API Endpoints

### Auth
- `POST /token` — Login and receive a JWT access token. **401** on invalid credentials.
- `GET /whoami` — Get the current authenticated user's profile.
- `GET /health` — Plain-text health check (demonstrates non-HTML response to avoid XSS).

### Users
- `POST /users/` — **Admin only.** Create a user.
  - Request body: `email`, `password` (min 8, max 128), `role` in `["user","admin"]`
  - Responses: **201** Created, **409** Conflict if email exists
- `GET /users/me` — Returns the authenticated user profile.

### Transactions
- `POST /transactions/` — Create a transaction for the authenticated user.
  - Body: `amount>0`, `description<=255`, `date` (YYYY-MM-DD)
- `GET /transactions/` — List transactions.
  - **Users** see only their own. **Admins** see all.
  - Optional filters (parameterized & safe): `q` (substring match on description), `min_amount>0`, `max_amount>0`
- `GET /transactions/{tx_id}` — Retrieve one transaction (RBAC enforced).
- `PUT /transactions/{tx_id}` — Update fields (RBAC enforced).
- `DELETE /transactions/{tx_id}` — Delete (RBAC enforced).

---

## Security Choices (and Why)

### bcrypt for Passwords
We use the **bcrypt** library directly:
- `bcrypt.gensalt(rounds=12)` generates a per-password salt.
- `bcrypt.hashpw(password, salt)` stores a salted hash; plaintext password is never stored.
- `bcrypt.checkpw(password, hashed)` safely verifies without exposing timing or data about the salt.
bcrypt is a proven adaptive hashing function; the cost factor (`rounds`) makes brute-force increasingly expensive over time.

### SQL Injection Prevention
- All database access is done via **SQLAlchemy ORM** (`session.query(...).filter(...)`). No raw SQL strings.
- Even when filtering, e.g. `description.contains(q)`, SQLAlchemy builds **parameterized** queries under the hood, avoiding string concatenation in SQL.

### XSS Mitigation
- FastAPI returns **JSON** by default. Browsers do not execute JSON; it is treated as data, not HTML.
- `/health` explicitly returns `text/plain` to demonstrate non-HTML output. We never render client-controlled HTML in responses.

### Strong Input Validation with Pydantic
- Request bodies and query/path parameters are validated by **Pydantic** models.
- Examples: `amount` must be `> 0`, `description` has `max_length=255`, and emails are validated with `EmailStr`.

### RBAC: Principle of Least Privilege
- Roles: `user` and `admin`.
- **Users** can CRUD only their **own** transactions.
- **Admins** can CRUD **any** user's transactions and create users.
- Enforcement is centralized in dependencies and per-endpoint checks.

### Generic Error Messages
- The global exception handler logs detailed stack traces **server-side**.
- Clients receive a generic `{"detail": "An error occurred"}` for unexpected errors to **avoid information leakage**.
- Authentication failures return `401 Invalid credentials` without confirming whether the email exists.

---

## Swap SQLite for PostgreSQL/MySQL
- Change `DATABASE_URL` in `app/database.py` to something like:
  - PostgreSQL: `postgresql+psycopg://user:pass@host:5432/dbname`
  - MySQL: `mysql+pymysql://user:pass@host:3306/dbname`
- Remove `connect_args={"check_same_thread": False}` (SQLite-specific).

---

## Development Notes
- The project avoids raw SQL and uses SQLAlchemy's query API to inherently prevent injection.
- Logging goes to `app.log` in the project root.
- Token expiry is configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`.
- All responses are JSON unless explicitly `text/plain`.

---

## Example: Create a normal user and transact
1. Login as admin, copy token.
2. Create a user:
   ```bash
   curl -X POST http://127.0.0.1:8000/users/ \
     -H "Authorization: Bearer <ADMIN_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"email":"user1@example.com","password":"S3curePass!","role":"user"}'
   ```
3. Login as `user1@example.com` to get a token.
4. Create a transaction:
   ```bash
   curl -X POST http://127.0.0.1:8000/transactions/ \
     -H "Authorization: Bearer <USER_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"amount": 12.5, "description":"Coffee", "date":"2024-01-02"}'
   ```

