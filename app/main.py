from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import customer, chat, legacy_trigger

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  #  Vue.js frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(customer.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(legacy_trigger.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Pelephone Customer Service API"}
