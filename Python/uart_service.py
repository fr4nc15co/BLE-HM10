"""
UART Service
-------------

An example showing how to write a simple program using the Nordic Semiconductor
(nRF) UART service.

This code has been adapted for ICAI Lab sessions by Francisco Martín. Please see original in https://github.com/hbldh/bleak 

Steps:
    1. Create a virtual environment: python -m venv venv
    2. Activate the virtual environment:
        - On Windows: .\venv\Scripts\activate
        - On macOS/Linux: source venv/bin/activate
    3. Install bleak: pip install bleak
    4. Run the script: python uart_service.py

    5. Enter the BLE address when prompted (or set it in the code BLE_ADDRESS)
    6. Type messages to send to the device and press ENTER
    7. The device will respond and the response will be printed to the console
    8. To exit, press CTRL+D (or CTRL+C to force quit)
"""

import asyncio
import sys
import platform
from itertools import count, takewhile
from typing import Iterator

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

UART_SERVICE_UUID = "FFE0" # UART SERVICE UUID in HM-10
UART_RX_CHAR_UUID = "FFE1" # UART RX CHARACTERISTIC UUID in HM-10
UART_TX_CHAR_UUID = "FFE1" # UART TX CHARACTERISTIC UUID in HM-10
BLE_ADDRESS = "" # Replace with your device's address (e.g. Windows "D0:B5:C2:E9:C8:62"), left empty for user input


# TIP: you can get this function and more from the ``more-itertools`` package.
def sliced(data: bytes, n: int) -> Iterator[bytes]:
    """
    Slices *data* into chunks of size *n*. The last slice may be smaller than
    *n*.
    """
    return takewhile(len, (data[i : i + n] for i in count(0, n)))


async def uart_terminal():
    """This is a simple "terminal" program that uses the Nordic Semiconductor
    (nRF) UART service. It reads from stdin and sends each line of data to the
    remote device. Any data received from the device is printed to stdout.
    """

    def match_nus_uuid(device: BLEDevice, adv: AdvertisementData):
        # This assumes that the device includes the UART service UUID in the
        # advertising data. This test may need to be adjusted depending on the
        # actual advertising data supplied by the device.
        if UART_SERVICE_UUID.lower() in adv.service_uuids:
            return True

        return False
    #device = await BleakScanner.find_device_by_filter(match_nus_uuid)

    if BLE_ADDRESS == "":
        devices = await BleakScanner.discover()

        for device in devices:
            print(device)

        ble_address_selected = input("Please, copy the BLE address: ")
        # Mostrar el valor ingresado
        print(f"The BLE address introduced is: {ble_address_selected}")
    else:
        ble_address_selected = BLE_ADDRESS
        print(f"The predefined BLE address is: {ble_address_selected}")

    device_selected = await BleakScanner.find_device_by_address(ble_address_selected)

    if device_selected is None:
        print("No matching device found, you may need to edit BLE_ADDRESS or scan for finding a new id.")
        sys.exit(1)

    
    def handle_disconnect(_: BleakClient):
        print("Device was disconnected, goodbye.")
        # cancelling all tasks effectively ends the program
        for task in asyncio.all_tasks():
            task.cancel()

    def handle_rx(_: BleakGATTCharacteristic, data: bytearray):
        print("received:", data)

    async with BleakClient(device_selected, disconnected_callback=handle_disconnect) as client:
        await client.start_notify(UART_TX_CHAR_UUID, handle_rx)
        
        print("Connected, start typing and press ENTER...Control+C to exit.")
        print(f"Platform: {platform.system()} {platform.version()}")

        async def write_with_debug(client, char, data: bytes):
            """Write helper that logs and uses a macOS-friendly default.

            On macOS some devices expect "write with response" instead of
            "write without response". Use response=True on Darwin by
            default, but log and fall back if an error occurs.
            """
            use_response = platform.system() == "Darwin"
            # Prefer the characteristic's reported max size for slicing when available
            max_size = getattr(char, "max_write_without_response_size", 20) or 20

            for chunk in sliced(data, max_size):
                try:
                    print(f"Writing to {char.uuid}: {chunk!r} (len={len(chunk)}) response={use_response} properties={getattr(char, 'properties', None)}")
                    await client.write_gatt_char(char, chunk, response=use_response)
                    # small pause to give the adapter/remote time to process
                    await asyncio.sleep(0.02)
                except Exception as e:
                    print(f"Write error (response={use_response}): {e}")
                    # Try the opposite mode as a fallback
                    try:
                        alt = not use_response
                        print(f"Retrying write with response={alt}")
                        await client.write_gatt_char(char, chunk, response=alt)
                        await asyncio.sleep(0.02)
                    except Exception as e2:
                        print(f"Retry failed: {e2}")

        loop = asyncio.get_running_loop()
        nus = client.services.get_service(UART_SERVICE_UUID)
        rx_char = nus.get_characteristic(UART_RX_CHAR_UUID)

        # Primer envio para probar conexión
        data = b"Hello UART\n"
        #data = bytes([0x01,0x0C, 0x0A, 0x01])  # Ejemplo: enviar bytes específicos
        # Dividir datos en fragmentos si es necesario
        await write_with_debug(client, rx_char, data)

        while True:
            # This waits until you type a line and press ENTER.
            # A real terminal program might put stdin in raw mode so that things
            # like CTRL+C get passed to the remote device.
            data = await loop.run_in_executor(None, sys.stdin.buffer.readline)

            # data will be empty on EOF (e.g. CTRL+D on *nix)
            if not data:
                break

            # some devices, like devices running MicroPython, expect Windows
            # line endings (uncomment line below if needed)
            # data = data.replace(b"\n", b"\r\n")

            # Writing without response requires that the data can fit in a
            # single BLE packet. We can use the max_write_without_response_size
            # property to split the data into chunks that will fit.

            await write_with_debug(client, rx_char, data)

            print("sent:", data)


if __name__ == "__main__":
    try:
        asyncio.run(uart_terminal())
    except asyncio.CancelledError as e:
        # task is cancelled on disconnect, so we ignore this error
        # print(f"Error durante la operación: {e}")
        pass
    except KeyboardInterrupt:
        pass
    finally:
        # Lógica para liberar recursos o desconectar
        print("Connection closed.")
