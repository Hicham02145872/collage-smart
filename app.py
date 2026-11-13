from io import BytesIO
from pathlib import Path
import json
import math
import hashlib
import base64
from types import SimpleNamespace
import streamlit as st
from PIL import Image,ImageDraw
from core import load_template,read_media,trim_borders,Detector,assemble_lazy,crop_bounds,viewport_clips,ROOT,VIDEO_EXTENSIONS,PHOTO_EXTENSIONS,render_template
from exporting import client_name,page_name,file_name,label_client,export_batch
from editor_component import a4_editor

from ui import header,guide,crop_notice
st.set_page_config(page_title='Collage Smart · Atelier photo',page_icon=str(ROOT/'assets'/'logo.png') if (ROOT/'assets'/'logo.png').exists() else '📷',layout='wide')
header()
guide()
with st.sidebar:
    st.subheader('Commande client')
    with st.form('client_form'):
        client=client_name(st.text_input('Nom du client','Nom client',max_chars=120,key='client_name_input'))
        st.form_submit_button('Appliquer le nom',use_container_width=True)
    st.caption('Nom des fichiers : '+page_name(client,0)+' · '+page_name(client,1))
    st.divider()

@st.cache_resource
def detector():
    return Detector()

@st.cache_resource(show_spinner=False)
def template(path,mtime):
    image,slots=load_template(path)
    scale=min(1,3564/image.width,2520/image.height)
    if scale<1:
        small=image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.LANCZOS)
        image.close();image=small
        for slot in slots: slot['box']=tuple(round(v*scale) for v in slot['box'])
    return image,slots

@st.cache_resource(show_spinner=False)
def integrated_template():
    return render_template()

@st.cache_data(show_spinner=False,max_entries=512)
def analyze(data,remove_black,filename='photo.jpg'):
    image=read_media(data,filename)
    original=image.size
    image,box=trim_borders(image) if remove_black else (image,(0,0,*image.size))
    boxes,method=detector().detect(image)
    # Only small metadata is cached, never decoded photographs.
    image.close()
    return box,boxes,method,box!=(0,0,*original)

def decoded_photo(upload,metadata):
    image=read_media(upload.getvalue(),upload.name)
    box=metadata[0]
    if box!=(0,0,*image.size):
        cropped=image.crop(box);image.close();return cropped
    return image

@st.cache_data(show_spinner=False,max_entries=40)
def editor_texture(data,filename,box):
    image=read_media(data,filename)
    if tuple(box)!=(0,0,*image.size):
        cropped=image.crop(box);image.close();image=cropped
    width,height=image.size
    image.thumbnail((1200,1200),Image.Resampling.LANCZOS)
    out=BytesIO();image.save(out,format='JPEG',quality=88);image.close()
    return width,height,'data:image/jpeg;base64,'+base64.b64encode(out.getvalue()).decode()

with st.sidebar:
    st.caption('DOCUMENT · A4 paysage · 10 cadres')
    with st.expander('Changer le template'):
        path=st.text_input('Autre chemin PSD (facultatif)','')
    st.subheader('Bibliothèque de photos')
    uploads=st.file_uploader('Photos et vidéos (10 images par page)',type=sorted(s[1:] for s in PHOTO_EXTENSIONS|VIDEO_EXTENSIONS),accept_multiple_files=True)
    st.caption('Vidéos : uniquement la première image, sans rechercher une autre image.')
    suggested=Path.home()/'Desktop'/'photoshop'/'pic'
    folder=st.text_input('Ou un dossier local',str(suggested) if suggested.is_dir() else '')
    if not uploads and folder.strip():
        source_folder=Path(folder)
        if source_folder.is_dir():
            files=sorted((p for p in source_folder.iterdir() if p.is_file() and p.suffix.lower() in PHOTO_EXTENSIONS|VIDEO_EXTENSIONS),key=lambda p:p.name.lower())
            uploads=[SimpleNamespace(name=p.name,getvalue=p.read_bytes) for p in files]
        else: st.warning('Ce dossier est introuvable.')
    remove_black=st.checkbox('Retirer les bandes noires ou colorées',True)
    st.caption('Ne retire pas les barres d’interface, le texte ou les bandes intégrées à la scène. Désactive cette option pour une scène très sombre.')
    st.caption('Les photos restent sur cet ordinateur. Le modèle de détection est téléchargé au premier usage.')

try:
    with st.spinner('Lecture du template…'):
        if path.strip():
            file=Path(path)
            if not file.is_file(): st.info('Ce fichier PSD est introuvable.'); st.stop()
            base,slots=template(str(file),file.stat().st_mtime_ns)
        else:
            base,slots=integrated_template()
except Exception as e:
    st.error('Lecture du template impossible : '+str(e)); st.stop()

if not uploads:
    st.markdown('<span id="planches"></span>',unsafe_allow_html=True)
    preview=label_client(base,client,0); preview.thumbnail((1400,1000))
    draw=ImageDraw.Draw(preview); scale=preview.width/base.width
    for i,slot in enumerate(slots):
        x0,y0,x1,y1=[round(v*scale) for v in slot['box']]
        draw.rectangle((x0,y0,x1,y1),outline='#ef6526',width=3)
        draw.text((x0+8,y0+8),str(i+1),fill='#ef6526',stroke_width=1)
    st.image(preview,caption='Les cadres sont numérotés de gauche à droite, puis de haut en bas.')
    st.markdown('<span id="exports"></span>',unsafe_allow_html=True)
    st.info('Choisis des photos ou un dossier. Les noms de fichiers déterminent l’ordre initial : 01.jpg, 02.jpg…')
    st.stop()

uploads=sorted(uploads,key=lambda f:f.name.lower())
all_uploads=uploads
total=len(uploads); pages=math.ceil(total/10)
with st.sidebar:
    videos=sum(Path(f.name).suffix.lower() in VIDEO_EXTENSIONS for f in uploads)
    st.caption(f'{total} images · {pages} planche(s) · {videos} vidéo(s), première image uniquement.')
dataset_hash=hashlib.sha256()
for f in all_uploads:
    dataset_hash.update(f.name.encode())
    dataset_hash.update(hashlib.sha256(f.getvalue()).digest())
dataset=dataset_hash.hexdigest()[:16]
try:
    with st.spinner(f'Analyse des {total} images avant la composition des planches…'):
        all_info=[analyze(f.getvalue(),remove_black,f.name) for f in all_uploads]
except Exception as e:
    st.error('Une image ne peut pas être analysée : '+str(e)); st.stop()
def render_editor(page):
    uploads=all_uploads[page*10:(page+1)*10]
    real_count=len(uploads)
    if real_count<10:
        blank=BytesIO(); Image.new('RGB',(600,850),'white').save(blank,format='PNG')
        uploads += [SimpleNamespace(name='Cadre vide',getvalue=lambda:blank.getvalue()) for _ in range(10-real_count)]
    settings_key=f'settings_{dataset}_{page}'
    widget_prefix=f'{dataset}_{page}'
    info=all_info[page*10:(page+1)*10]
    while len(info)<10:
        info.append(((0,0,600,850),[],'cadre vide',False))
    if detector().message: st.warning(detector().message)
    subjects=[r[1] for r in info]
    if settings_key not in st.session_state:
        st.session_state[settings_key]=[dict(source=i,zoom=1.,x=0.,y=0.,contain=False) for i in range(10)]

    def apply_canvas_event(event):
        if not isinstance(event,dict) or event.get('token')!=widget_prefix or event.get('id')==st.session_state.get('last_event_'+widget_prefix):
            return
        index=event.get('frame')
        if not isinstance(index,int) or not 0<=index<10:return
        config=st.session_state[settings_key][index];box=slots[index]['box'];idx=config['source']
        if event.get('action')=='reset':
            rect=info[idx][0]
            viewport,_=crop_bounds(SimpleNamespace(size=(rect[2]-rect[0],rect[3]-rect[1])),(box[2]-box[0],box[3]-box[1]),subjects[idx])
            config['viewport']=list(viewport)
            config['rotation']=0.
        else:
            viewport=event.get('viewport')
            if not (isinstance(viewport,list) and len(viewport)==4 and all(isinstance(v,(float,int)) and math.isfinite(v) and abs(v)<1e7 for v in viewport)):return
            w=viewport[2]-viewport[0];h=viewport[3]-viewport[1]
            if w<1 or h<1 or abs(w/h-(box[2]-box[0])/(box[3]-box[1]))>=.001:return
            config['viewport']=viewport
            angle=event.get('rotation',0.)
            if isinstance(angle,(float,int)) and math.isfinite(angle):config['rotation']=float(angle)%360
        st.session_state['last_event_'+widget_prefix]=event.get('id')
        st.session_state['edited_photo_'+widget_prefix]=index

    # Consume the gesture before building the next canvas: one rerun, no extra
    # page refresh that would scroll/jump or briefly restore the previous crop.
    apply_canvas_event(st.session_state.get('canvas_'+widget_prefix))
    with st.sidebar.expander(f'Planche {page+1} · réglages numériques',expanded=False):
        st.header('Ajuster un cadre')
        selected=st.selectbox('Cadre',range(10),format_func=lambda i:f'Photo {i+1}',key=widget_prefix+'_selected')
        st.caption('Chaque cadre conserve ses propres réglages.')
        # Keep settings in independent state: widgets for hidden frames are removed by Streamlit.
        if settings_key not in st.session_state:
            st.session_state[settings_key]=[dict(source=i,zoom=1.,x=0.,y=0.,contain=False) for i in range(10)]
        config=st.session_state[settings_key][selected]
        source=st.selectbox('Photo à placer',range(10),index=config['source'],format_func=lambda i:uploads[i].name,key=f'{widget_prefix}_source_{selected}')
        contain=st.checkbox('Afficher la photo entière sur fond flouté',config['contain'],key=f'{widget_prefix}_contain_{selected}')
        zoom=st.slider('Zoom',1.,3.,float(config['zoom']),.05,key=f'{widget_prefix}_zoom_{selected}',disabled=contain)
        x=st.slider('Déplacement horizontal',-1.,1.,float(config['x']),.02,key=f'{widget_prefix}_x_{selected}',disabled=contain)
        y=st.slider('Déplacement vertical',-1.,1.,float(config['y']),.02,key=f'{widget_prefix}_y_{selected}',disabled=contain)
        updated=dict(config,source=source,zoom=zoom,x=x,y=y,contain=contain)
        if any(updated[k]!=config[k] for k in ('source','zoom','x','y','contain')):
            updated.pop('viewport',None)
        st.session_state[settings_key][selected]=updated
        st.caption(f'Cadrage : {info[source][2]}. Bandes retirées : {"oui" if info[source][3] else "non"}.')

    st.markdown(f'**Planche {page+1} / {pages}**')
    st.text(page_name(client,page))
    background=label_client(base,client,page);background.thumbnail((1600,1200),Image.Resampling.LANCZOS)
    buffer=BytesIO();background.save(buffer,format='PNG');background.close()
    background_url='data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()
    frames=[];clipped=[]
    for index,slot in enumerate(slots):
        config=st.session_state[settings_key][index];idx=config['source']
        width,height,texture=editor_texture(uploads[idx].getvalue(),uploads[idx].name,info[idx][0])
        box=slot['box'];size=(box[2]-box[0],box[3]-box[1])
        auto,_=crop_bounds(SimpleNamespace(size=(width,height)),size,subjects[idx])
        calculated,_=crop_bounds(SimpleNamespace(size=(width,height)),size,subjects[idx],config['zoom'],(config['x'],config['y']),config['contain'])
        viewport=config.get('viewport',calculated)
        if viewport_clips(subjects[idx],viewport,config.get('rotation',0.)):clipped.append(index+1)
        frames.append(dict(box=box,width=width,height=height,image=texture,viewport=viewport,auto=auto,rotation=config.get('rotation',0.)))
    event=a4_editor(token=widget_prefix,width=base.width,height=base.height,background=background_url,frames=frames,key='canvas_'+widget_prefix,default=None)
    apply_canvas_event(event)
    edited=st.session_state.get('edited_photo_'+widget_prefix)
    if edited is not None:
        st.caption(f'Photo {edited+1} : cadrage enregistré et appliqué aux exports de cette planche.')
    if real_count<10: st.caption(f'{10-real_count} cadre(s) laissé(s) blanc(s) sur cette dernière planche.')
    if clipped:
        st.warning(crop_notice(clipped))


st.markdown('<span id="planches"></span>',unsafe_allow_html=True)
st.subheader('Planches de la commande')
st.caption(f'{total} images réparties sur {pages} planche(s) · 10 emplacements par A4')
st.caption('Clic : sélectionner  ·  Glisser : recadrer  ·  Molette : zoom  ·  ↻ : rotation  ·  Ctrl+Z : annuler')
for row_start in range(0,pages,2):
    columns=st.columns(2)
    for offset in range(min(2,pages-row_start)):
        with columns[offset]:
            with st.container(border=True):
                render_editor(row_start+offset)

st.divider()
st.markdown('<span id="exports"></span>',unsafe_allow_html=True)
st.subheader('Exporter la commande')
st.caption('Vérifiez les cadrages signalés avant de préparer les fichiers pour impression.')
formats=st.multiselect('Formats à exporter',['JPG','PDF','PNG'],default=['JPG','PDF'])
st.caption('Le ZIP regroupe toutes les planches et leurs aperçus. Les fichiers portent le nom du client, puis 1, 2, 3…')

def default_settings():
    return [dict(source=i,zoom=1.,x=0.,y=0.,contain=False) for i in range(10)]

all_settings=[st.session_state.get(f'settings_{dataset}_{i}',default_settings()) for i in range(pages)]
signature=hashlib.sha256(json.dumps(dict(dataset=dataset,client=client,trim=remove_black,path=path,template_mtime=Path(path).stat().st_mtime_ns if path.strip() else 0,settings=all_settings,formats=formats),sort_keys=True).encode()).hexdigest()

def rendered_pages():
    for index in range(pages):
        items=all_uploads[index*10:(index+1)*10]
        analyzed=all_info[index*10:(index+1)*10]
        boxes=[r[1] for r in analyzed]
        while len(boxes)<10: boxes.append([])
        def loader(idx):
            return decoded_photo(items[idx],analyzed[idx]) if idx<len(items) else Image.new('RGB',(600,850),'white')
        image,warnings=assemble_lazy(base,slots,loader,boxes,all_settings[index])
        if warnings:
            st.warning('**Planche '+str(index+1)+'** — '+crop_notice(warnings))
        yield index,label_client(image,client,index)

if st.button('Préparer toutes les planches',type='primary',disabled=not formats):
    try:
        with st.spinner(f'Préparation de {pages} planche(s) et des aperçus…'):
            data,previews=export_batch(rendered_pages(),client,formats)
            st.session_state.exports=dict(signature=signature,data=data,previews=previews)
    except Exception as e:
        st.error('Export impossible : '+str(e))

pack=st.session_state.get('exports')
if pack and pack['signature']==signature:
    st.download_button('Télécharger tous les exports (ZIP)',pack['data'],file_name(client)+'_exports.zip','application/zip',on_click='ignore')
    st.caption('Aperçus de toutes les planches exportées · impression PDF à 100 % / taille réelle.')
    for preview_index,(label,data) in enumerate(pack['previews']):
        with st.expander(label,expanded=pages<=3):
            st.image(data,caption=label)
            st.download_button('Télécharger cet aperçu',data,file_name(client,preview_index)+'.jpg','image/jpeg',on_click='ignore',key='preview_'+label)
