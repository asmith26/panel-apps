# Adapted from https://huggingface.co/spaces/ahuang11/tweak-mpl-chat/raw/main/app.py
# Blog: https://blog.holoviz.org/posts/tweak-mpl-chat/ (also https://huggingface.co/blog/sophiamyang/tweak-mpl-chat)

import re
from pprint import pprint

import panel as pn
from panel.io.mime_render import exec_with_return

pn.extension("codeeditor", sizing_mode="stretch_width")

SYSTEM_MESSAGE = "You are a renowned data visualization expert " \
        "with a strong background in matplotlib. " \
        "Your primary goal is to assist the user " \
        "in edit the code based on user request " \
        "using best practices. Simply provide code " \
        "in code fences (```python). You must have `fig` " \
        "as the last line of code"

PROMPT_FORMAT = """
{SYSTEM_MESSAGE}

User: {user_prompt}\n\n```python\n{code}```
Assistant: 
""".strip()

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
    in_message = PROMPT_FORMAT.format(
        SYSTEM_MESSAGE=SYSTEM_MESSAGE, user_prompt=content, code=code_editor.value
    )
    pprint(f"in_message = {in_message}")

    # stream LLM tokens
    # async for chunk in client.chat_stream(model=LLM_MODEL, messages=messages):
    #     if chunk.choices[0].delta.content is not None:
    #         message += chunk.choices[0].delta.content
    with Timer() as t:
        out_message = pipe(in_message)
        yield out_message

    pprint(f"out_message = {out_message}")
    print(f"Duration to generate: {t.duration}")

    # extract code
    llm_code = re.findall(r"```python\n(.*)\n```", out_message, re.DOTALL)[0]
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

sidebar = [chat_interface]
main = [tabs]
template = pn.template.FastListTemplate(
    sidebar=sidebar,
    main=main,
    sidebar_width=600,
    main_layout=None,
    accent_base_color="#fd7000",
    header_background="#fd7000",
    title="Chat with Plot"
)
template.servable()
