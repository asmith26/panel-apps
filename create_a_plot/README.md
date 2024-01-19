This provides an example of deploying the [create_a_plot](../create_a_plot) Panel application to Modal, in addition to 
deploying a LLM to Modal.

## Test Panel + Ollama locally

#### 1. Create and start a local panel server

```bash
$ make env-create
$ mamba activate create_a_plot
$ make env-update
$ make serve-local-panel
```

#### 2. Install ollama and setup

```bash
$ curl https://ollama.ai/install.sh | sh
```

This should also create and start an ollama server/a systemd service as the ollama user (check with e.g. `ps -ef | grep ollama`). If you need to start the 
ollama service (see also [these docs](https://github.com/jmorganca/ollama/blob/main/docs/linux.md):

```bash
sudo systemctl daemon-reload
sudo systemctl enable ollama  # enable on boot
sudo systemctl start ollama
```

You can test ollama with:

```bash
$ ollama run mistral  # Ctrl+d to exit
```

and the api:

```bash
$ curl http://localhost:11434/api/tags
```

You can also check and follow ollama logs with 

```bash
$ sudo journalctl -u ollama -f
```

To access the ollama server from a remote machine, you can configure the 
[ollama server environment variables](https://github.com/jmorganca/ollama/blob/main/docs/faq.md#how-do-i-use-ollama-server-environment-variables-on-linux)
e.g. `sudo nano /etc/systemd/system/ollama.service.d/environment.conf`:

```bash
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

and reload systemd/restart Ollama:

```bash
$ sudo systemctl daemon-reload
$ sudo systemctl restart ollama
```

Check you can connect with e.g.:

```bash
$ curl http://IP ADDRESS:11434/api/tags
```

#### 3. Try the app

Assuming the app code is point to the correct IP address for the ollama service, the app should now work
