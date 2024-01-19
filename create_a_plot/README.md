This provides an example of deploying the [create_a_plot](../create_a_plot) Panel application to a Panel server alongside Ollama.

* [Run Panel and Ollama locally](#run-panel-and-ollama-locally)
* [Run local Panel and Ollama on Modal](#run-local-panel-and-ollama-on-modal)
* [Run both Panel and Ollama on Modal](#run-both-panel-and-ollama-on-modal)

## Run Panel and Ollama locally

#### 1. Create environment and start a local panel server

```bash
$ make env-create
$ mamba activate create_a_plot
$ make env-update
$ make serve-local-panel
```

#### 2. Install Ollama and setup

```bash
$ curl https://ollama.ai/install.sh | sh
```

This should also create and start an Ollama server using a systemd service as the ollama user (check with e.g. 
`ps -ef | grep ollama`). If you need to start the Ollama service (see also 
[these docs](https://github.com/jmorganca/ollama/blob/main/docs/linux.md):

```bash
sudo systemctl daemon-reload
sudo systemctl enable ollama  # enable on boot
sudo systemctl start ollama
```

You can test Ollama with:

```bash
$ ollama run mistral  # Ctrl+d to exit
```

and the api:

```bash
$ curl http://localhost:11434/api/tags
```

You can also check and follow Ollama logs with 

```bash
$ sudo journalctl -u ollama -f
```

To access the Ollama server from a remote machine, you can configure the 
[Ollama server environment variables](https://github.com/jmorganca/ollama/blob/main/docs/faq.md#how-do-i-use-ollama-server-environment-variables-on-linux)
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

Assuming the `app.py` code is pointing to the correct IP address for the Ollama service (e.g. http://localhost:11434), the app should now work.

## Run local Panel and Ollama on Modal

To run a local Panel server, follow the step 1 in [Run Panel and Ollama locally](#run-panel-and-ollama-locally).

To spin up an Ollama server listening via Modal, run `make modal-serve`. Once the Modal app has started, your local app should
be able to connect to it (note with this script the URL in `app.py` takes the form `IP-ADDRESS`, not `IP-ADDRESS:11434`).

## Run both Panel and Ollama on Modal

(ToDo when needed.)
