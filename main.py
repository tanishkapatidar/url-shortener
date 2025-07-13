from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, HttpUrl, PrivateAttr
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, Form
import uvicorn
import os
from dotenv import load_dotenv
import random
import string
import psycopg2
load_dotenv()

BASEURL = os.getenv("BASE_URL")
DATABASE = os.getenv("DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

if BASEURL is None:
    raise ValueError("BASEURL is not set in the .env file")

def connection():
    conn = psycopg2.connect(
        database = DATABASE, user = DB_USER, password = DB_PASSWORD, host = DB_HOST, port = DB_PORT, 
    )
    print("Connection Created Successfully")
    return conn


conn= connection()
cursor = conn.cursor()

# Define the SQL query for creating a new table
create_table_query = '''
CREATE TABLE IF NOT EXISTS url_shortener.shortenedUrl (
    id VARCHAR(255),
    longUrl VARCHAR(255));'''
try:
    # Execute the SQL query
    cursor.execute(create_table_query)
    
    # Commit the transaction
    conn.commit()
    print("Table created successfully")
except Exception as error:
    print(f"Error occurred: {error}")
    conn.rollback()
finally:
    # Close the cursor and connection
    cursor.close()
    conn.close()


def generate_id():
    # Define the character pool (digits, lowercase letters, uppercase letters)
    characters = string.digits + string.ascii_lowercase + string.ascii_uppercase
    
    id = ''.join(random.choices(characters,k=4))
    return id

def save(id, longUrl):

    conn= connection()
    cursor= conn.cursor()

    cursor.execute(""" INSERT INTO url_shortener.shortenedUrl(id,longUrl)
    VALUES(%s,%s);""",(id,longUrl))
    conn.commit()
    cursor.close()
    conn.close()

def getLongUrl(id):
    conn= connection()
    cursor= conn.cursor()
    cursor.execute("""SELECT shortenedUrl.longUrl FROM url_shortener.shortenedUrl WHERE id = %s """,(id,))
    response = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    return response

def checkIfExist(longUrl):
    conn= connection()
    cursor= conn.cursor()
    cursor.execute("""SELECT shortenedUrl.id FROM url_shortener.shortenedUrl WHERE longUrl = %s """,(longUrl,))
    response = cursor.fetchone()
    print(response)
    conn.commit()
    cursor.close()
    conn.close()
    return response


def Shortener(longUrl):
    isUrlExist = checkIfExist(longUrl)
    if not isUrlExist:
        id = generate_id() 
    else :
        return  BASEURL + isUrlExist[0]
        

    if not id:
        raise ValueError("Generated ID is empty or None")
    save(id,longUrl)
    print('url saved')
    url = BASEURL + id
    return url

class Validation(BaseModel):
    url: HttpUrl

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <-- your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/{shortUrl}")
def fetchUrl(shortUrl:str):
    longUrl = getLongUrl(shortUrl)
    if not longUrl:
        return {"error": "Invalid short link"}
    return RedirectResponse(url=longUrl[0])


@app.post("/")
def url_shortner(longUrl:str = Form("")):
    valid_url = Validation(url = longUrl)
    valid_url = str(valid_url.url)
    res = Shortener(longUrl)
    
    if isinstance(res,str):
        msg= "Your URL shortened successfully"
        print("req_url:",{res})
    else:
        print("Error:",{res})
    return {"text":res}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)