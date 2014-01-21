"""
Packing Santa's Sleigh -- Compute lower bound for the Top-Down Layer approach
"""

import os
import csv

SLEIGH_LENGTH = 1000
MAX_LAYERS = 999999 
DEBUG = False

class Layer:
   """ Object to keep track of present position and max extent in sleigh so far. """    
   def __init__(self, id, zbase, leftovers):
        self.id = id
        self.z_base = zbase 
        self.z_max = zbase 
        self.presents = []
        self.presents.extend(leftovers)

   """ Density score """
   def score(self):
      return 100.*sum(p.area for p in self.presents)/(SLEIGH_LENGTH*SLEIGH_LENGTH)

   """ Add present to layer """
   def add_present(self, present):
      self.presents.append(present)
      self.z_max = max(self.z_max, self.z_base + present.z_depth - 1)
      return True


class Present:
   def __init__(self, row):
      self.id = int(row[0])
      dim = [int(x) for x in row[1:]]
      dim.sort()
      self.width = dim[0]     # along x-axis 
      self.height = dim[1]    # along y-axis
      self.z_depth = dim[2]   # along z-axis
      self.area = self.width * self.height
      self.xpos = 0
      self.ypos = 0
      self.zpos = 0
  
   # rotate on the x-y plane
   def rotate(self):
      self.width, self.height = self.height, self.width
      # should also change positions? it's not univocal.

if __name__ == "__main__":
   path = '.'
   presentsFilename = os.path.join(path, 'presents.csv')
    
   layer = Layer(1,1,[])
   prev_layer = None
   maxz = 1
   totScore=0.
   layers=0.
   with open(presentsFilename, 'rb') as f:
         f.readline() # header
         fcsv = csv.reader(f)
         cumul_area = 0
         for row in fcsv:
            if int(row[0])%5000 == 0:
               print row[0], "layer:", layer.id, "height:",layer.z_max,"avg:", 0 if layers==0 else totScore/layers

            present = Present(row)

            added_present = False
            if cumul_area + present.area <= SLEIGH_LENGTH*SLEIGH_LENGTH:
               cumul_area += present.area
               added_present = layer.add_present(present) 
            
            if not added_present:

               totScore += layer.score()
               layers+=1
               if DEBUG:
                  print layer.id,"Score:", layer.score(), "Avg:", totScore/layers
               
               # open new shelf and add current present
               cumul_area = 0
               prev_layer = layer
               if layer.id >= MAX_LAYERS:
                  break
               layer = Layer(prev_layer.id+1, prev_layer.z_max+1, [])
               added_present = layer.add_present(present)
               cumul_area += present.area

   maxz = layer.z_max

   print "Max z =", maxz
   print "Metric =", 2*maxz
   print "Last present packed", layer.presents[-1].id
   print 'Done'
