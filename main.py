import copy
import decimal
import json
import os
import pathlib
import time
from typing import Optional
import uuid
import aiofiles
from fastapi import FastAPI, Form, Request, UploadFile, status, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import requests
import sqlmodel
import uvicorn

from fastapi.templating import Jinja2Templates
from app.compress import compress_file

from app.database import MintOrder, get_db
from app.ordwrapper import OrdWrapper
from app.settings import FEE_RATE, MAX_FILESIZE_BYTES, MIN_WEI_VALUE, RECEIVER_ETH_ADDR, SERVER_PORT, TG_ALERTS_CHANNEL
from app.shared.mempool import get_fee_rates
from app.shared.telegram import tg_send_message
from app.tasks import start_checking_order

app = FastAPI()
templates = Jinja2Templates(directory='templates')

app.mount('/assets', StaticFiles(directory='assets'), name='assets')


@app.get('/')
def index(req: Request, embed: bool = False):
    fee_rates = get_fee_rates()

    context = {
        'request': req,
        'embed': embed,
        'fees': fee_rates,
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


@app.post('/orders/{order_uuid}')
def update_order_btc_addr(
    order_uuid: str,
    receiver_btc_addres: str = Form(),
):
    with get_db() as db:
        order = db.exec(
            sqlmodel
            .select(MintOrder)
            .where(MintOrder.order_uuid == order_uuid)
            .where(MintOrder.receiver_btc_addres == '')
        ).first()

        if order:
            order.receiver_btc_addres = receiver_btc_addres
            r = tg_send_message(
                f'<b>Wallet Added</b>\n\nWallet <code>{receiver_btc_addres}</code> were added to order <code>{order_uuid}</code>',
                TG_ALERTS_CHANNEL,
            )
            db.add(order)
            db.commit()

    return RedirectResponse(
        f'/orders/{order_uuid}',
        status_code=status.HTTP_302_FOUND,
    )


@app.get('/api/estimate_price')
async def estimate_price_route(filesize_bytes: int, fee_rate: int):
    ord_wrapper = OrdWrapper()
    try:
        res = ord_wrapper.estimate_price(filesize_bytes, fee_rate)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f'Error: {e}')

    return res


@app.post('/api/files')
async def estimate_price_route(file: UploadFile):
    # Save file to disk
    os.makedirs('./storage', exist_ok=True)
    order_filepath = pathlib.Path(f'./storage/{uuid.uuid4()}_{file.filename}')
    async with aiofiles.open(order_filepath, 'wb') as out_file:
        while content := await file.read(1024):
            await out_file.write(content)

    compressed_filepath = compress_file(order_filepath)

    compressed_filesize_bytes = os.path.getsize(compressed_filepath)
    compress_pct = round(100 * compressed_filesize_bytes / file.size, 2)

    return {
        'filepath': order_filepath,
        'compressed_filepath': compressed_filepath,
        'filesize_bytes': file.size,
        'compressed_filesize_bytes': compressed_filesize_bytes,
        'compress_pct': compress_pct,
    }


@app.post('/api/orders')
async def order(
    file: UploadFile,
    optimize: Optional[bool] = Form(False),
    tx_hash: str = Form(),
    fee_rate: int = Form(),
    sender_wallet_addr: str = Form(),
    value_wei: str = Form(),
    receiver_btc_addres: Optional[str] = Form(''),
    email: Optional[str] = Form(''),
):
    order_uuid = str(uuid.uuid4())

    if file.size > MAX_FILESIZE_BYTES:
        raise HTTPException(status_code=400, detail='File too big')

    # Save file to disk
    os.makedirs('./storage', exist_ok=True)
    order_filepath = pathlib.Path(f'./storage/{tx_hash}_{file.filename}')
    async with aiofiles.open(order_filepath, 'wb') as out_file:
        while content := await file.read(1024):
            await out_file.write(content)

    final_filename = order_filepath.name
    if optimize:
        final_filename = str(compress_file(order_filepath).name)

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
            filename=final_filename,
            optimize=optimize,
            sender_eth_addr=sender_wallet_addr,
            receiver_eth_addr=RECEIVER_ETH_ADDR,
            value_wei=value_wei,
            receiver_btc_addres=receiver_btc_addres,
            email=email,
            status='CHECKING_PAYMENT',
            filesize_bytes=file.size,
            fee_rate=fee_rate,
        )

        order_dict = copy.deepcopy(order.__dict__)
        order_dict.pop('_sa_instance_state')
        order_json = json.dumps(order_dict, ensure_ascii=False, sort_keys=True, indent=2)
        r = tg_send_message(f'<b>New order</b>\n\n<code>{order_json}</code>', TG_ALERTS_CHANNEL)

        db.add(order)
        db.commit()

    start_checking_order(order_uuid)
    return RedirectResponse(
        f'/orders/{order_uuid}',
        status_code=status.HTTP_302_FOUND,
    )


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=SERVER_PORT, workers=1)
