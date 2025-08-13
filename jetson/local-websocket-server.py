import asyncio
import json
import time
import random
import websockets
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

HOST = "localhost"
PORT = 8000  # Django(8000)와 충돌 피하기 위해 변경
PUSH_INTERVAL = 1.5  # 서버 → 클라이언트 주기적 송신 주기(초)

# track-video.py 클라이언트 관리용 집합
track_video_clients = set()

# track-video.py에서 보내는 payload를 받아서 출력하는 서버
async def receive_from_client(websocket):
    async for message in websocket:
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            data = {"raw": message}
        print(f"[server] from client: {data}")

        # track-video.py에서 오는 메시지면 단순 출력 및 ack
        ack = {"type": "ack", "received_at": time.time()}
        await websocket.send(json.dumps(ack))

async def push_periodically(websocket):
    seq = 0
    while True:
        # 2) 주기적으로 주차 할당 요청 푸시(테스트용)
        if seq % 5 == 0:
            # 5개 할당 요청을 한 번에 보냄
            assignments = []
            for i in range(5):
                assignment = {
                    "message_type": "request_assignment",
                    "license_plate": f"TEST-{1000 + seq}-{i+1}",
                    "size_class": random.choice(["small", "medium", "large"]),
                }
                assignments.append(assignment)
            for assignment in assignments:
                await websocket.send(json.dumps(assignment))
        seq += 1
        await asyncio.sleep(PUSH_INTERVAL)

async def handler(websocket):
    # 최초 메시지로 클라이언트 타입 구분
    try:
        first_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
        try:
            hello = json.loads(first_msg)
        except Exception:
            hello = {}
    except Exception:
        hello = {}

    # track-video.py는 초기 hello를 보내지 않을 수 있으므로 기본 허용
    is_track_video = True
    track_video_clients.add(websocket)
    print("[server] track-video.py 클라이언트 연결됨 (hello 생략 허용)")

    async def receive_from_client_inner(first_msg=None):
        if first_msg is not None:
            try:
                data = json.loads(first_msg)
            except json.JSONDecodeError:
                data = {"raw": first_msg}
            print(f"[server] from client: {data}")

            ack = {"type": "ack", "received_at": time.time()}
            await websocket.send(json.dumps(ack))
        # 이후 메시지 루프
        await receive_from_client(websocket)

    push_task = asyncio.create_task(push_periodically(websocket))
    recv_task = asyncio.create_task(receive_from_client_inner(first_msg))
    try:
        await asyncio.gather(recv_task, push_task)
    except (ConnectionClosedOK, ConnectionClosedError):
        pass
    finally:
        for t in (recv_task, push_task):
            if not t.done():
                t.cancel()
        if is_track_video:
            track_video_clients.discard(websocket)
        print("[server] connection closed")

async def main():
    async with websockets.serve(handler, HOST, PORT, ping_interval=20, ping_timeout=20, max_size=10*1024*1024):
        print(f"[server] listening on ws://{HOST}:{PORT}")
        await asyncio.Future()  # 서버 유지

if __name__ == "__main__":
    print("로컬 웹소켓 서버를 시작합니다. track-video.py에서 보내는 데이터를 수신합니다.")
    print("track-video.py는 최초 연결 시 {\"client_type\": \"track_video\"} 메시지를 먼저 보내야 합니다.")
    asyncio.run(main())
