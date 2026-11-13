"""Regression checks for the two reported face-framing failures."""
import threading
import unittest
import numpy as np
from PIL import Image
from core import Detector,crop_photo,assemble

class Faces:
    def __init__(self,boxes): self.boxes=boxes
    def setInputSize(self,size): pass
    def detect(self,image):
        rows=np.zeros((len(self.boxes),15),np.float32)
        for row,box in zip(rows,self.boxes): row[:4]=box;row[-1]=.95
        return None,rows

class Body:
    def infer(self,image):
        # Only the person on the right is found by the body detector.
        return np.array([[230,80,410,415,.9,0]])

def detector(boxes):
    d=Detector.__new__(Detector)
    d.face=Faces(boxes);d.person=Body();d.lock=threading.Lock()
    return d

class FramingTests(unittest.TestCase):
    def test_rotation_is_applied_inside_fixed_export_rectangle(self):
        a=np.zeros((100,100,3),np.uint8);a[:,:50]=[255,0,0];a[:,50:]=[0,0,255]
        result,_=crop_photo(Image.fromarray(a),(100,100),viewport=[0,0,100,100],rotation=90)
        b=np.asarray(result)
        self.assertGreater(b[10,50,0],240)
        self.assertGreater(b[90,50,2],240)
        self.assertEqual(result.size,(100,100))

    def test_manual_export_never_changes_pixels_outside_placeholder(self):
        base=Image.new('RGB',(300,400),'white')
        source=Image.fromarray(np.random.default_rng(9).integers(0,255,(900,1200,3),dtype=np.uint8))
        config=dict(source=0,zoom=1.,x=0.,y=0.,contain=False,viewport=[200.,100.,600.,700.])
        result,_=assemble(base,[dict(box=(30,40,130,190))],[source],[[]],[config])
        a=np.asarray(result);outside=np.ones(a.shape[:2],bool);outside[40:190,30:130]=False
        self.assertTrue(np.all(a[outside]==255))
        expected,_=crop_photo(source,(100,150),viewport=config['viewport'])
        self.assertTrue(np.array_equal(a[40:190,30:130],np.asarray(expected)))

    def test_manual_viewport_is_exactly_the_export_crop(self):
        image=Image.fromarray(np.random.default_rng(3).integers(0,255,(900,1200,3),dtype=np.uint8))
        viewport=[200.,100.,600.,700.]
        expected=image.transform((400,600),Image.Transform.EXTENT,viewport,Image.Resampling.BICUBIC)
        actual,_=crop_photo(image,(400,600),viewport=viewport)
        self.assertTrue(np.array_equal(np.asarray(expected),np.asarray(actual)))
        with self.assertRaises(ValueError): crop_photo(image,(400,600),viewport=[0,0,600,600])

    def test_wide_group_fills_rectangle_without_white_bands(self):
        image=Image.new('RGB',(1200,600),(40,90,160))
        subjects=[(0,50,400,500),(800,50,1200,500)]
        for contain in (False,True):
            result,clipped=crop_photo(image,(600,850),subjects,contain=contain)
            self.assertEqual(result.size,(600,850))
            self.assertFalse(clipped)
            self.assertLess(np.asarray(result).max(),200)

    def test_face_without_detected_body_is_retained(self):
        image=Image.new('RGB',(1000,1000),'grey')
        subjects,method=detector([(650,200,160,180),(100,100,180,220)]).detect(image)
        self.assertLess(min(s[0] for s in subjects),100)
        result,clipped=crop_photo(image,(600,850),subjects)
        self.assertFalse(clipped)

    def test_wide_selfie_uses_faces_instead_of_full_body(self):
        image=Image.new('RGB',(1000,600),'grey')
        subjects,method=detector([(400,100,150,180)]).detect(image)
        self.assertIn('selfie horizontal',method)
        self.assertEqual(len(subjects),1)
        result,clipped=crop_photo(image,(600,850),subjects)
        self.assertFalse(clipped)
        white=(np.asarray(result).min(axis=2)>250).mean()
        self.assertLess(white,.1)

if __name__=='__main__': unittest.main()
