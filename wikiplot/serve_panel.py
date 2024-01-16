# Adapted from https://github.com/modal-labs/modal-examples/blob/main/10_integrations/panel/serve_panel.py

import pathlib

import modal

#  Container Dependencies
#
# Installs dependencies in panel_app.py and `asgiproxy` to proxy the Panel server.

image = (
    modal.Image.debian_slim()
    .apt_install("git")
    .pip_install("panel", "numpy", "pandas")
    # Use fork until https://github.com/valohai/asgiproxy/pull/11 is merged.
    .pip_install("git+https://github.com/modal-labs/asgiproxy.git")
)

stub = modal.Stub(name="wikiplot", image=image)

# Mount the `app.py` script inside the container at a pre-defined path using a Modal mount
panel_script_local_path = pathlib.Path(__file__).parent / "app.py"
panel_script_remote_path = pathlib.Path("/root/app.py")

if not panel_script_local_path.exists():
    raise RuntimeError(
        "app.py not found! Place the script with your panel app in the same directory."
    )

panel_script_mount = modal.Mount.from_local_file(
    panel_script_local_path,
    panel_script_remote_path,
)

# Spawning the Panel server
# Inside the container, we will run the Panel server in a background subprocess using
# `subprocess.Popen`. Here we define `spawn_server()` to do this and then poll until the server
# is ready to accept connections.
HOST = "127.0.0.1"
PORT = "8000"


def spawn_server():
    import socket
    import subprocess

    process = subprocess.Popen(
        [
            "panel",
            "run",
            str(panel_script_remote_path),
            "--browser.serverAddress",
            HOST,
            "--server.port",
            PORT,
            "--browser.serverPort",
            PORT,
            "--server.enableCORS",
            "false",
        ]
    )

    # Poll until webserver accepts connections before running inputs.
    while True:
        try:
            socket.create_connection((HOST, int(PORT)), timeout=1).close()
            print("Webserver ready!")
            return process
        except (socket.timeout, ConnectionRefusedError):
            # Check if launcher webserving process has exited.
            # If so, a connection can never be made.
            retcode = process.poll()
            if retcode is not None:
                raise RuntimeError(
                    f"launcher exited unexpectedly with code {retcode}"
                )


# ## Wrap it in an ASGI app
#
# Finally, Modal can only serve apps that speak the [ASGI](https://modal.com/docs/guide/webhooks#asgi) or
# [WSGI](https://modal.com/docs/guide/webhooks#wsgi) protocols. Since the Panel server is neither,
# we run a separate ASGI app that proxies requests to the Panel server using the `asgiproxy` package.
# Note that at this point `asgiproxy` has a bug with websocket handling, so we are using a
# [fork](https://github.com/modal-labs/asgiproxy) with the fix for this.


@stub.function(
    # Allows 1 concurrent requests per container.
    allow_concurrent_inputs=1,  # was 100
    mounts=[panel_script_mount],
)
@modal.asgi_app()
def run():
    from asgiproxy.config import BaseURLProxyConfigMixin, ProxyConfig
    from asgiproxy.context import ProxyContext
    from asgiproxy.simple_proxy import make_simple_proxy_app

    spawn_server()

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


# ## Iterate and Deploy
#
# While you're iterating on your screamlit app, you can run it "ephemerally" with `modal serve`. This will
# run a local process that watches your files and updates the app if anything changes.
#
# ```shell
# modal serve serve_panel.py
# ```
#
# Once you're happy with your changes, you can deploy your application with
#
# ```shell
# modal deploy serve_panel.py
# ```
#
# If successful, this will print a URL for your app, that you can navigate to from
# your browser 🎉 .
