import contextlib
import dataclasses
import datetime
import json
import pathlib
from typing import Optional

import sqlmodel

from app.settings import DB_URL

engine = sqlmodel.create_engine(
    DB_URL,
    connect_args={'check_same_thread': False},
)


@contextlib.contextmanager
def get_db() -> sqlmodel.Session:
    """Yield db session."""
    sqlmodel.SQLModel.metadata.create_all(engine)
    with sqlmodel.Session(engine) as sess:
        sess.execute('PRAGMA journal_mode=WAL;')
        yield sess


@dataclasses.dataclass
class MintOrder(sqlmodel.SQLModel, table=True):
    """Class to represent customer order to mint file."""

    order_uuid: str = sqlmodel.Field(primary_key=True, default=False)
    created_ts: int
    tx_hash: str
    filename: str
    sender_eth_addr: str
    receiver_eth_addr: str
    value_wei: str
    receiver_btc_addres: str
    status: str
    ord_stdout: Optional[str] = None

    @property
    def filepath(self) -> str:
        rel_path = f'./storage/{self.tx_hash}_{self.filename}'
        return pathlib.Path(rel_path).absolute()

    @property
    def reveal_tx_url(self) -> str:
        tx_hash = json.loads(self.ord_stdout)['reveal']
        return f'https://mempool.space/tx/{tx_hash}'

    @property
    def ordinals_url(self) -> str:
        insctiption_id = json.loads(self.ord_stdout)['inscription']
        return f'https://ordinals.com/inscription/{insctiption_id}'

    @property
    def created(self) -> datetime.datetime:
        """Return datetime"""

    def is_transaction_done(self):
        """Check if transaction is mined."""

    def get_mint_status(self) -> str:
        """Return status of minting file related to current order."""
