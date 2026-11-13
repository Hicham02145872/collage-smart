from pathlib import Path
from streamlit.components.v1 import declare_component

a4_editor=declare_component('a4_editor',path=str(Path(__file__).parent/'canvas_editor'))
