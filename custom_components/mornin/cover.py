"""Mornin as Cover"""

# Import the device class
from homeassistant.components.cover import (
    CoverDevice, PLATFORM_SCHEMA, DEVICE_CLASS_CURTAIN,
    SUPPORT_OPEN, SUPPORT_CLOSE, SUPPORT_STOP
)

# Import constants
# https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/const.py
from homeassistant.const import (
    CONF_API_KEY, CONF_MAC, CONF_NAME, ATTR_DEVICE_CLASS,
    STATE_OPEN, STATE_CLOSED, STATE_OPENING, STATE_CLOSING
)

# Import classes for validation
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

# Import the logger for debugging
import logging

# Define the validation of configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_MAC): cv.string,
    vol.Optional(CONF_NAME): cv.string
})

# Initialize the logger
_LOGGER = logging.getLogger(__name__)

# Define constants
BLE_CONNECT_TIMEOUT_SEC = 15
BLE_CONNECT_MAX_RETRY_COUNT = 5
BLE_READ_TIMEOUT_SEC = 5
APP_SERVICE_STATUS_UUID = '79ab0001-9dfa-4ae2-bd46-ac69d9fdd743'
CONTROL_SERVICE_CONTROL_UUID = '79ab1001-9dfa-4ae2-bd46-ac69d9fdd743'
CONTROL_SERVICE_CONTROL_OPEN_VALUE = b'\x00\x00'
CONTROL_SERVICE_CONTROL_CLOSE_VALUE = b'\x00\x01'
CONTROL_SERVICE_CONTROL_STOP_VALUE = b'\x00\x02'
CONTROL_SERVICE_CONTROL_WAIT_SEC = 5

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup platform."""

    auth_key = config[CONF_API_KEY]
    mac_address = config[CONF_MAC]

    name = config.get(CONF_NAME)

    add_devices([MorninCoverDevice(auth_key, mac_address, name)])

class MorninCoverDevice(CoverDevice):

    def __init__(self, auth_key: str, mac_address: str, name: str) -> None:
        """Initialzing device...."""

        # Import dependencies
        import pygatt
        from time import sleep
        self._ble_adapter = pygatt.GATTToolBackend()
        self._sleep = sleep

        # Initialize
        self._auth_key = auth_key
        self._mac_address = mac_address.upper()
        self._name = name if name != None else mac_address
        self._mornin_device = None
        self._state = None

    @property
    def assumed_state(self) -> bool:
        """Use the assumed state because we can't get the actual status of the curtain."""
        return True

    @property
    def unique_id(self) -> str:
        """Return a unique identifier for this device."""
        return 'mornin_' + self._mac_address

    @property
    def current_cover_position(self) -> int:
        """Return the cover position as unknown."""
        return None

    @property
    def current_cover_tilt_position(self) -> int:
        """Return the cover tilt position as unknown."""
        return None

    @property
    def name(self) -> str:
        """Return the name of device."""
        return self._name

    @property
    def state(self):
        """Return the state of this device."""
        return self._state

    @property
    def device_class(self) -> str:
        """Return the class of this device."""
        return DEVICE_CLASS_CURTAIN

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP

    @property
    def is_opening(self):
        """Return if the cover is opening or not."""
        if (self._state == STATE_OPENING):
            return True
        return False

    @property
    def is_closing(self):
        """Return if the cover is closing or not."""
        if (self._state == STATE_CLOSING):
            return True
        return False

    @property
    def is_closed(self):
        """Return if the cover is closed or not."""
        if (self._state == STATE_CLOSED):
            return True
        elif (self._state == STATE_OPEN):
            return False
        return None

    def open_cover(self, **kwargs) -> None:
        """Open the curtain with using this device."""

        # Connect to device
        if self._connect() == False:
            self._state = None
            return

        # Change the state on Home Assistant
        self._state = STATE_OPENING

        # Control device
        _LOGGER.info('Moving the mornin to open the curtain %s...', self._mac_address)
        self._mornin_device.char_write(CONTROL_SERVICE_CONTROL_UUID, CONTROL_SERVICE_CONTROL_OPEN_VALUE, True)
        self._sleep(CONTROL_SERVICE_CONTROL_WAIT_SEC)

        # Change the state on Home Assistant
        self._state = STATE_OPEN

    def close_cover(self, **kwargs) -> None:
        """Close the curtain with using this device."""

        # Connect to device
        if self._connect() == False:
            self._state = None
            return

        # Change the state on Home Assistant
        self._state = STATE_CLOSING

        # Control the device
        _LOGGER.info('Moving the mornin to close the curtain %s...', self._mac_address)
        self._mornin_device.char_write(CONTROL_SERVICE_CONTROL_UUID, CONTROL_SERVICE_CONTROL_CLOSE_VALUE, True)
        self._sleep(CONTROL_SERVICE_CONTROL_WAIT_SEC)

        # Change the state on Home Assistant
        self._state = STATE_CLOSED

    def stop_cover(self, **kwargs) -> None:
        """Stop the moving of this device."""

        # Connect to device
        if self._connect() == False:
            self._state = None
            return

        # Control the device
        _LOGGER.info('Stopping the mornin %s...', self._mac_address)
        self._mornin_device.char_write(CONTROL_SERVICE_CONTROL_UUID, CONTROL_SERVICE_CONTROL_STOP_VALUE, True)
        self._sleep(CONTROL_SERVICE_CONTROL_WAIT_SEC)

        # Change the state on Home Assistant
        self._state = None

    def _connect(self) -> bool:
        """Connect to this device."""

        # Initialize BLE adapter
        _LOGGER.debug('Initializing BLE adapter...')
        try:
            self._ble_adapter.start(False)
        except Exception as error:
            _LOGGER.debug('Error occurred during initializing: %s; However ignored.', error)

        # Start a loop for retry
        for retry_count in range(0, BLE_CONNECT_MAX_RETRY_COUNT):

            # Disconnect from device if necessary
            self._disconnect()

            # Connect to device
            _LOGGER.debug('Connecting to mornin (%d/%d)... %s', retry_count, BLE_CONNECT_MAX_RETRY_COUNT - 1, self._mac_address)
            self._mornin_device = None

            from pygatt import BLEAddressType

            try:
                self._mornin_device = self._ble_adapter.connect(self._mac_address, BLE_CONNECT_TIMEOUT_SEC, BLEAddressType.random)
            except Exception as error:
                _LOGGER.error('Error occurred during connecting: %s', error)
                self._mornin_device = None
                # Retry
                continue

            # Perform authentication
            try:
                enc_main_token = self._get_encrypted_main_token()
                self._auth_by_encrypted_main_token(enc_main_token)
            except Exception as error:
                _LOGGER.error('Error occurred during authentication: %s', error)
                self._mornin_device = None
                # Retry
                continue

            # Done
            break

        if (self._mornin_device == None):
            return False

        return True

    def _disconnect(self) -> None:
        """Disconnect from this device."""

        if (self._mornin_device == None):
            return

        _LOGGER.debug('Disconnecting from mornin... %s', self._mac_address)

        try:
            self._mornin_device.disconnect()
        except Exception as error:
            _LOGGER.debug('Error occurred during disconnecting: %s; However ignored.', error)

        self._mornin_device = None

    def _get_encrypted_main_token(self) -> str:

        _LOGGER.debug('Receiving status from mornin %s...', self._mac_address)
        app_service_status = self._mornin_device.char_read(APP_SERVICE_STATUS_UUID, BLE_READ_TIMEOUT_SEC)
        _LOGGER.debug('Status received from mornin %s: ', self._mac_address, app_service_status)

        _LOGGER.debug('Generating seed for %s... %s', self._mac_address)
        seeds = self._get_seeds_by_app_service_status(app_service_status)

        _LOGGER.debug('Generating main token for %s...  %s', self._mac_address)
        main_token =  self._get_main_token_by_seeds(seeds)

        _LOGGER.debug('Generating encrypted main token for %s...', self._mac_address)
        enc_main_token = self._get_encrypted_main_token_by_main_token_and_auth_key(main_token, self._auth_key)
        _LOGGER.debug('Encrypted main token for %s was generated: %s', self._mac_address, enc_main_token)

        return enc_main_token

    def _auth_by_encrypted_main_token(self, encrypted_main_token: str) -> str:

        _LOGGER.debug('Trying to authentication for %s...', self._mac_address)
        BYTE_LENGTH = 1
        BYTE_ENDIAN = 'little'
        HEADER_BYTE = '02'
        auth_value = HEADER_BYTE + encrypted_main_token
        self._mornin_device.char_write(APP_SERVICE_STATUS_UUID, bytes.fromhex(auth_value), True)

    def _get_seeds_by_app_service_status(self, app_service_status: list) -> list:
        seeds = [
            app_service_status[11],
            app_service_status[12],
            app_service_status[13],
            app_service_status[14]
        ]
        return seeds

    def _get_main_token_by_seeds(self, seeds: list) -> str:
        BYTE_LENGTH = 1
        BYTE_ENDIAN = 'little'
        main_token = [92, 101, 44, 182, 81, 212, 239, 235, 137, 90, 188, 111]
        main_token.extend(seeds)
        main_token = list(map(lambda x : x.to_bytes(BYTE_LENGTH, BYTE_ENDIAN), main_token))

        main_token_hex = bytearray(b''.join(main_token)).hex()
        return main_token_hex

    def _get_encrypted_main_token_by_main_token_and_auth_key(self, main_token_hex: str, auth_key_hex: str) -> str:

        from Crypto.Cipher import AES

        main_token = bytes.fromhex(main_token_hex)
        auth_key = bytes.fromhex(auth_key_hex)

        if (len(main_token.hex()) != 32):
            raise Exception('main_token is invalid... value = ' + main_token.hex() + ', length = ' + str(len(main_token.hex())))
        if (len(auth_key.hex()) != 32):
            raise Exception('auth_key is invalid... value = ' + main_token.hex() + ', length = ' + str(len(main_token.hex())))

        cipher = AES.new(auth_key, AES.MODE_ECB)
        enc_main_token_hex = cipher.encrypt(main_token).hex()

        if (len(enc_main_token_hex) != 32):
            raise Exception('encrypted main token has generated but seems invalid... value = ' + enc_main_token_hex + ', length = ' + str(len(enc_main_token_hex)))

        return enc_main_token_hex
