# Adapted from https://huggingface.co/spaces/ahuang11/tweak-mpl-chat/raw/main/app.py
# Blog: https://blog.holoviz.org/posts/tweak-mpl-chat/ (also https://huggingface.co/blog/sophiamyang/tweak-mpl-chat)
import re

import panel as pn
from panel.io.mime_render import exec_with_return
from ollama import AsyncClient


client = AsyncClient(base_url='http://localhost:11434')

pn.extension("codeeditor", sizing_mode="stretch_width")

SYSTEM_MESSAGE = "You are a renowned data visualization expert " \
        "with a strong background in matplotlib. " \
        "Your primary goal is to assist the user " \
        "in edit the code based on user request " \
        "using best practices. Simply provide code " \
        "in code fences (```python). You must have `fig` " \
        "as the last line of code"
INITIAL_CODE = """
import numpy as np
import matplotlib.pyplot as plt

fig = plt.figure()
ax = plt.axes(title="Plot Title", xlabel="X Label", ylabel="Y Label")

x = np.linspace(1, 10)
y = np.sin(x)
z = np.cos(x)
c = np.log(x)

ax.plot(x, y, c="blue", label="sin")
ax.plot(x, z, c="orange", label="cos")

img = ax.scatter(x, c, c=c, label="log")
plt.colorbar(img, label="Colorbar")
plt.legend()

# must have fig at the end!
fig
""".strip()


async def callback(content: str, user: str, instance: pn.chat.ChatInterface):
    # return "test"
    in_message = f"{content}\n\n```python\n{code_editor.value}```"

    # stream LLM tokens
    message = ""
    async for part in await client.generate(
        model='mistral',
        system=SYSTEM_MESSAGE,
        prompt=in_message,
        stream=True,
        options={
            'temperature': 0,
        },
    ):
        message += part['response']
        yield message

    # extract code
    llm_code = re.findall(r"```python\n(.*)\n```", message, re.DOTALL)[0]
    if llm_code.splitlines()[-1].strip() != "fig":
        llm_code += "\nfig"
    code_editor.value = llm_code


def update_plot(event):
    matplotlib_pane.object = exec_with_return(event.new)


# instantiate widgets and panes
chat_interface = pn.chat.ChatInterface(
    callback=callback,
    show_clear=False,
    show_undo=False,
    show_button_name=False,
    message_params=dict(
        show_reaction_icons=False,
        show_copy_icon=False,
    ),
    height=700,
    callback_exception="verbose",
)
matplotlib_pane = pn.pane.Matplotlib(
    exec_with_return(INITIAL_CODE),
    sizing_mode="stretch_both",
    tight=True,
)
code_editor = pn.widgets.CodeEditor(
    value=INITIAL_CODE,
    language="python",
    sizing_mode="stretch_both",
)

# watch for code changes
code_editor.param.watch(update_plot, "value")

# lay them out
tabs = pn.Tabs(
    ("Plot", matplotlib_pane),
    ("Code", code_editor),
)

sidebar = [chat_interface, pn.pane.Markdown("#### Examples \n"
                                            "- Please add gridlines to this plot.")]
main = [tabs]
template = pn.template.FastListTemplate(
    sidebar=sidebar,
    main=main,
    sidebar_width=600,
    main_layout=None,
    accent_base_color="#fd7000",
    header_background="#fd7000",
    title="Create a plot"
)
template.servable()
