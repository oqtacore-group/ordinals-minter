import decimal

DB_URL = 'sqlite:///ordinals_minter.db'
RECEIVER_ETH_ADDR = '0x76e11ec0963db2Af995D5FC1B45Fb2d7b1Ec0890'
ETH_RPC_URL = 'http://127.0.0.1:8545'
MAX_FILESIZE_BYTES = 1024 * 20  # 20kb
MIN_WEI_VALUE = decimal.Decimal('15000000000000000')
