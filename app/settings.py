import decimal
import os

import dotenv

dotenv.load_dotenv()


DB_URL = 'sqlite:///ordinals_minter.db'
#RECEIVER_ETH_ADDR = '0x76e11ec0963db2Af995D5FC1B45Fb2d7b1Ec0890'  # Dev
RECEIVER_ETH_ADDR = '0x1ab373A9791A9D44f6065CA522d22eD0d8eDD3C7'  # Prod
#ETH_RPC_URL = 'http://127.0.0.1:8545'  # Dev
ETH_RPC_URL = 'https://eth.llamarpc.com'  # Prod
MAX_FILESIZE_BYTES = 1024 * 1024 * 5  # 5mb
MIN_WEI_VALUE = decimal.Decimal('15000000000000000')
TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_ALERTS_CHANNEL = os.getenv('TG_ALERTS_CHANNEL')
FEE_RATE = 15  # sat/vByte
