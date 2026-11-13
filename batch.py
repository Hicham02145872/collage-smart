"""Generate all A4 pages from a local folder, without the browser UI."""
import argparse
import io
import json
from pathlib import Path
import zipfile
from PIL import Image
from core import ROOT,PHOTO_EXTENSIONS,VIDEO_EXTENSIONS,read_media,trim_borders,Detector,assemble_lazy,render_template
from exporting import client_name,file_name,label_client,export_batch

def generate(folder,client,destination,formats=('JPG','PDF'),rotations=None):
    source=Path(folder);destination=Path(destination)
    files=sorted((p for p in source.iterdir() if p.is_file() and p.suffix.lower() in PHOTO_EXTENSIONS|VIDEO_EXTENSIONS),key=lambda p:p.name.lower())
    if not files: raise ValueError('Le dossier ne contient aucune image ou video compatible.')
    client=client_name(client)
    destination.mkdir(parents=True,exist_ok=True)
    base,slots=render_template()
    detector=Detector();report=[];prepared=[]
    # Finish analysis for the complete folder before composing any page.
    for number,path in enumerate(files):
        image=read_media(path.read_bytes(),path.name)
        rotation=(rotations or {}).get(path.name,0)
        if rotation: image=image.rotate(rotation,expand=True)
        clean,box=trim_borders(image)
        found,method=detector.detect(clean)
        prepared.append((box,found))
        report.append(dict(file=path.name,page=number//10+1,rotation=rotation,original=list(image.size),retained_box=box,subjects=found,method=method))
        clean.close();image.close()
        print(f'Analyse {number+1}/{len(files)} : {path.name}, rotation {rotation}, {method}',flush=True)
    print('Analyse complete. Composition des planches.',flush=True)
    def pages():
        for page,start in enumerate(range(0,len(files),10)):
            subjects=[found for box,found in prepared[start:start+10]]
            while len(subjects)<10:subjects.append([])
            def loader(idx):
                number=start+idx
                if number>=len(files): return Image.new('RGB',(600,850),'white')
                path=files[number];image=read_media(path.read_bytes(),path.name)
                angle=(rotations or {}).get(path.name,0)
                if angle:
                    turned=image.rotate(angle,expand=True);image.close();image=turned
                box=prepared[number][0]
                if box!=(0,0,*image.size):
                    cropped=image.crop(box);image.close();image=cropped
                return image
            settings=[dict(source=i,zoom=1.,x=0.,y=0.,contain=False) for i in range(10)]
            image,warnings=assemble_lazy(base,slots,loader,subjects,settings)
            print(f'Planche {page+1}: {len(files[start:start+10])} images; cadres a verifier: {warnings}',flush=True)
            yield page,label_client(image,client,page)
    data,previews=export_batch(pages(),client,formats)
    archive=destination/(file_name(client)+'_exports.zip')
    archive.write_bytes(data)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            target=(destination/name).resolve()
            if not target.is_relative_to(destination.resolve()): raise ValueError('Chemin ZIP invalide.')
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(z.read(name))
    return archive,report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Collage A4, dix images par planche, premiere image des videos.')
    parser.add_argument('--folder',required=True)
    parser.add_argument('--client',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    archive,report=generate(args.folder,args.client,args.output)
    print(f'{len(report)} images exportees : {archive}',flush=True)
