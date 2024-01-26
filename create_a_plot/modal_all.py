# Adapted from: https://github.com/modal-labs/modal-examples/blob/main/06_gpu_and_ml/stable_diffusion/stable_diffusion_xl.py
import modal
from modal import Image, Stub, build, enter, method, Mount


HOST = "127.0.0.1"
PORT = "8888"
SYSTEM_MESSAGE = "You are a renowned data visualization expert " \
        "with a strong background in matplotlib. " \
        "Your primary goal is to assist the user " \
        "in edit the code based on user request " \
        "using best practices. Simply provide code " \
        "in code fences (```python). You must have `fig` " \
        "as the last line of code"

ollama_image = (
    Image.from_registry(
        "ollama/ollama:0.1.20",
        add_python="3.11",
    )
    .pip_install_from_requirements("requirements.txt")
    .copy_local_dir("../utils/", "/root/")
    .copy_local_file("../utils/entrypoint.sh", "/opt/entrypoint.sh")
    .dockerfile_commands(
        [
            "RUN chmod a+x /opt/entrypoint.sh",
            'ENTRYPOINT ["/opt/entrypoint.sh"]',
        ]
    )
)

stub = Stub("ollama")
with ollama_image.imports():
    from ollama import AsyncClient
    from utils import download_model, start_ollama_server
    from utils import run_subprocess


## Load Ollama server and define inference functions
# The container lifecycle [`__enter__` function](https://modal.com/docs/guide/lifecycle-functions#container-lifecycle-beta)
# loads the model at startup.
# To avoid excessive cold-starts, we set the idle timeout to 240 seconds, meaning once a GPU has loaded the model it will stay
# online for 4 minutes before spinning down. This can be adjusted for cost/experience trade-offs.
@stub.cls(container_idle_timeout=240, image=ollama_image)
class Model:
    @build()
    def build(self):
        # from ollama import AsyncClient
        # from utils import download_model, start_ollama_server
        # from utils import run_subprocess
        MODEL_ID: str = "mistral"
        start_ollama_server()
        download_model(MODEL_ID)

    @enter()
    def enter(self):
        # from ollama import AsyncClient
        # from utils import run_subprocess
        self.client = AsyncClient()
        # panel.serve(template, address=HOST, port=PORT, websocket_origin="*")
        run_subprocess([
                    "panel",
                    "serve",
                    "/root/app.py",
                    "--address",
                    HOST,
                    "--port",
                    PORT,
                    "--allow-websocket-origin",
                    "*",
        ])
    @method()
    def generate(self, in_message):
        return self.client.generate(
                model='mistral',
                system=SYSTEM_MESSAGE,
                prompt=in_message,
                stream=True,
                options={
                    'temperature': 0,
                },
        )




# def spawn_server():
#     import socket
#     import subprocess
#     process = subprocess.Popen(
#         [
#             "panel",
#             "server",
#             str(app_remote_path),
#             "--address",
#             HOST,
#             "--port",
#             PORT,
#             "--allow-websocket-origin",
#             "*",
#         ]
#     )
#
#     # Poll until webserver accepts connections before running inputs.
#     while True:
#         try:
#             socket.create_connection((HOST, int(PORT)), timeout=1).close()
#             print("Webserver ready!")
#             return process
#         except (socket.timeout, ConnectionRefusedError):
#             # Check if launcher webserving process has exited.
#             # If so, a connection can never be made.
#             retcode = process.poll()
#             if retcode is not None:
#                 raise RuntimeError(
#                     f"launcher exited unexpectedly with code {retcode}"
#                 )




@stub.function(
    mounts=[Mount.from_local_dir("./", remote_path="/root/")],
    # keep_warm=1,
    allow_concurrent_inputs=20,
    # timeout=60 * 10,
)
@modal.asgi_app()
def run():
    from asgiproxy.config import BaseURLProxyConfigMixin, ProxyConfig
    from asgiproxy.context import ProxyContext
    from asgiproxy.simple_proxy import make_simple_proxy_app

    config = type(
        "Config",
        (BaseURLProxyConfigMixin, ProxyConfig),
        {
            "upstream_base_url": f"http://{HOST}:{PORT}",
            "rewrite_host_header": f"{HOST}:{PORT}",
        },
    )()
    proxy_context = ProxyContext(config)
    return make_simple_proxy_app(proxy_context)
