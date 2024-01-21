# From: https://modallabscommunity.slack.com/archives/C069UABSDB4/p1703269358628439?thread_ts=1703200791.672809&cid=C069UABSDB4

import sys
import time
import modal
import subprocess

from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse

# Default server port.
MODEL_ID: str = "mistral"
OLLAMA_PORT: int = 11434
OLLAMA_URL: str = f"http://localhost:{OLLAMA_PORT}"


def _run_subprocess(cmd: list[str], block: bool = True) -> None:
    if block:
        subprocess.run(
            cmd,
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
        )
    else:
        subprocess.Popen(
            cmd,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )


def _is_server_healthy() -> bool:
    try:
        response = requests.get(OLLAMA_URL)
        if response.ok:
            print(f"ollama server running => {OLLAMA_URL}")
            return True
        else:
            print(f"ollama server not running => {OLLAMA_URL}")
            return False
    except requests.RequestException as e:
        return False


def download_model():
    _run_subprocess(["ollama", "serve"], block=False)
    while not _is_server_healthy():
        print("waiting for server to start ...")
        time.sleep(1)

    # choose model to download
    _run_subprocess(["ollama", "pull", MODEL_ID])


image = (
    modal.Image.from_registry(
        "ollama/ollama:0.1.20",
        add_python="3.11",
    )
    .pip_install("requests")  # for healthchecks
    .pip_install("httpx")  # for reverse proxy
    .copy_local_file("../utils/entrypoint.sh", "/opt/entrypoint.sh")
    .dockerfile_commands(
        [
            "RUN chmod a+x /opt/entrypoint.sh",
            'ENTRYPOINT ["/opt/entrypoint.sh"]',
        ]
    )
    .env({"OLLAMA_ORIGINS": "*"})
    .run_function(download_model)
)

stub = modal.Stub("ollama-server", image=image)
with stub.image.imports():
    import httpx
    import requests

    from starlette.background import BackgroundTask

    # Start Ollama server and make sure it is running before accepting inputs.
    _run_subprocess(["ollama", "serve"], block=False)
    while not _is_server_healthy():
        print("waiting for server to start ...")
        time.sleep(1)

    print("ollama server started!")


# FastAPI proxy. This allows for requests to be handled by Modal, allowing
# effective scaling, queues, etc.
app = FastAPI()


@stub.function(container_idle_timeout=180)
@modal.asgi_app()
def create_asgi():
    return app


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
async def proxy(request: Request, path: str):
    # Create a new client on every request.
    client = httpx.AsyncClient(
        base_url=OLLAMA_URL, headers=request.headers, timeout=60 * 5
    )  # ollama can take a few seconds to respond

    url = httpx.URL(path=request.url.path, query=request.url.query.encode("utf-8"))

    # Supports both streaming and non-streaming responnses.
    async def _response():
        # Handle all other non-streaming methods.
        response = await client.request(
            request.method,
            url,
            params=request.query_params,
            json=await request.json() if len(await request.body()) > 0 else None,
        )
        return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))

    async def _streaming_response():
        rp_req = client.build_request(
            request.method,
            url,
            content=request.stream(),
            json=await request.json() if len(await request.body()) > 0 else None,
        )
        rp_resp = await client.send(rp_req, stream=True)
        background_task = BackgroundTask(rp_resp.aclose)
        return StreamingResponse(
            rp_resp.aiter_raw(),
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "*",  # Allows all origins
                "Access-Control-Allow-Methods": "GET",  # Only allow GET method
                "Access-Control-Allow-Headers": "Content-Type",  # Specify allowed headers
            },
            media_type="text/event-stream", background=background_task
        )

    # These two methods support streaming responses.
    # Reference: https://github.com/jmorganca/ollama/blob/main/docs/api.md
    if request.url.path in ("/api/generate", "/api/chat"):
        return await _streaming_response()
    else:
        return await _response()
