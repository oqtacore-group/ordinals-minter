import decimal
import json
import subprocess
import tempfile
import time

from app.shared.currencies import eth_to_wei, sat_to_usd, usd_to_eth


class OrdWrapper(object):

    def __init__(self, config='/home/ubuntu/.bitcoin/bitcoin.conf', wallet='test2'):
        self.config = config
        self.wallet = wallet

    def inscribe(self, filepath: str, fee_rate: int=15, dry_run: bool=False):
        command = ['wallet', 'inscribe', '--fee-rate', str(fee_rate), filepath]
        if dry_run:
            command = ['wallet', 'inscribe', '--dry-run', '--fee-rate', str(fee_rate), filepath]

        proc = self._run_command(command)
        message = f'stdout: {proc.stdout = }\n{proc.stderr = }'
        print(message, flush=True)

        try:
            res = json.loads(proc.stdout)
        except:
            raise Exception(message)

        return res

    def estimate_price(self, filesize_bytes: int, fee_rate: int) -> dict:
        if filesize_bytes > 1024 * 1024 * 5:  # 5mb = 5 * 1024kb
            raise Exception('File too big, use filesize under 5mb')

        with tempfile.NamedTemporaryFile(suffix='.txt') as tmp:
            # Create file of given size
            for _ in range(filesize_bytes):
                tmp.write(b'a')
            tmp.flush()

            try:
                sat_price = self._estimate_file_sat_price(tmp.name, fee_rate)
            except:
                sat_price = int(filesize_bytes / 3.7 * fee_rate)
            usd_price = sat_to_usd(sat_price)
            eth_price = usd_to_eth(usd_price)
            wei_price = eth_to_wei(eth_price)

            service_fee_usd = usd_price * decimal.Decimal(0.1) + decimal.Decimal(5)
            total_price_eth = usd_to_eth(usd_price + service_fee_usd)
            total_price_wei = eth_to_wei(total_price_eth)

        return {
            'bytes': filesize_bytes,
            'fee_rate': fee_rate,
            'sat': sat_price,
            'usd': usd_price,
            'eth': eth_price,
            'wei': wei_price,
            'service_fee_usd': service_fee_usd,
            'total_price_wei': total_price_wei,
        }

    def get_balance(self):
        proc = self._run_command(['wallet', 'balance'])

        return json.loads(proc.stdout)

    def index(self):
        proc = self._run_command(['index'])
        return proc

    def _estimate_file_sat_price(self, filepath: str, fee_rate: int=15):
        self.index()
        res = self.inscribe(filepath, fee_rate, dry_run=True)
        satoshi_fees = decimal.Decimal(res['fees'])
        return satoshi_fees

    def _run_command(self, command: list[str]):
        args = ['ord', '--config', self.config, '--wallet', self.wallet] + command
        proc = subprocess.run(args, capture_output=True, text=True)

        return proc


class OrdWrapperMock(OrdWrapper):
    def index(self):
        time.sleep(5)

    def inscribe(self, filepath: str, fee_rate: int=10):
        return {'commit': 'a6c8bc0feb6688f2c6f8b5354ccf14d25e180c51fe1a4cc6787ad56820d080c8', 'inscription': 'b7c33f003f32efd21be6fc905501067f8117fbee4274ff7902661359b4cf73cbi0', 'reveal': 'b7c33f003f32efd21be6fc905501067f8117fbee4274ff7902661359b4cf73cb', 'fees': 2920}

    def get_balance(self):
        return {'cardinal': 473272}


if __name__ == '__main__':
    ord_wrapper = OrdWrapper()

    index = ord_wrapper.index()
    print(index)

    bal = ord_wrapper.get_balance()
    print(bal)

    inscribtion = ord_wrapper.inscribe('/home/ubuntu/test.txt')
    print(inscribtion)
