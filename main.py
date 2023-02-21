import copy
import decimal
import json
import os
import time
from typing import Optional
import uuid
import aiofiles
from fastapi import FastAPI, Form, Request, UploadFile, status, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import sqlmodel
import uvicorn

from fastapi.templating import Jinja2Templates

from app.database import MintOrder, get_db
from app.ordwrapper import OrdWrapper
from app.settings import MAX_FILESIZE_BYTES, MIN_WEI_VALUE, RECEIVER_ETH_ADDR, TG_ALERTS_CHANNEL
from app.shared.telegram import tg_send_message
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


@app.get('/api/estimate_price')
async def estimate_price_route(filesize_bytes: int, fee_rate: int):
    ord_wrapper = OrdWrapper()
    try:
        res = ord_wrapper.estimate_price(filesize_bytes, fee_rate)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f'Error: {e}')

    return res


@app.post('/api/orders')
async def order(
    file: UploadFile,
    tx_hash: str = Form(),
    sender_wallet_addr: str = Form(),
    value_wei: str = Form(),
    receiver_btc_addres: Optional[str] = Form(''),
):
    order_uuid = str(uuid.uuid4())

    value_wei_decimal = decimal.Decimal(value_wei)
    if value_wei_decimal < MIN_WEI_VALUE:
        raise HTTPException(status_code=400, detail='Value too small')

    if file.size > MAX_FILESIZE_BYTES:
        raise HTTPException(status_code=400, detail='File too big')

    with get_db() as db:
        existing_order = db.exec(
            sqlmodel
            .select(MintOrder)
            .where(MintOrder.tx_hash == tx_hash)
        ).first()
        if existing_order is not None:
            raise HTTPException(status_code=400, detail='Order already exist')

        order = MintOrder(
            order_uuid=order_uuid,
            created_ts=time.time(),
            tx_hash=tx_hash,
            filename=file.filename,
            sender_eth_addr=sender_wallet_addr,
            receiver_eth_addr=RECEIVER_ETH_ADDR,
            value_wei=value_wei,
            receiver_btc_addres=receiver_btc_addres,
            status='CHECKING_PAYMENT',
        )
        order_filepath = order.filepath

        order_dict = copy.deepcopy(order.__dict__)
        order_dict.pop('_sa_instance_state')
        order_json = json.dumps(order_dict, ensure_ascii=False, sort_keys=True, indent=2)
        r = tg_send_message(f'<b>New order</b>\n\n<code>{order_json}</code>', TG_ALERTS_CHANNEL)

        db.add(order)
        db.commit()

    start_checking_order(order_uuid)

    os.makedirs('./storage', exist_ok=True)
    async with aiofiles.open(order_filepath, 'wb') as out_file:
        while content := await file.read(1024):
            await out_file.write(content)

    return RedirectResponse(
        f'/orders/{order_uuid}',
        status_code=status.HTTP_302_FOUND,
    )


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=1337, workers=1)
