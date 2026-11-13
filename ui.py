import base64
from pathlib import Path
import streamlit as st

ASSETS=Path(__file__).parent/'assets'
def header():
    st.markdown("""<style>
    :root{--studio-bg:#1e1e1e;--studio-panel:#292929;--studio-field:#333;--studio-text:#f1f1f1;--studio-muted:#bdbdbd;--studio-border:#606060;--studio-accent:#80baff}
    .stApp,[data-testid="stAppViewContainer"]{background:var(--studio-bg);color:var(--studio-text);color-scheme:dark}
    [data-testid="stHeader"]{background:var(--studio-bg)}[data-testid="stAppDeployButton"]{display:none}
    [data-testid="stSidebar"]{background:var(--studio-panel);border-right:1px solid #464646}
    .block-container{padding:4rem 1.5rem 2rem;max-width:1800px}
    h1,h2,h3,h4,p,label,summary,[data-testid="stMarkdownContainer"], [data-testid="stText"]{color:var(--studio-text)}
    h2,h3{font-size:18px!important;letter-spacing:0} [data-testid="stCaptionContainer"] p{color:var(--studio-muted)!important;font-size:12px}
    [data-testid="stTextInput"] input,[data-baseweb="select"]>div,[data-testid="stFileUploaderDropzone"]{background:var(--studio-field)!important;color:var(--studio-text)!important;border-color:var(--studio-border)!important}
    [data-testid="stTextInput"]>div>div{background:var(--studio-field)!important;border-color:var(--studio-border)!important}
    input::placeholder{color:var(--studio-muted)!important}
    button{color:var(--studio-text)!important} [data-testid="stButton"] button,[data-testid="stFormSubmitButton"] button,[data-testid="stDownloadButton"] button{background:#383838;border:1px solid #707070;border-radius:5px;min-height:40px}
    [data-testid="stButton"] button:hover,[data-testid="stFormSubmitButton"] button:hover{background:#484848;border-color:var(--studio-accent)}
    [data-testid="stButton"] button[kind="primary"],[data-testid="stDownloadButton"] button{background:#1763b6;border-color:#80baff;color:white!important}
    [data-testid="stExpander"]{background:var(--studio-panel);border-radius:5px} [data-testid="stExpander"] details{border-color:#606060}
    [data-testid="stForm"]{border:0;padding:0} [data-testid="stAlert"]{background:#30363e;color:var(--studio-text)}
    [data-baseweb="popover"]{color:var(--studio-text)} [data-baseweb="popover"] ul{background:#333!important;color:var(--studio-text)!important}
    button:focus-visible,input:focus-visible,a:focus-visible,summary:focus-visible{outline:2px solid var(--studio-accent)!important;outline-offset:3px}
    .brand{display:flex;align-items:center;gap:12px;border-bottom:1px solid #494949;padding-bottom:12px;margin-bottom:12px}.brand img{width:38px;height:38px;object-fit:contain}.brand h1{font:600 20px 'Segoe UI',sans-serif;color:var(--studio-text);margin:0;padding:0}.brand p{font-size:12px;margin:2px 0 0;color:var(--studio-muted)}
    .studio-nav{margin-left:auto;display:flex;gap:8px}.studio-nav a{color:#d7e9ff;text-decoration:none;font-size:13px;padding:10px 12px;border:1px solid #606060;border-radius:4px}.studio-nav a:hover{background:#3b3b3b}
    .guidegrid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.guidecard{background:#333;border:1px solid #606060;border-radius:5px;padding:12px}.guidecard img{width:100%;height:100px}.guidecard b{display:block;margin:8px 0}.guidecard p{font-size:13px;color:#ddd;margin:0}
    [data-testid="stHorizontalBlock"]{gap:20px}hr{border-color:#494949!important}html{scroll-padding-top:70px}
    @media(min-width:900px){.stApp{zoom:0.8}[data-testid="stMain"],[data-testid="stSidebar"]{height:125vh}iframe[data-testid="stCustomComponentV1"]{width:100%}}
    @media(max-width:800px){.guidegrid{grid-template-columns:repeat(2,1fr)}.block-container{padding-left:1rem;padding-right:1rem}.brand{flex-wrap:wrap}.studio-nav{margin-left:0}.brand h1{font-size:18px}}
    @media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
    </style>""",unsafe_allow_html=True)
    logo=ASSETS/'logo.png'
    mark=('<img alt="Logo Collage Smart" src="data:image/png;base64,'+base64.b64encode(logo.read_bytes()).decode()+'">') if logo.exists() else ''
    st.markdown('<div class="brand">'+mark+'<div><h1>Collage Smart</h1><p>Atelier de retouche · A4 polaroid</p></div><nav class="studio-nav" aria-label="Navigation atelier"><a href="#planches" target="_self">Planches</a><a href="#exports" target="_self">Exporter</a></nav></div>',unsafe_allow_html=True)

def guide():
    from streamlit.components.v1 import declare_component
    tutorial=declare_component('photo_onboarding',path=str(Path(__file__).parent/'onboarding'))
    tutorial(key='photo_onboarding',default=None)


def crop_notice(numbers):
    labels=', '.join(str(n) for n in numbers)
    target=('la photo '+labels) if len(numbers)==1 else ('les photos '+labels)
    return ('**Cadrage à vérifier — '+target+'**\n\n'
            'Une personne pourrait être coupée au bord de la photo. '
            'Cliquez sur la photo concernée, puis sur **Afficher la photo entière** pour la voir en entier. '
            'Vous pouvez aussi dézoomer avec la molette ou déplacer la photo dans son rectangle.\n\n'
            'Les photos sont numérotées de gauche à droite : **1 à 5 en haut, 6 à 10 en bas**. '
            'Si le cadrage vous convient, vous pouvez le garder et exporter.')
