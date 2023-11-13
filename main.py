from fastapi import FastAPI, Depends, Response, status, HTTPException
from database import engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from models import ProductModel
from schemas import ProductSchema, User, UserInDB, Token, TokenData
from database import get_db, Base

app = FastAPI()

origins = [
    "http://8000-coachhallso-fastapiauth-ncq61p1ghmk.ws-us106.gitpod.io",
]

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    print(f"{repr(exc)}")
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)



@app.post("/product")
def create(product: ProductSchema, db:Session = Depends(get_db)):
    new_product = ProductModel(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

# Get
@app.get("/product")
def get(db: Session = Depends(get_db), status_code = status.HTTP_204_NO_CONTENT):
    products = db.query(ProductModel).all()
    return products

@app.get("/product/{id}")
def get_by_id(id:int, db: Session = Depends(get_db), status_code = status.HTTP_204_NO_CONTENT):
    existing_post = db.query(ProductModel).filter(ProductModel.id == id).first()
    if existing_post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"product with id does not exist")

    return existing_post

# Delete
@app.delete("/product/{id}")
def delete(id:int, db: Session = Depends(get_db), status_code = status.HTTP_204_NO_CONTENT):
    delete_post = db.query(models.ProductModel).filter(models.ProductModel.id == id)
    if delete_post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"product with id does not exist")
    else:
        delete_post.delete(synchronize_session=False)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Update
@app.put("/product/{id}")
def update(id:int, product:ProductSchema, db: Session = Depends(get_db), status_code = status.HTTP_204_NO_CONTENT):
    update_post = db.query(models.ProductModel).filter(models.ProductModel.id == id)
    update_post.first()
    if update_post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"product with id does not exist")
    else:
        update_post.update(product.dict(), synchronize_session=False)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)



@app.get("/")
async def get_root():
    return "Hello World"

# to get the key run this command: openssl rand -hex 32
SECRET_KEY = "293bc37dafdbd68e264988cb88aec5a97595d9590bd59617af5894013a63e408"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

db = {
    "jdh": {
        "username": "jdh",
        "full_name": "Justin Hall",
        "email": "jhalljhall@gmail.com",
        "hashed_password": "$2b$12$X/9jkgQEy0HHBADsEhHtG.CRK5Ic/2WFsQ0bmb5rS8DZHUV7O1U8u",
        "status":True
    }
}

pwd_context = CryptContext(schemes="bcrypt", deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_data = db[username]
        return UserInDB(**user_data)

def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False;

    if not verify_password(password, user.hashed_password):
        return False;

    return user

def create_access_token(data:dict, expires_delta:timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate":"Bearer"})

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username:str = payload.get("sub")
        if username is None:
            raise credential_exception
        token_data = TokenData(username=username)

    except JWTError:
        raise 
    
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credential_exception
    
    return user

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if not current_user.status:
        raise HTTPException(status_code=400, detail="Inactive User")
    return current_user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorect user/pass", headers={"WWW-Authenticate":"Bearer"})

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type":"bearer"}

@app.get("/users/me/", response_model=User)
async def read_users_me(current_user:User = Depends(get_current_active_user)):
    return current_user

@app.get("/users/me/items")
async def read_own_items(current_user:User = Depends(get_current_active_user)):
    return [{"item_id":1, "owner": current_user}]

# pw = get_password_hash("jdh1974")
# print(pw)