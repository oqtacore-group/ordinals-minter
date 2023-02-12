import os
import uuid
from fastapi import FastAPI, Form, Request, UploadFile, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
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


@app.get('/orders/{order_uuid}')
def order(req: Request, order_uuid: str):
    context = {
        'request': req,
        'order_uuid': order_uuid,
    }
    return templates.TemplateResponse('order.html', context)


@app.post('/api/orders')
async def order(
    file: UploadFile,
    tx_hash: str = Form(),
    sender_wallet_addr: str = Form(),
    value_wei: str = Form(),
    receiver_btc_addres: str = Form(),
):
    # TODO: Save timestamp
    # TODO: Save order to database
    order_uuid = str(uuid.uuid4())

    filename = file.filename
    with open(f'./storage/{filename}', 'w', encoding='utf-8') as file:
        file.write(receiver_btc_addres)

    return RedirectResponse(
        f'/orders/{order_uuid}',
        status_code=status.HTTP_302_FOUND,
    )


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=1337, workers=1)
