import asyncio
import aiohttp
import ssl
import certifi
import logging
import yaml

from custom_components.compit.api import CompitAPI

logging.basicConfig(level=logging.INFO)

CREDENTIALS_FILE = "credential.yaml"

def load_credentials(filename):
    with open(filename, "r") as f:
        creds = yaml.safe_load(f)
        return creds["email"], creds["password"]

async def main():
    email, password = load_credentials(CREDENTIALS_FILE)
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        api = CompitAPI(email, password, session)
        print(f"Logging in as {email!r} ...")
        result = await api.authenticate()
        print("Auth result:", result)
        if getattr(api, "token", None):
            print("Successfully retrieved token:", api.token)
            print("Successfully retrieved api", api)

            # Download (fetch) devices/gates information
            gates = await api.get_gates()
            print("Downloaded devices/gates:", gates)
            device = gates.gates[0]
            print("devices/gates:", device.code, device.label, device.id)
            print("devices/gates:", device.devices[0].class_, device.devices[0].id, device.devices[0].label, device.devices[0].type)


        else:
            print("Login failed.")

if __name__ == "__main__":
    asyncio.run(main())