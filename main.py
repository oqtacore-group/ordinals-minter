import os
import time
import uuid
import aiofiles
from fastapi import FastAPI, Form, Request, UploadFile, status, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import sqlmodel
import uvicorn

from fastapi.templating import Jinja2Templates

from app.database import MintOrder, get_db
from app.settings import RECEIVER_ETH_ADDR
from app.tasks import start_checking_order

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
    with get_db() as db:
        order = db.exec(
            sqlmodel
            .select(MintOrder)
            .where(MintOrder.order_uuid == order_uuid)
        ).first()

    if not order:
        raise HTTPException(status_code=404, detail='Order not found')

    context = {
        'request': req,
        'order_uuid': order_uuid,
        'order': order,
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
    order_uuid = str(uuid.uuid4())

    with get_db() as db:
        order = MintOrder(
            order_uuid=order_uuid,
            created_ts=time.time(),
            tx_hash=tx_hash,
            filename=file.filename,
            sender_eth_addr=sender_wallet_addr,
            receiver_eth_addr=RECEIVER_ETH_ADDR,
            value_wei=value_wei,
            receiver_btc_addres=receiver_btc_addres,
            status='WAIT_MINTING',
        )
        db.add(order)
        db.commit()

    start_checking_order(order_uuid)

    os.makedirs('./storage', exist_ok=True)
    filepath = f'./storage/{tx_hash}_{file.filename}'
    async with aiofiles.open(filepath, 'wb') as out_file:
        while content := await file.read(1024):
            await out_file.write(content)

    return RedirectResponse(
        f'/orders/{order_uuid}',
        status_code=status.HTTP_302_FOUND,
    )


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=1337, workers=1)
