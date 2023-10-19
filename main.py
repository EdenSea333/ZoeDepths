from fastapi import FastAPI, Request, Depends, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
import gradio as gr
from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException
from fastapi.responses import RedirectResponse
import requests

from gradio_im_to_3d import set_user_information

from app import init

SECRET = "cf75e1901d98eabb0ae7c63e0163059c2b5026ab4b50a8af"
manager = LoginManager(SECRET, '/authenticate')
app = FastAPI()

def get_user_credit(id):
    id=id
    url = f"https://aianimationstg.wpengine.com/wp-json/customapi/v1/user-credit/{id}"
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
    response = requests.get(url, headers=headers)
    credit_information = response.json()
    print("abc", credit_information)
    free = credit_information[0]['free_count']
    premium = credit_information[0]['premium_count']
    set_user_information(id, free, premium)
    

def get_wordpress_users(username, password):
    url = f"https://aianimationstg.wpengine.com/wp-json/wp/v2/users/me"
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
    response = requests.get(url, headers=headers, auth=(username, password))
    user_data=response.json()
    id=user_data['id']
    print("userid =========================",id)
    get_user_credit(id)
    if response.status_code == 200:
         return response.json()
    else:
         return None
    
gr_interface = init()
gradio_app = FastAPI()
gradio_app = gr.mount_gradio_app(gradio_app, gr_interface, "/")    
app.mount("/gradio", gradio_app)     

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post('/authenticate')
def login(data: OAuth2PasswordRequestForm = Depends()):
    email = data.username
    password = data.password

    user = get_wordpress_users(email, password)
    if not user:
        # you can return any response or error of your choice
        raise InvalidCredentialsException

    access_token = manager.create_access_token(
        data={'sub': email}
    )
    return {'access_token': access_token}

@app.get("/")
def index():
    # if manager.get_current_user() is None:
        return RedirectResponse("/login")
    # else:
        # return RedirectResponse("/gradio")
