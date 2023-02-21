import json
import subprocess
import time


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

    def get_balance(self):
        proc = self._run_command(['wallet', 'balance'])

        return json.loads(proc.stdout)

    def index(self):
        proc = self._run_command(['index'])
        return proc

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
