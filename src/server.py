import websockets.asyncio.client
from logger import logger
import json
import asyncio
import flitter
import websockets.asyncio.server

# TODO: 卡顿问题，需要优化

token = ""
ws_client = None
ws_server = None

async def send_heartbeat():
    global ws_client
    while True:
        try:
            await ws_client.send(json.dumps({"type": "heartbeat"}))  # 发送心跳消息
            await asyncio.sleep(30)  # 每30秒发送一次心跳
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket 客户端连接已关闭")

async def reconnect_client():
    global ws_client, token
    target_url = ws_client.path if ws_client else ""
    self_id = ws_client.request_headers.get("x-self-id", "") if ws_client else ""
    
    if not target_url or not self_id:
        logger.error("无法重连: 缺少目标URL或self_id")
        return
        
    while True:
        try:
            headers = {"platform": "qq", "x-self-id": self_id}
            if token:
                headers["Authorization"] = token
                
            ws_client = await websockets.asyncio.client.connect(
                target_url, 
                additional_headers=headers, 
                max_size=30 * (1024 ** 2)
            )
            logger.info(f"已重新连接到 WebSocket 服务器 {target_url}")
            return
        except Exception as e:
            logger.error(f"重连失败: {e}, 10秒后重试...")
            await asyncio.sleep(10)

async def client_listener():
    global ws_client, ws_server
    
    while True:
        try:
            if ws_client and ws_client.open:
                response = await asyncio.wait_for(ws_client.recv(), timeout=300)
                logger.debug(f"WebSocket 连接对方响应: {response}")
                if ws_server and ws_server.open:
                    await ws_server.send(response)
            else:
                await asyncio.sleep(5)
                
        except asyncio.TimeoutError:
            logger.warning("WebSocket 客户端接收超时，继续等待...")
            await asyncio.sleep(5)
                
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"WebSocket 客户端连接已关闭: {e}, 尝试重新连接...")
            await reconnect_client()
            
        except Exception as e:
            logger.error(f"发生未预期错误: {e}, 10秒后重试...")
            await asyncio.sleep(10)


async def server_handler(websocket):
    global ws_client
    global ws_server

    ws_server = websocket

    async for message in websocket:
        logger.debug(f"收到消息: {message}")

        data = json.loads(message)
        post_type = data.get("post_type", "")

        if post_type == "meta_event":
            # 元事件
            meta_event_type = data.get("meta_event_type")
            sub_type = data.get("sub_type")

            if meta_event_type == "lifecycle":
                msg = "连接" if sub_type == "connect" else "断开"
                logger.info(f"WebSocket 连接状态变更: {msg}")

        elif post_type == "message":
            # 消息
            raw_message = data.get("raw_message")
            passed = await flitter.check_message(data)
            if passed:
                logger.debug(f"消息通过: {raw_message}")
                await ws_client.send(message)
            else:
                logger.debug(f"消息被拦截: {raw_message}")

        elif not post_type:
            # 不是消息
            if data.get("status",""):
                # 状态消息
                logger.debug(f"WebSocket 状态消息: {data}")
                await ws_client.send(message)



async def start_server(
    host: str,
    port: int,
):
    ws_server = await websockets.asyncio.server.serve(server_handler, host, port, max_size=30 * (1024 ** 2))
    logger.info(f"WebSocket 服务器已启动")


async def start_client(
    target_url: str,
    self_id: str,
):
    global token
    logger.info(f"正在连接 WebSocket 服务器 {target_url}...")

    headers = {"platform": "qq", "x-self-id": self_id}
    if token:
        headers["Authorization"] = token

    global ws_client
    ws_client = await websockets.asyncio.client.connect(target_url, additional_headers=headers, max_size=30 * (1024 ** 2))
    logger.info(f"已连接到 WebSocket 服务器 {target_url}")

    asyncio.create_task(client_listener())  # 启动监听客户端响应的任务
    asyncio.create_task(send_heartbeat())  # 启动心跳任务
        
