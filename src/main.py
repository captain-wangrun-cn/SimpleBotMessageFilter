import argparse
import asyncio
import logging
import json
import server
import flitter
from logger import logger

__version__ = "1.0.3"

parser = argparse.ArgumentParser(description=f'Simple Bot Message Filter v{__version__}')
parser.add_argument("-H", "--host", type=str, default="localhost", help="host for websockets listen on")
parser.add_argument("-p", "--port", type=int, default=4080, help="port for websockets listen on")
parser.add_argument("-c", "--config", type=str, default="config.json", help="config file path") 
parser.add_argument("-t", "--token", type=str, default="", help="token for websockets authentication")
parser.add_argument("-u", "--url", type=str, default="", help="target url for websockets connection")
parser.add_argument("-i", "--id", type=str, default="", help="self id for websockets connection")
parser.add_argument("-d", "--debug", action="store_true", help="debug mode")
args = parser.parse_args()

if __name__ == "__main__":
    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)
        flitter.rules = config["rules"]
    
    if args.token:
        server.token = args.token
    
    if args.debug:
        logger.setLevel(logging.DEBUG)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(server.start_client(args.url, args.id))
    loop.run_until_complete(server.start_server(args.host, args.port))
    
    try:
        logger.info("Simple Bot Message Filter v"+__version__)
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("已退出")
    except RuntimeError:
        logger.info("已退出")
