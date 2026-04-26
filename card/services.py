from smartcard.System import readers
from smartcard.CardConnection import CardConnection
from smartcard.pcsc.PCSCReader import PCSCReader
from .apdu import (
    GET_UID, LOAD_KEY, AUTHENTICATE, READ_BLOCK, WRITE_BLOCK,
    KEY_A, SLOT_0, DEFAULT_KEY, SW_SUCCESS
)


class CardException(Exception):
    pass


class CardService:
    def __init__(self):
        self.connection: CardConnection = None
    
    def get_readers(self) -> list:
        return readers()

    def connect(self, reader_index: int = 0) -> str:
        r = self.get_readers()
        if not r:
            raise CardException("No reader found")
        reader: PCSCReader = r[reader_index]
        self.connection = reader.createConnection()
        self.connection.connect()
        return str(reader)
    
    def disconnect(self):
        if self.connection:
            self.connection.disconnect()
            self.connection = None
    
    def reconnect(self):
        if self.connection:
            self.connection.disconnect()
        self.connection.connect()
    
    def _transmit(self, apdu: list) -> tuple[list, int, int]:
        pass
    
    def _check_sw(self, sw1: int, sw2: int, error_msg: str):
        if (sw1, sw2) != SW_SUCCESS:
            raise CardException(f"{error_msg}: {sw1:02X} {sw2:02X}")
    
    def get_uid(self):
        data, sw1, sw2 = self._transmit(GET_UID)
        self._check_sw(sw1, sw2, "Failed to get UID")
    
    def load_key(self, key: list = DEFAULT_KEY):
        apdu = LOAD_KEY + key
        data, sw1, sw2 = self._transmit(apdu)
        self._check_sw(sw1, sw2, "Failed to load key")
    
    def authenticate(self, block: int, key_type: int = KEY_A, slot: int = SLOT_0):
        apdu = AUTHENTICATE + [block, key_type, slot]
        data, sw1, sw2 = self._transmit(apdu)
        self._check_sw(sw1, sw2, f"Authentication failed for block {block}")
    
    def read_block(self, block: int) -> list:
        apdu = READ_BLOCK + [block, 0x10]
        data, sw1, sw2 = self._transmit(apdu)
        self._check_sw(sw1, sw2, f"Failed to read block {block}")
        return data
    
    def write_block(self, block: int, data: list):
        if len(data) != 16:
            raise CardException("Data must be exactly 16 bytes")
        
        apdu = WRITE_BLOCK + [block, 0x10] + data
        _, sw1, sw2 = self._transmit(apdu)
        self._check_sw(sw1, sw2, f"Failed to write to block {block}")

    def dump_card(self, sector_keys: dict = None) -> dict:
        dump = {}
        for sector in range(16):
            self.reconnect()
            key = sector_keys.get(sector, DEFAULT_KEY) if sector_keys else DEFAULT_KEY
            first_block = sector * 4
            try:
                self.load_key(key)
                self.authenticate(first_block)
                blocks = {}
                for block in range(4):
                    block_number = first_block + block
                    data = self.read_block(block_number)
                    blocks[block] = {
                        'data': data,
                        'hex': ' '.join(f'{b:02X}' for b in data),
                        'is_trailer': block == 3
                    }
                dump[sector] = {
                    'status': 'ok',
                    'blocks': blocks
                }
            except CardException as e:
                dump[sector] = {
                    'status': 'error',
                    'error': str(e),
                    'blocks': {}
                }
        return dump 