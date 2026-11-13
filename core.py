"""Collage local : rendu PSD conserve, detection YuNet et recadrage contraint."""
from pathlib import Path
from io import BytesIO
import urllib.request
import threading
import tempfile
import json
import numpy as np
import cv2
from PIL import Image, ImageOps, ImageFilter
from psd_tools import PSDImage

ROOT = Path(__file__).resolve().parent
MODEL_URL = 'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx'
VIDEO_EXTENSIONS={'.mp4','.mov','.avi','.mkv','.webm','.m4v'}
PHOTO_EXTENSIONS={'.jpg','.jpeg','.png','.webp','.tif','.tiff'}

def line_stats(a,axis,threshold=28):
    """Bound float working arrays to 32 scanlines, never a whole photograph."""
    view=a if axis==1 else np.swapaxes(a,0,1)
    n=len(view); variation=np.empty(n,np.float32);means=np.empty((n,3),np.float32);dark=np.empty(n,np.float32)
    for start in range(0,n,32):
        block=view[start:start+32]
        variation[start:start+32]=np.std(block,axis=1,dtype=np.float32).max(axis=1)
        means[start:start+32]=np.mean(block,axis=1,dtype=np.float32)
        dark[start:start+32]=(np.max(block,axis=2)<=threshold).mean(axis=1)
    return variation,means,dark

def render_template():
    """Exact A4 ratio at 304.8 dpi; one shared 27 MB canvas, not 117 MB copies."""
    compact=ROOT/'template'/'base-print.png'
    if compact.exists():
        with Image.open(compact) as image: base=image.convert('RGB')
    else:
        with Image.open(ROOT/'template'/'base.png') as image:
            image.thumbnail((3564,2520),Image.Resampling.LANCZOS)
            base=image.convert('RGB')
    slots=json.loads((ROOT/'template'/'slots.json').read_text(encoding='utf-8'))
    for slot in slots:
        slot['box']=tuple(round(v*base.width/7425) for v in slot['box'])
    return base,slots

def read_photo(data):
    with Image.open(BytesIO(data)) as im:
        return ImageOps.exif_transpose(im).convert('RGB')

def read_media(data,filename='photo.jpg'):
    """For video, decode precisely the first frame, without seeking/skipping."""
    extension=Path(filename).suffix.lower()
    if extension not in VIDEO_EXTENSIONS:
        return read_photo(data)
    temporary=None; capture=None
    try:
        with tempfile.NamedTemporaryFile(suffix=extension,delete=False) as stream:
            temporary=Path(stream.name)
            stream.write(data)
        capture=cv2.VideoCapture(str(temporary))
        ok,frame=capture.read()
        if not ok or frame is None:
            raise ValueError(f'Premiere image illisible dans la video : {filename}')
        return Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
    finally:
        if capture is not None: capture.release()
        if temporary is not None: temporary.unlink(missing_ok=True)

def trim_black(im, threshold=28):
    """Only trim contiguous nearly uniform dark rows/columns connected to edges.

    A transition and a maximum removed area guard against dark scenes. This
    deliberately does not attempt to erase screenshot UI or embedded captions.
    """
    a=np.asarray(im)
    def edges(axis):
        variation,_,fraction=line_stats(a,axis,threshold)
        flat=(fraction>=0.985)&(variation<12)
        n=len(flat); lo=0; hi=n
        while lo<n and flat[lo]: lo+=1
        while hi>lo and flat[hi-1]: hi-=1
        # Very thin edges, or a dark scene filling most of the frame: retain.
        lo=lo if 3<=lo<=n*.28 else 0
        hi=hi if 3<=n-hi<=n*.28 else n
        return lo,hi
    y0,y1=edges(1); x0,x1=edges(0)
    if (x1-x0)*(y1-y0)<im.width*im.height*.5:
        return im,(0,0,im.width,im.height)
    box=(x0,y0,x1,y1)
    return im.crop(box),box

def trim_borders(im):
    """Black edges plus paired uniform screenshot bands, including gradients."""
    clean,box=trim_black(im)
    a=np.asarray(clean)
    offsets=[0,0,clean.width,clean.height]
    for axis in (1,0):
        # A colored band may change color along its height, but is flat across
        # each scanline. Require TWO opposing bands and sharp transitions.
        variation,means,_=line_stats(a,axis)
        flat=variation<5
        n=len(flat); lo=0; hi=n
        while lo<n and flat[lo]: lo+=1
        while hi>lo and flat[hi-1]: hi-=1
        if not (.015*n<=lo<=.22*n and .015*n<=n-hi<=.22*n): continue
        def transition(k):
            return np.linalg.norm(means[max(0,k-4)]-means[min(n-1,k+4)])
        changes=(transition(lo),transition(hi))
        if min(changes)<12 or max(changes)<25: continue
        if np.median(variation[lo:min(hi,lo+12)])<6: continue
        if np.median(variation[max(lo,hi-12):hi])<6: continue
        if axis==1:
            offsets[1]=lo; offsets[3]=hi
        else:
            offsets[0]=lo; offsets[2]=hi
    x0,y0,x1,y1=offsets
    combined=(box[0]+x0,box[1]+y0,box[0]+x1,box[1]+y1)
    return im.crop(combined),combined

def load_template(path):
    psd=PSDImage.open(path)
    # Cached Photoshop composite, rather than re-rendering its text/effects.
    base=psd.topil()
    if base is None:
        raise ValueError('Le PSD ne contient pas de rendu integre. Le re-enregistrer avec la compatibilite maximale dans Photoshop.')
    base=base.convert('RGB')
    slots=[]
    for group in psd.descendants():
        if not group.is_group(): continue
        candidates=[]
        for layer in group:
            if layer.name.lower().startswith('rectangle 2') and layer.vector_mask:
                x0,y0,x1,y1=layer.vector_mask.bbox
                rect=tuple(round(v*d) for v,d in zip((x0,y0,x1,y1),(psd.width,psd.height,psd.width,psd.height)))
                if rect[2]>rect[0] and rect[3]>rect[1]: candidates.append(rect)
        if len(candidates)==2:
            # Align to the actual dark placeholder in the cached rendering.
            # The two PSD paths differ by a few pixels in this template.
            union=(max(0,min(r[0] for r in candidates)-3),max(0,min(r[1] for r in candidates)-3),min(psd.width,max(r[2] for r in candidates)+3),min(psd.height,max(r[3] for r in candidates)+3))
            patch=np.asarray(base.crop(union))
            dark=(np.max(patch,axis=2)<50).astype(np.uint8)
            n,labels,stats,centers=cv2.connectedComponentsWithStats(dark,8)
            if n<2: raise ValueError('Rectangle photo noir introuvable dans le rendu du PSD.')
            component=stats[1:][np.argmax(stats[1:,cv2.CC_STAT_AREA])]
            px,py,pw,ph,area=map(int,component)
            if area<pw*ph*.95: raise ValueError('Le placeholder ne semble pas etre un rectangle noir uni.')
            rect=(union[0]+px,union[1]+py,union[0]+px+pw,union[1]+py+ph)
            if not (0<=rect[0]<rect[2]<=psd.width and 0<=rect[1]<rect[3]<=psd.height):
                raise ValueError('Un cadre depasse la page.')
            slots.append({'name':group.name,'box':rect})
    if len(slots)!=10:
        raise ValueError(f'{len(slots)} cadres trouves au lieu de 10. Ce lecteur est adapte au template polaroid fourni.')
    # Reading order, tolerant of the small vertical differences between frames.
    row_tolerance=min(s['box'][3]-s['box'][1] for s in slots)*.5
    ordered=[]
    for slot in sorted(slots,key=lambda s:s['box'][1]):
        for row in ordered:
            if abs(slot['box'][1]-row[0]['box'][1])<row_tolerance:
                row.append(slot); break
        else: ordered.append([slot])
    slots=[s for row in ordered for s in sorted(row,key=lambda s:s['box'][0])]
    return base,slots

class Detector:
    def __init__(self):
        self.lock=threading.Lock()
        self.face=None
        self.message=''
        model=ROOT/'models'/'face_detection_yunet_2023mar.onnx'
        try:
            if not model.exists():
                model.parent.mkdir(exist_ok=True)
                with urllib.request.urlopen(MODEL_URL,timeout=120) as r:
                    data=r.read()
                if len(data)<100000: raise ValueError('Modele incomplet')
                temporary=model.with_suffix('.tmp'); temporary.write_bytes(data); temporary.replace(model)
            self.face=cv2.FaceDetectorYN.create(str(model),'',(640,640),0.75,0.3,5000)
        except Exception as e:
            self.message='YuNet indisponible : '+str(e)+'. Detection de personnes seulement.'
        self.hog=cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        self.person=None
        person_model=ROOT/'models'/'object_detection_nanodet_2022nov.onnx'
        if person_model.exists():
            from nanodet import NanoDet
            self.person=NanoDet(str(person_model),prob_threshold=.35)

    def detect(self,im):
        with self.lock:
            return self._detect(im)

    def _detect(self,im):
        scale=min(1,1000/max(im.size))
        small=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))))
        a=cv2.cvtColor(np.asarray(small),cv2.COLOR_RGB2BGR)
        faces=[]
        if self.face:
            self.face.setInputSize((small.width,small.height))
            _,found=self.face.detect(a)
            if found is not None:
                for f in found:
                    x,y,w,h=map(float,f[:4])
                    # Include hair and a little breathing space around faces.
                    faces.append((max(0,(x-.2*w)/scale),max(0,(y-.4*h)/scale),min(im.width,(x+1.2*w)/scale),min(im.height,(y+1.3*h)/scale)))
        if faces:
            largest=max((f[2]-f[0])*(f[3]-f[1]) for f in faces)
            # Small distant faces need not control the crop, but every face of
            # comparable size must be protected, even without a detected body.
            faces=[f for f in faces if (f[2]-f[0])*(f[3]-f[1])>=largest*.20]
            # Wide close-up selfies: a body box often spans arms and most of the
            # frame. Frame around faces rather than creating huge white margins.
            if im.width>im.height and largest/(im.width*im.height)>.025:
                return faces,'visages (selfie horizontal)'
        if self.person:
            scale_person=min(416/im.width,416/im.height)
            pw,ph=round(im.width*scale_person),round(im.height*scale_person)
            ox,oy=(416-pw)//2,(416-ph)//2
            letterbox=np.full((416,416,3),114,dtype=np.uint8)
            letterbox[oy:oy+ph,ox:ox+pw]=cv2.cvtColor(np.asarray(im.resize((pw,ph))),cv2.COLOR_RGB2BGR)
            predictions=self.person.infer(letterbox)
            persons=[]
            for row in predictions:
                if int(row[5])!=0 or row[4]<.60: continue
                x0,y0,x1,y1=map(float,row[:4])
                bounds=[max(0,(x0-ox)/scale_person),max(0,(y0-oy)/scale_person),min(im.width,(x1-ox)/scale_person),min(im.height,(y1-oy)/scale_person)]
                # Associate faces with a confident body; ignore faces printed on
                # background posters when a foreground body is present.
                matched=[f for f in faces if bounds[0]<=(f[0]+f[2])/2<=bounds[2] and bounds[1]-50<=(f[1]+f[3])/2<=bounds[3]]
                if matched:
                    bounds=[min(bounds[0],min(f[0] for f in matched)),min(bounds[1],min(f[1] for f in matched)),max(bounds[2],max(f[2] for f in matched)),max(bounds[3],max(f[3] for f in matched))]
                persons.append(tuple(bounds))
            if persons:
                return persons+faces,'silhouette (NanoDet) + visages proteges' if faces else 'silhouette (NanoDet)'
        if faces: return faces,'visages'
        if small.width>=64 and small.height>=128:
            rects,weights=self.hog.detectMultiScale(a,winStride=(8,8),padding=(8,8),scale=1.05)
            persons=[(x/scale,y/scale,(x+w)/scale,(y+h)/scale) for (x,y,w,h),score in zip(rects,weights) if float(score)>.5]
            if persons: return persons,'personnes'
        return [],'centre (aucun sujet detecte)'

def crop_bounds(im,size,subjects=(),zoom=1.0,pan=(0,0),contain=False):
    tw,th=size; w,h=im.size
    ratio=tw/th
    if contain:
        cw=max(w,h*ratio);ch=cw/ratio
        return ((w-cw)/2,(h-ch)/2,(w+cw)/2,(h+ch)/2),False
    cw=min(w,h*ratio)/zoom; ch=cw/ratio
    if subjects:
        x0=min(s[0] for s in subjects); y0=min(s[1] for s in subjects)
        x1=max(s[2] for s in subjects); y1=max(s[3] for s in subjects)
        cx=(x0+x1)/2; cy=(y0+y1)/2
        if not contain:
            # Automatic composition: remove excessive ceiling/empty background,
            # preserve full silhouettes, and use a blurred photo background if
            # the subject cannot physically fit in a full-bleed crop.
            maximum_height=min(h,w/ratio)
            needed=max(y1-y0,(x1-x0)/ratio)
            preferred=max(y1-y0+.08*h,(x1-x0+.08*w)/ratio)
            ch=max(maximum_height/1.7,min(maximum_height,preferred),needed)/zoom
            cw=ch*ratio
        # If the union fits, constrain the crop to keep every detected face.
        lx=max(0,x1-cw); hx=min(w-cw,x0)
        ly=max(0,y1-ch); hy=min(h-ch,y0)
    else:
        cx=w/2; cy=h/2; lx=ly=1; hx=hy=0
    x=max(0,min(w-cw,cx-cw/2)) if cw<=w else (w-cw)/2
    y=max(0,min(h-ch,cy-ch/2)) if ch<=h else (h-ch)/2
    if lx<=hx: x=max(lx,min(hx,x))
    if ly<=hy: y=max(ly,min(hy,y))
    if pan[0]: x=max(min(0,w-cw),min(max(0,w-cw),x+pan[0]*abs(w-cw)/2))
    if pan[1]: y=max(min(0,h-ch),min(max(0,h-ch),y+pan[1]*abs(h-ch)/2))
    clipped=any(s[0]<x-.5 or s[1]<y-.5 or s[2]>x+cw+.5 or s[3]>y+ch+.5 for s in subjects)
    return (x,y,x+cw,y+ch),clipped

def viewport_clips(subjects,viewport,rotation=0.):
    import math
    x,y,x1,y1=viewport;cx=(x+x1)/2;cy=(y+y1)/2
    co=math.cos(math.radians(rotation));si=math.sin(math.radians(rotation))
    for a,b,c,d in subjects:
        for sx,sy in ((a,b),(a,d),(c,b),(c,d)):
            dx=sx-cx;dy=sy-cy
            if abs(co*dx-si*dy)>(x1-x)/2+.5 or abs(si*dx+co*dy)>(y1-y)/2+.5:return True
    return False

def crop_photo(im,size,subjects=(),zoom=1.0,pan=(0,0),contain=False,viewport=None,rotation=0.):
    tw,th=size;w,h=im.size
    if viewport is None:
        viewport,clipped=crop_bounds(im,size,subjects,zoom,pan,contain)
    else:
        if len(viewport)!=4 or not all(np.isfinite(float(v)) for v in viewport):
            raise ValueError('Cadrage invalide.')
        x,y,x1,y1=map(float,viewport)
        if x1-x<1 or y1-y<1 or abs((x1-x)/(y1-y)-tw/th)>.001:
            raise ValueError('Le cadrage doit respecter le ratio du rectangle.')
        clipped=any(s[0]<x-.5 or s[1]<y-.5 or s[2]>x1+.5 or s[3]>y1+.5 for s in subjects)
    x,y,x1,y1=viewport;cw=x1-x;ch=y1-y
    if rotation:
        import math
        if not math.isfinite(rotation):raise ValueError('Rotation invalide.')
        theta=math.radians(rotation);scale=cw/tw
        a=math.cos(theta)*scale;b=math.sin(theta)*scale
        d=-math.sin(theta)*scale;e=math.cos(theta)*scale
        affine=(a,b,(x+x1)/2-a*tw/2-b*th/2,d,e,(y+y1)/2-d*tw/2-e*th/2)
        result=ImageOps.fit(im,(tw,th),Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(max(tw,th)/24))
        foreground=im.convert('RGBA').transform((tw,th),Image.Transform.AFFINE,affine,Image.Resampling.BICUBIC,fillcolor=(0,0,0,0))
        result.paste(foreground,(0,0),foreground.getchannel('A'));foreground.close()
        return result,viewport_clips(subjects,viewport,rotation)
    if x<0 or y<0 or x+cw>w or y+ch>h:
        # Fill every pixel of the original photo rectangle, keeping the sharp
        # foreground isotropically scaled and the protected faces intact.
        result=ImageOps.fit(im,(tw,th),Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(max(tw,th)/24))
        foreground=im.convert('RGBA').transform((tw,th),Image.Transform.EXTENT,(x,y,x+cw,y+ch),Image.Resampling.BICUBIC,fillcolor=(0,0,0,0))
        result.paste(foreground,(0,0),foreground.getchannel('A'))
        return result,clipped
    result=im.transform((tw,th),Image.Transform.EXTENT,(x,y,x+cw,y+ch),Image.Resampling.BICUBIC,fillcolor='white')
    return result,clipped

def assemble(base,slots,photos,subjects,settings):
    result=base.copy(); warnings=[]
    for i,slot in enumerate(slots):
        config=settings[i]; idx=config['source']; box=slot['box']
        photo,clipped=crop_photo(photos[idx],(box[2]-box[0],box[3]-box[1]),subjects[idx],config['zoom'],(config['x'],config['y']),config['contain'],config.get('viewport'),config.get('rotation',0.))
        result.paste(photo,box[:2])
        if clipped: warnings.append(i+1)
    return result,warnings

def assemble_lazy(base,slots,loader,subjects,settings):
    """Decode and release ONE source at a time, including during exports."""
    result=base.copy();warnings=[]
    for i,slot in enumerate(slots):
        config=settings[i];idx=config['source'];box=slot['box']
        source=loader(idx)
        try:
            photo,clipped=crop_photo(source,(box[2]-box[0],box[3]-box[1]),subjects[idx],config['zoom'],(config['x'],config['y']),config['contain'],config.get('viewport'),config.get('rotation',0.))
            result.paste(photo,box[:2]);photo.close()
            if clipped: warnings.append(i+1)
        finally: source.close()
    return result,warnings
