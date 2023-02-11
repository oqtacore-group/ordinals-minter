from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
import uvicorn

from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory='templates')

app.mount('/assets', StaticFiles(directory='assets'), name='assets')


@app.get('/')
def index(req: Request):
    context = {
        'request': req,
    }
    return templates.TemplateResponse('index.html', context)


@app.get('/order/{order_uuid}')
def order(req: Request, order_uuid: str):
    context = {
        'request': req,
        'order_uuid': order_uuid,
    }
    return templates.TemplateResponse('order.html', context)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=1337, workers=1)