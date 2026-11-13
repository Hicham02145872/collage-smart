"""Client labels and multi-page exports, shared by the UI and batch tests."""
from io import BytesIO
from pathlib import Path
import re
import zipfile
from PIL import Image, ImageDraw, ImageFont

def client_name(value):
    return ' '.join(value.split()) or 'Nom client'

def page_name(value,index):
    name=client_name(value)
    return name if index==0 else f'{name} {index}'

def file_name(value,index=0):
    # Keep the page suffix after truncation so distinct pages cannot collide.
    name=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',client_name(value)).strip(' .')[:100].rstrip(' .') or 'Nom client'
    reserved={'CON','PRN','AUX','NUL'}|{f'{p}{n}' for p in ('COM','LPT') for n in range(1,10)}
    if name.split('.')[0].upper() in reserved: name='_'+name
    return name if index==0 else f'{name} {index}'

def label_client(base,value,index):
    result=base.copy();draw=ImageDraw.Draw(result)
    sx=base.width/7425;sy=base.height/5250
    # Text location from the supplied PSD's NOM DE CLIENT layer.
    x,y=round(890*sx),round(4795*sy)
    draw.rectangle((round(880*sx),round(4785*sy),round(7300*sx),round(4955*sy)),fill='white')
    text=page_name(value,index)
    fonts=Path('C:/Windows/Fonts')
    candidates=['arial.ttf'] if any('\u0600'<=c<='\u06ff' for c in text) else ['LHANDW.TTF','segoepr.ttf','ariali.ttf']
    font_path=next((fonts/n for n in candidates if (fonts/n).exists()),None)
    def font_at(size):
        return ImageFont.truetype(str(font_path),size) if font_path else ImageFont.load_default(size=size)
    lo,hi=1,max(2,round(250*sy));chosen=font_at(1)
    while lo<=hi:
        size=(lo+hi)//2;f=font_at(size);box=draw.textbbox((0,0),text,font=f)
        if box[2]-box[0]<=base.width-x-round(200*sx) and box[3]-box[1]<=round(140*sy):
            chosen=f;lo=size+1
        else:hi=size-1
    draw.text((x,y),text,font=chosen,fill='black',anchor='lt')
    return result

def export_image(image,kind):
    landscape=image.width>=image.height
    mmw,mmh=(297,210) if landscape else (210,297)
    if abs(image.width/image.height-mmw/mmh)>.01:
        raise ValueError('Le template ne respecte pas le ratio A4.')
    dpi=image.width/(mmw/25.4);out=BytesIO()
    if kind=='JPG': image.save(out,format='JPEG',quality=97,subsampling=0,dpi=(dpi,dpi))
    elif kind=='PNG': image.save(out,format='PNG',dpi=(dpi,dpi))
    elif kind=='PDF': image.save(out,format='PDF',resolution=dpi)
    else: raise ValueError('Format inconnu : '+kind)
    return out.getvalue()

def export_batch(pages,client,formats=('JPG','PDF')):
    """Consume pages one by one, keeping only small previews in memory."""
    if not formats: raise ValueError('Choisis au moins un format.')
    archive=BytesIO();previews=[]
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_STORED) as z:
        for index,image in pages:
            name=file_name(client,index)
            for kind in formats:
                z.writestr(f'{name}.{kind.lower()}',export_image(image,kind))
            preview=image.copy();preview.thumbnail((1600,1200))
            out=BytesIO();preview.save(out,format='JPEG',quality=94)
            data=out.getvalue()
            z.writestr(f'Apercus/{name}.jpg',data)
            previews.append((page_name(client,index),data))
    return archive.getvalue(),previews
