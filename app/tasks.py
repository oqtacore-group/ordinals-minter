import decimal
import json
import time

import sqlmodel

from huey import SqliteHuey, crontab
from huey.exceptions import RetryTask
from web3 import Web3

from app.database import MintOrder, get_db
from app.ordwrapper import OrdWrapper, OrdWrapperMock
from app.settings import ETH_RPC_URL, FEE_RATE, RECEIVER_ETH_ADDR, TG_ALERTS_CHANNEL
from app.shared.currencies import eth_to_wei, sat_to_usd, usd_to_eth
from app.shared.telegram import tg_send_message

web3 = Web3(Web3.HTTPProvider(ETH_RPC_URL))
huey = SqliteHuey(filename='huey.db')


import functools

def exp_backoff_task(retries=10, retry_backoff=1.15, retry_delay=15):
    def deco(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            # We will register this task with `context=True`, which causes
            # Huey to pass the task instance as a keyword argument to the
            # decorated task function. This enables us to modify its retry
            # delay, multiplying it by our backoff factor, in the event of
            # an exception.
            task = kwargs.pop('task')
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                task.retry_delay *= retry_backoff
                raise exc

        # Register our wrapped task (inner()), which handles delegating to
        # our function, and in the event of an unhandled exception,
        # increases the retry delay by the given factor.
        return huey.task(
            retries=retries,
            retry_delay=retry_delay,
            context=True
        )(inner)
    return deco


@exp_backoff_task()
def start_checking_order(order_uuid):
    with get_db() as db:
        order = db.exec(
            sqlmodel
            .select(MintOrder)
            .where(MintOrder.order_uuid == order_uuid)
        ).first()
        if not order:
            raise Exception('Order not created yet')

        txn = web3.eth.get_transaction(order.tx_hash)
        print(txn)

        # TODO: Check wei size
        txn_receipt = web3.eth.get_transaction_receipt(order.tx_hash)
        is_mined = (txn_receipt['status'] == 1)
        print(txn_receipt)
        print(f'{is_mined = }')

        if txn['from'].lower() != order.sender_eth_addr.lower():
            order.status = 'ERROR_WRONG_FROM_ADDR'
            db.add(order)
            db.commit()
            return False

        if txn['to'].lower() != RECEIVER_ETH_ADDR.lower():
            order.status = 'ERROR_WRONG_TO_ADDR'
            db.add(order)
            db.commit()
            return False

        if is_mined:
            ord_wrapper = OrdWrapper()
            ord_wrapper.index()

            # XXX: Check that price is profitable for us, in case of errors add gap of 1$
            one_usd_in_wei = eth_to_wei(usd_to_eth(1))
            prices = ord_wrapper.estimate_price(order.filesize_bytes, order.fee_rate)
            if decimal.Decimal(txn['value']) < decimal.Decimal(prices['total_price_wei']) + one_usd_in_wei:
                order.status = 'ERROR_SMALL_WEI'
                db.add(order)
                db.commit()
                print(order, prices)
                return False

            try:
                stdout = json.dumps(ord_wrapper.inscribe(order.filepath, fee_rate=order.fee_rate))
                status = 'MINT_STARTED'
            except Exception as e:
                stdout = str(e)
                status = 'MINT_ERROR'

            order.ord_stdout = stdout
            order.status = status

            db.add(order)
            db.commit()

            if status == 'MINT_ERROR':
                order_dict = order.__dict__
                order_dict.pop('_sa_instance_state')
                order_json = json.dumps(order_dict, ensure_ascii=False, sort_keys=True, indent=2)
                r = tg_send_message(f'<b>Error</b>\n\n<code>{order_json}</code>', TG_ALERTS_CHANNEL)

            # Send message to telegram with money left on BTC wallet
            sat_balance = ord_wrapper.get_balance()['cardinal']
            usd_balance = sat_to_usd(sat_balance)
            message = f'<b>Money left on BTC wallet</b>\n\nBalance: {usd_balance:.2f}$'
            r = tg_send_message(message, TG_ALERTS_CHANNEL)

    return True


@huey.periodic_task(crontab(minute='*/15'))  # Every 15 mins
def background_ord_reindexed():
    ord_wrapper = OrdWrapper()
    ord_wrapper.index()
