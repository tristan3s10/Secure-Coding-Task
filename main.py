
import logging, os, traceback
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from . import models, schemas
from .auth import authenticate_user, create_access_token, get_current_user, hash_password
from .routers import transactions, users

# --- Logging setup ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logger = logging.getLogger("secure_api")
logger.setLevel(LOG_LEVEL)
fh = logging.FileHandler("app.log")
fh.setLevel(LOG_LEVEL)
formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)

app = FastAPI(title="Secure Transactions API", version="1.0.0")

# --- Database init and admin seeding ---
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    # Seed an initial admin if none exists
    from sqlalchemy.orm import Session as _Session
    db: _Session = next(get_db())
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        existing_admin = db.query(models.User).filter(models.User.email == admin_email).first()
        if not existing_admin:
            admin = models.User(
                email=admin_email,
                hashed_password=hash_password(admin_password),
                role=models.RoleEnum.admin
            )
            db.add(admin)
            db.commit()
            logger.info("Seeded default admin user %s", admin_email)
    finally:
        db.close()

# --- Global exception handling ---
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log detailed error server-side
    logger.error("Unhandled error: %s\n%s", str(exc), traceback.format_exc())
    # Return generic message to avoid information leakage
    return JSONResponse(status_code=500, content={"detail": "An error occurred"})

# --- Health & XSS demo endpoint ---
@app.get("/health", response_class=PlainTextResponse, tags=["system"])
def healthcheck():
    # Returns plain text, explicitly not HTML, demonstrating XSS-safe response.
    return "OK"

# --- Auth ---
@app.post("/token", response_model=schemas.Token, tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # Do not reveal whether email exists
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=user.email, role=user.role.value)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/whoami", response_model=schemas.UserOut, tags=["auth"])
def whoami(current_user: models.User = Depends(get_current_user)):
    return current_user

# --- Routers ---
app.include_router(transactions.router)
app.include_router(users.router)
