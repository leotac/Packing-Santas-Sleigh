"""
Packing Santa's Sleigh -- Top-Down Layer approach
General approach: 
- Start from smallest unpacked PresentId
- Count the number N of presents that fit in 1000*1000
- Try packing the first N presents on the same layer (with one or more methods)
- Decrease N until they fit
[- Try bubbling down]
- Move to next layer
"""

import os
import csv
import random
from random import sample

PLOT = False 
if PLOT:
   from matplotlib import cm
   import matplotlib.pyplot as plt
   from mpl_toolkits.mplot3d import Axes3D

SLEIGH_LENGTH = 1000
MAX_LAYERS = 2
TRIES = 1
FRACTION = 4
DEBUG = True
WRITE = True
RATIO = 0.83
GUILL = False

print "Tries:", TRIES
print "Reshuffle fraction:", FRACTION

# Global variables for plotting
xpos, ypos, zpos, dx, dy, dz = [],[],[],[],[],[]
colors = []

#myShuffle(list,3): shuffle first 3 elements
#myShuffle(list,3,None): shuffle from 3 to the end
def myShuffle(x, *s):
   x[slice(*s)] = sample(x[slice(*s)], len(x[slice(*s)]))


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

   """ Pack the presents """
   def pack(self):
      if GUILL:
         return self.guillotine_pack()
      else:
         return self.max_rect_pack()

   """ Compute size of the batch to be sorted """
   def batch_size(self, ratio):
      #batch_size = int(RATIO*len(self.presents))
      batch_size = 0
      cumul_area=0
      for p in self.presents:
         cumul_area += p.area
         if cumul_area < ratio*SLEIGH_LENGTH*SLEIGH_LENGTH:
            batch_size += 1
         else:
            return batch_size
      return batch_size


   ##################################
   ######## Max-Rect Packing ########
   ##################################
   """ Set up Max-Rect packing """
   def max_rect_pack(self):
      ratio = RATIO
      all_presents = self.presents[:]
      sorties = self.batch_size(ratio)
      initial_batch_size = sorties
      if DEBUG:
         print "Layer:",self.id
         print "Batch size:", sorties
      ok = False
      for it in xrange(sorties):
         result = None 
         resultLeftovers = None
         bestScore = 0
         for self.packMode in [0,1]:
            if ok == True:
               break
            for sortMode in xrange(TRIES):
               rect = Rectangle() #entire shelf
               self.free_rectangles = [rect]
               self.used_rectangles = []

               tmp = all_presents[:sorties]
               if sortMode==0:
                  tmp.sort(key= lambda p : p.height, reverse=True)
               elif sortMode==1:
                  tmp.sort(key= lambda p : p.width, reverse=True)
               elif sortMode==2:
                  tmp.sort(key= lambda p : p.area, reverse=True)
               elif sortMode==3:
                  tmp.sort(key= lambda p : p.z_depth, reverse=True)
               elif sortMode>=4:
                  tmp.sort(key= lambda p : p.height, reverse=True)
                  myShuffle(tmp, len(tmp)/FRACTION)

               tmp.extend(all_presents[sorties:])
               self.presents = []
               leftovers = []
               full = False
               for present in tmp:
                  if full == True:
                     leftovers.append(present)
                     continue
                  
                  coord = self.pack_present(present) 
                  if coord is None:
                     full = True
                     leftovers.append(present)
                     continue
                  else:
                     present.xpos = coord.xpos
                     present.ypos = coord.ypos
                     present.zpos = self.z_base
                     # Orientation must be copied too! (should be already ok though)
                     present.width = coord.width
                     present.height = coord.height
                     if present.xpos<1 or present.ypos<1 or present.xpos + present.width - 1 > SLEIGH_LENGTH or present.ypos+present.height -1 > SLEIGH_LENGTH:
                        raise Exception("Out of bounds!")
                     self.presents.append(present)
                     self.z_max = max(self.z_max, present.zpos + present.z_depth - 1)
               self.presents.sort(key= lambda p : p.id, reverse=True)
               leftovers.sort(key= lambda p : p.id, reverse=True)
               if len(leftovers)>0 and self.presents[-1].id < leftovers[0].id:
                  #print "With", sorties,"presents, wrong order of at least ", self.presents[-1].id - leftovers[0].id, self.presents[-1].id,"-",leftovers[0].id
                  #sorties -= 1
                  self.presents = all_presents
                  if DEBUG:
                     print "Mode",sortMode, self.packMode, "failed with", sorties, "sorted presents"
               else:
                  ok = True
                  if DEBUG:
                     print "Mode", sortMode, self.packMode, "found it! Packed presents:", len(self.presents), "with", sorties, "sorted presents"
                     print "Initial size:", initial_batch_size, "iterations:",it
                  result = self.presents[:]
                  resultLeftovers = leftovers[:]
                  bestScore = self.score()
                  break #MUST BREAK OUT! otherwise presents will be rotated or modified by the following cycle iterations!
         if ok == True:
            self.presents = result
            leftovers = resultLeftovers
            break
         else:
            #print "Decrease size"
            sorties -= 1
      if not ok:
         print "NOT OK!", it
      return leftovers

   def try_fit_rectangle(self, lefty):
      z_value = self.z_max - lefty[0].z_depth

      # Build list of free rectangles with at least depth = lefty[0].depth
      rect = Rectangle() #entire shelf
      self.free_rectangles = [rect]
      self.used_rectangles = []
      for p in self.presents:
         if p.zpos+p.z_depth-1 > z_value:
#            print p.id,p.xpos,p.ypos,p.width,p.height
            toDelete= []
            for i,r in enumerate(self.free_rectangles):
               if self.split_rect(r, p):
#                  print "Splitted rectangle", i,r.xpos,r.ypos,r.width,r.height
                  toDelete.append(i)
            #delete from largest
            toDelete.sort(reverse=True)
            for i in toDelete:
               del self.free_rectangles[i]
              
            self.prune_free()

      count = 0
      for presy in lefty:
         if presy.z_depth > lefty[0].z_depth:
            break
         newrect= self.find_position(presy)
         if newrect is not None:
#            print "present:",presy.id,presy.width,presy.height,presy.z_depth
#            print "new rectangle",newrect.xpos, newrect.ypos, newrect.width, newrect.height
#            print "z-position of the present", z_value+1
#            print "z-position of top of the present", z_value + 1 + presy.z_depth - 1
#            print "max", self.z_max
            x1, x2, y1, y2, z1, z2 = newrect.xpos, newrect.xpos+newrect.width-1, newrect.ypos, newrect.ypos + newrect.height-1, z_value+1, z_value + 1 + presy.z_depth - 1
            xpos.append(min(x1,x2))
            presy.xpos = min(x1,x2)
            ypos.append(min(y1,y2))
            presy.ypos = min(y1,y2)
            zpos.append(min(z1,z2))
            presy.zpos = min(z1,z2)
            dx.append(abs(x1-x2))
            dy.append(abs(y1-y2))
            dz.append(abs(z1-z2))
            colors.append("w")
            self.presents.append(presy)
            count += 1
            #detect which free rectangles must be split due to the new present
            toDelete= []
            for i,r in enumerate(self.free_rectangles):
               if self.split_rect(r, newrect):
                  toDelete.append(i)
            #delete from largest
            toDelete.sort(reverse=True)
            for i in toDelete:
               del self.free_rectangles[i]
         else:
            break
      return count


   """ Pack a present with Max-Rect """
   def pack_present(self, present):
      #find the new rectangle where to store the present
      if self.packMode == 0:
         newRect = self.find_position(present)
      elif self.packMode == 1:
         newRect = self.find_positionBAF(present)

      if newRect is None:
         return None
     
      #detect which free rectangles must be split due to the new present
      toDelete= []
      for i,r in enumerate(self.free_rectangles):
         if self.split_rect(r, newRect):
            toDelete.append(i)
      #delete from largest
      toDelete.sort(reverse=True)
      for i in toDelete:
         del self.free_rectangles[i]
     
      self.prune_free()
      self.used_rectangles.append(newRect)
      
      return newRect

   """ Find position, BSSF """
   def find_position(self, present):
      bestRect = Rectangle()
      bestShortSideFit = SLEIGH_LENGTH 
      bestLongSideFit = SLEIGH_LENGTH 

      for i,r in enumerate(self.free_rectangles):
         # Attempt to fit the present
         if r.width >= present.width and r.height >= present.height:
            leftoverHoriz = r.width - present.width
            leftoverVert = r.height - present.height
            shortSideFit = min(leftoverHoriz, leftoverVert)
            longSideFit = max(leftoverHoriz, leftoverVert)

            if shortSideFit < bestShortSideFit or (shortSideFit == bestShortSideFit and longSideFit < bestLongSideFit):
               bestRect.xpos = r.xpos
               bestRect.ypos = r.ypos
               bestRect.width = present.width
               bestRect.height = present.height
               bestShortSideFit = shortSideFit
               bestLongSideFit = longSideFit

         # Try rotating the present 
         if r.width >= present.height and r.height >= present.width:
            present.rotate()
            leftoverHoriz = r.width - present.width
            leftoverVert = r.height - present.height
            shortSideFit = min(leftoverHoriz, leftoverVert)
            longSideFit = max(leftoverHoriz, leftoverVert)

            if shortSideFit < bestShortSideFit or (shortSideFit == bestShortSideFit and longSideFit < bestLongSideFit):
               bestRect.xpos = r.xpos
               bestRect.ypos = r.ypos
               bestRect.width = present.width
               bestRect.height = present.height
               bestShortSideFit = shortSideFit
               bestLongSideFit = longSideFit
            else:
               # if rotating it's not useful, rotate it back!
               present.rotate()

      if bestShortSideFit == SLEIGH_LENGTH:
         return None
      return bestRect

   """ Find position, BAF """
   def find_positionBAF(self, present):
      bestRect = Rectangle()
      bestShortSideFit = SLEIGH_LENGTH 
      bestLongSideFit = SLEIGH_LENGTH 
      bestAreaFit = SLEIGH_LENGTH*SLEIGH_LENGTH

      for i,r in enumerate(self.free_rectangles):
         # Attempt to fit the present
         if r.width >= present.width and r.height >= present.height:
            leftoverHoriz = r.width - present.width
            leftoverVert = r.height - present.height
            shortSideFit = min(leftoverHoriz, leftoverVert)
            longSideFit = max(leftoverHoriz, leftoverVert)
            areaFit = r.area - present.area 

            if areaFit < bestAreaFit or (areaFit == bestAreaFit and shortSideFit < bestShortSideFit):
               bestRect.xpos = r.xpos
               bestRect.ypos = r.ypos
               bestRect.width = present.width
               bestRect.height = present.height
               bestShortSideFit = shortSideFit
               bestLongSideFit = longSideFit
               bestAreaFit = areaFit

         # Try rotating the present 
         if r.width >= present.height and r.height >= present.width:
            present.rotate()
            leftoverHoriz = r.width - present.width
            leftoverVert = r.height - present.height
            shortSideFit = min(leftoverHoriz, leftoverVert)
            longSideFit = max(leftoverHoriz, leftoverVert)
            areaFit = r.area - present.area 

            if areaFit < bestAreaFit or (areaFit == bestAreaFit and shortSideFit < bestShortSideFit):
               bestRect.xpos = r.xpos
               bestRect.ypos = r.ypos
               bestRect.width = present.width
               bestRect.height = present.height
               bestShortSideFit = shortSideFit
               bestLongSideFit = longSideFit
               bestAreaFit = areaFit
            else:
               # if rotating it's not useful, rotate it back!
               present.rotate()

      if bestAreaFit == SLEIGH_LENGTH*SLEIGH_LENGTH:
         return None
      return bestRect

   """ Compute (and delete) the intersection of a selected rectangle with another rectangle """
   def split_rect(self, freeRect, usedRect):
      if not freeRect.overlap(usedRect):
         return False
 
      if (usedRect.xpos <= freeRect.xpos + freeRect.width-1 and usedRect.xpos + usedRect.width-1 >= freeRect.xpos):
        
         # New node at the bottom side of the used rectangle.
         if (usedRect.ypos > freeRect.ypos and usedRect.ypos <= freeRect.ypos + freeRect.height-1):
            #horrible
            newRect = Rectangle()
            newRect.xpos = freeRect.xpos
            newRect.ypos = freeRect.ypos
            newRect.width = freeRect.width
            newRect.height = freeRect.height
            
            newRect.height = usedRect.ypos - newRect.ypos
            self.free_rectangles.append(newRect)

         # New rectangle at the top side of the used rectangle.
         if (usedRect.ypos + usedRect.height < freeRect.ypos + freeRect.height):
            newRect = Rectangle()
            newRect.xpos = freeRect.xpos
            newRect.ypos = freeRect.ypos
            newRect.width = freeRect.width
            newRect.height = freeRect.height
         
            newRect.ypos = usedRect.ypos + usedRect.height
            newRect.height = freeRect.ypos + freeRect.height - (usedRect.ypos + usedRect.height)
            self.free_rectangles.append(newRect)

      if (usedRect.ypos <= freeRect.ypos + freeRect.height-1 and usedRect.ypos + usedRect.height-1 >= freeRect.ypos):
         # New rectangle at the left side of the used rectangle.
         if (usedRect.xpos > freeRect.xpos and usedRect.xpos <= freeRect.xpos + freeRect.width-1):
            newRect = Rectangle()
            newRect.xpos = freeRect.xpos
            newRect.ypos = freeRect.ypos
            newRect.width = freeRect.width
            newRect.height = freeRect.height
        
            newRect.width = usedRect.xpos - newRect.xpos
            self.free_rectangles.append(newRect)

         # New rectangle at the right side of the used rectangle.
         if (usedRect.xpos + usedRect.width < freeRect.xpos + freeRect.width):
            newRect = Rectangle()
            newRect.xpos = freeRect.xpos
            newRect.ypos = freeRect.ypos
            newRect.width = freeRect.width
            newRect.height = freeRect.height
       
            newRect.xpos = usedRect.xpos + usedRect.width
            newRect.width = freeRect.xpos + freeRect.width - (usedRect.xpos + usedRect.width)
            self.free_rectangles.append(newRect)

      return True

   """ Prune redundant rectangles from the list of free rectangles """
   def prune_free(self):
      toDelete = set()
      for i,r in enumerate(self.free_rectangles):
         for j,r2 in enumerate(self.free_rectangles):
            if j>i:
               if r2.contains(r):
                  toDelete.add(i)
                  break
               if r.contains(r2):
                  toDelete.add(j)
      # delete starting from largest
      toDelete=list(toDelete)
      toDelete.sort(reverse=True)
      for i in toDelete:
         del self.free_rectangles[i]
      return

   
   """ Copy presents and sort them decreasingly by tallest z-point they reach (if no compactor, the z_pos term is all the same (z_base), but otherwise it's not). """
   def z_sort_presents(self):
      self.sorted_presents = list(self.presents)
      self.sorted_presents.sort(key= lambda p : (p.zpos+p.z_depth-1), reverse=True)
      return self.sorted_presents
     
   """ Compactor """
   def compact(self, prev_layer):
      #z_min up to current present. then, following presents must not be smaller, they can be equal or greater.
      if prev_layer is not None:
         z_min = prev_layer.z_max+1       
      else:
         z_min = 1
      # z_max must be recomputed (initialized at z_base)
      self.z_max = self.z_base
      for p in sorted(self.presents,reverse=True): #in reverse order of id!
         # presents in the previous layer sorted by decreasing z-height
         if prev_layer is not None:
            for up_p in prev_layer.z_sort_presents():
               if p.overlap(up_p):
                  # this is the tallest overlapping present: you can move down the present, if possible. 
                  # if not possible, break!
                  diff = p.zpos - (up_p.zpos+up_p.z_depth)
                  if diff > 0 and (p.zpos - diff) >= z_min:
                     p.zpos -= diff
                     z_min = max(p.zpos, z_min)
                  break
         else: #First layer.
            diff = p.zpos - 1
            if diff > 0 and (p.zpos - diff) >= z_min:
               p.zpos -= diff
               z_min = max(p.zpos, z_min)
         z_min = max(p.zpos, z_min)
         self.z_max = max(self.z_max, p.zpos + p.z_depth - 1)
      return

   """ Finalize shelf: add coordinates for the plot """
   def finalize_shelf(self):
      if self.id <= MAX_LAYERS:
         for i,p in enumerate(self.presents):
            p.zpos = p.zpos + self.z_max - p.z_depth
            if PLOT:
               x1, x2, y1, y2, z1, z2 = p.xpos, p.xpos+p.width-1, p.ypos, p.ypos + p.height-1, p.zpos, p.zpos + p.z_depth-1
               xpos.append(min(x1,x2))
               ypos.append(min(y1,y2))
               zpos.append(min(z1,z2))
               dx.append(abs(x1-x2))
               dy.append(abs(y1-y2))
               dz.append(abs(z1-z2))
               colors.append(cm.jet(float(i)/len(self.presents)))

   """ Reflect x and y axis """ 
   def reflect_shelf(self):
      #print "Flipping layer", self.id
      for p in self.presents:
         p.xpos = 1 + SLEIGH_LENGTH - (p.xpos + p.width - 1)
         p.ypos = 1 + SLEIGH_LENGTH - (p.ypos + p.height - 1)

   """ Write next line """
   def write_shelf(self, writer):
      for p in self.presents:
         x1, x2, y1, y2, z1, z2 = p.xpos, p.xpos+p.width-1, p.ypos, p.ypos + p.height-1, p.zpos, p.zpos + p.z_depth-1

         list_vertices = [x1, y1, z1]
         list_vertices += [x1, y2, z1]
         list_vertices += [x2, y1, z1]
         list_vertices += [x2, y2, z1]
         list_vertices += [x1, y1, z2]
         list_vertices += [x1, y2, z2]
         list_vertices += [x2, y1, z2]
         list_vertices += [x2, y2, z2]
         writer.writerow([p.id] + list_vertices)
      return 

class Rectangle:
   def __init__(self, w=SLEIGH_LENGTH, h=SLEIGH_LENGTH):
      self.xpos = 1 
      self.ypos = 1
      self.width = w 
      self.height = h 
      self.area = self.width * self.height
 
   def overlap(self, rectangle):
      if (self.xpos+self.width-1) < rectangle.xpos:
         return False
      if self.xpos > (rectangle.xpos+rectangle.width-1):
         return False
      if (self.ypos+self.height-1) < rectangle.ypos:
         return False
      if self.ypos > (rectangle.ypos+rectangle.height-1): 
         return False
      return True

   def contains(self, rectangle):
      if self.xpos <= rectangle.xpos and self.xpos+self.width >= rectangle.xpos+rectangle.width and self.ypos <= rectangle.ypos and self.ypos+self.height >= rectangle.ypos+rectangle.height:
            return True
      else:
            return False

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

   def overlap(self, present):
      # make sure that positions are good, not 0's!

      if (self.xpos+self.width-1) < present.xpos:
         return False
      if self.xpos > (present.xpos+present.width-1):
         return False
      if (self.ypos+self.height-1) < present.ypos:
         return False
      if self.ypos > (present.ypos+present.height-1): 
         return False
      return True

class Tree:
   def __init__(self):
      self.root = Node()

class Node:
   def __init__(self):
      self.child = [None, None]
      self.xpos = SLEIGH_LENGTH 
      self.ypos = SLEIGH_LENGTH 
      self.width = SLEIGH_LENGTH 
      self.height = SLEIGH_LENGTH 
      self.id = None

   def insert(self, present):
      # if not leaf, DFS leftmost child
      if self.child[0] is not None and self.child[1] is not None:
         newNode = self.child[0].insert(present)
         if newNode is not None:
            return newNode
         return self.child[1].insert(present)
      
      # if it's a leaf
      else:
         # if the space is occupied
         if self.id is not None:
            return None
        
         # if the space is too small
#         if self.width < present.width or self.height < present.height:
#            present.rotate()
         if self.width < present.width or self.height < present.height:
#            present.rotate() #rotate it back
            return None

         # if the space is perfect
         if self.width == present.width and self.height == present.height:
            self.id = present.id
            return self

         # if the space is larger,
         # split the space 
         self.child[0] = Node()
         self.child[1] = Node()

         dw = self.width - present.width
         dh = self.height - present.height

         # cut vertically 
         if dw > dh:
            self.child[0].xpos = self.xpos
            self.child[0].ypos = self.ypos
            self.child[0].width = present.width
            self.child[0].height = self.height
            
            self.child[1].xpos = self.xpos - present.width
            self.child[1].ypos = self.ypos
            self.child[1].width = self.width - present.width
            self.child[1].height = self.height
         # cut horizontally
         else:
            self.child[0].xpos = self.xpos
            self.child[0].ypos = self.ypos
            self.child[0].width = self.width 
            self.child[0].height = present.height
            
            self.child[1].xpos = self.xpos
            self.child[1].ypos = self.ypos - present.height
            self.child[1].width = self.width 
            self.child[1].height = self.height - present.height

         # insert in first child
         return self.child[0].insert(present)



if __name__ == "__main__":
    
   path = '.'
   presentsFilename = os.path.join(path, 'presents_revorder.csv')
   submissionFilename = os.path.join(path, 'revoutput.csv')
   print submissionFilename

   # create header for submission file: PresentId, x1,y1,z1, ... x8,y8,z8
   header = ['PresentId']
   for i in xrange(1,9):
       header += ['x' + str(i), 'y' + str(i), 'z' + str(i)]
    
   layer = Layer(1,1,[])
   prev_layer = None
   maxz = 1
   totScore=0.
   layers=0.
   random.seed(1)
   with open(presentsFilename, 'rb') as f:
      with open(submissionFilename, 'wb') as w:
         f.readline() # header
         fcsv = csv.reader(f)
         wcsv = csv.writer(w)
         wcsv.writerow(header) #write header
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

               # the layer is guaranteed to be full. 
               # try to pack and return presents that do not fit
               leftovers = layer.pack()
               
               totScore += layer.score()
               layers+=1
               if DEBUG:
                  print layer.id,"Score:", layer.score(), "Avg:", totScore/layers
               #print "Leftovers",len(leftovers)
               #print layer.id, present.id, float(present.id)/layer.id
              
               # reflect even layers
               if layer.id % 2 == 0:
               #   print "Reflected shelf"
                  layer.reflect_shelf()
               
               layer.finalize_shelf()
               
               # compact shelf down (if possible), preserving order
               layer.compact(prev_layer)
               
#            if len(leftovers)>0:
#               del leftovers[:layer.try_fit_rectangle(leftovers)]
               if WRITE:
                  layer.write_shelf(wcsv)
               
               # open new shelf and add current present
               cumul_area = sum(p.area for p in leftovers)
               prev_layer = layer
               if layer.id >= MAX_LAYERS:
                  break
               layer = Layer(prev_layer.id+1, prev_layer.z_max+1, leftovers)
               added_present = layer.add_present(present)

            if not added_present:
               print "Something wrong"

         if added_present == True:
               # rows are over. 
               # last layer was not "full" (area-wise), so it has not been packed yet!
               print "Packing last layer?"
               leftovers = layer.pack()
               #however, it can still have leftovers
               if len(leftovers)>0: 
                  prev_layer = layer
                  layer = Layer(prev_layer.id+1, prev_layer.z_max+1, leftovers)
                  print "Packing leftovers", len(leftovers)
                  leftovers = layer.pack()
                  if len(leftovers) > 0:
                     print "even more leftovers!"

   print "Max z =", maxz
   print "Last present packed", layer.presents[-1].id

   print 'Done'
