from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, HttpUrl, PrivateAttr

from fastapi import FastAPI, Form
import uvicorn
import os
from dotenv import load_dotenv
import random
import string
import psycopg2
load_dotenv()
BASEURL = os.getenv("baseUrl")

def connection():
    conn = psycopg2.connect(
        database = "bodhi", user = "postgres", password = "password", host = "localhost", port ="5432"
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


def Shortener(longUrl):
    id = generate_id()
    save(id,longUrl)
    url = BASEURL + id
    return url

class Validation(BaseModel):
    url: HttpUrl

app = FastAPI()

@app.get("/{shortUrl}")
def fetchUrl(shortUrl:str):
    longUrl = getLongUrl(shortUrl)
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
    uvicorn.run("new_main:app", host="127.0.0.1", port=8000, reload=True)