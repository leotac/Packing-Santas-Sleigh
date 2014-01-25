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
import time
from random import sample

PLOT = False 
if PLOT:
   from matplotlib import cm
   import matplotlib.pyplot as plt
   from mpl_toolkits.mplot3d import Axes3D

SLEIGH_LENGTH = 1000
MAX_LAYERS = 9999
TRIES = 5000
FRACTION = 6
DEBUG = False
WRITE = True
RATIO = 1
GUILL = False

print "Tries:", TRIES
print "Reshuffle fraction:", FRACTION
print "Without try-refitting"
print "With smarter randomization"

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
        self.lefty_base = zbase 
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
            bestSoFar = initial_batch_size
            bestList = []
            nonimproving = 0
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
                  if sortMode == 4:
                     tmp.sort(key= lambda p : p.height, reverse=True)
                     bestList = tmp[:]
                  if nonimproving > 20:
                     #print "20 nonimproving, shuffling more"
                     myShuffle(tmp, len(tmp)/FRACTION)
                  tmp = bestList[:]
                  myShuffle(tmp, len(tmp)/(FRACTION*2))

               tmp.extend(all_presents[sorties:])
               self.presents = []
               leftovers = []
               self.z_max = self.z_base + 1
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
               self.presents.sort(key= lambda p : p.id)
               leftovers.sort(key= lambda p : p.id)
               if len(leftovers)>0 and self.presents[-1].id > leftovers[0].id:
                  #print "With", sorties,"presents, wrong order of at least ", self.presents[-1].id - leftovers[0].id, self.presents[-1].id,"-",leftovers[0].id
                  #sorties -= 1
                  if len(leftovers) < bestSoFar:
                     bestSoFar = len(leftovers)
                     if DEBUG:
                        print "Best so far is", bestSoFar, "leftovers"
                     bestList = tmp[:sorties]
                     nonimproving = 0
                  else:
                     nonimproving += 1
                  self.presents = all_presents
                  #if DEBUG:
                  #   print "Mode",sortMode, self.packMode, "failed with", sorties, "sorted presents"
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
            #print "present",presy.id, "coordinates:", presy.xpos, presy.ypos, presy.xpos+presy.width, presy.ypos+presy.height
            self.presents.append(presy)
            self.lefty_base = max(self.lefty_base, presy.zpos)
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

   """ Guillotine packing """
   def guillotine_pack(self):
      self.tree = Tree()
      
      sorties = self.batch_size(RATIO)
      
      tmp = self.presents[:sorties]
      tmp.sort(key= lambda p : p.area, reverse=True)
      tmp.extend(self.presents[sorties:])
      self.presents = []
      leftovers = []
      full = False
      for present in tmp:
         if full == True:
            leftovers.append(present)
            continue
         
         coordinates = self.guillotine_pack_present(present) 
         
         if coordinates is None:
            full = True
#            print "First leftover", present.id
            leftovers.append(present)
            continue
         else:
            [x1, x2, y1, y2, z1, z2] = coordinates
            present.xpos = min(x1,x2)
            present.ypos = min(y1,y2)
            present.zpos = min(z1,z2)
            self.presents.append(present)
            self.z_max = max(self.z_max, present.zpos + present.z_depth - 1)
#      print [p.id for p in leftovers]
      self.presents.sort(key= lambda p : p.id)
      leftovers.sort(key= lambda p : p.id)
      #print "last packed", self.presents[-1].id
      #print "first leftover", leftovers[0].id
      if len(leftovers)>0 and self.presents[-1].id > leftovers[0].id:
         print "wrong order of at least ", self.presents[-1].id - leftovers[0].id
      return leftovers

   """ Try to pack a present in this layer """ 
   def guillotine_pack_present(self, present):
      leaf = self.tree.root.insert(present)
      #print tree
      if leaf is None:
         present.rotate()
         leaf = self.tree.root.insert(present)

      if leaf is None:
         # Really no space! Rotate it back
         present.rotate()
         return None
         #open a new layer!
         #layer.z_base = layer.z_max + 1
         #tree.root = Node()
         #leaf = tree.root.insert(present)

      x1 = leaf.xpos
      x2 = leaf.xpos - leaf.width + 1
      y1 = leaf.ypos
      y2 = leaf.ypos - leaf.height + 1 
      z1 = self.z_base 
      z2 = z1 + present.z_depth - 1

      return [x1, x2, y1, y2, z1, z2]

   
   """ Copy presents and sort them decreasingly by tallest z-point they reach (if no compactor, the z_pos term is all the same (z_base), but otherwise it's not). """
   def z_sort_presents(self):
      self.sorted_presents = list(self.presents)
      self.sorted_presents.sort(key= lambda p : (p.zpos+p.z_depth-1), reverse=True)
      return self.sorted_presents
     
   """ Compactor """
   def compact(self, prev_layer):
      #z_min up to current present. then, following presents must not be smaller, they can be equal or greater.
      z_min = prev_layer.z_base-1       
      # z_max must be recomputed (initialized at z_base)
      self.z_max = self.z_base
      for p in self.presents: #in order of id!
         # presents in the previous layer sorted by decreasing z-height
         for up_p in prev_layer.z_sort_presents():
            if p.overlap(up_p):
               # this is the tallest overlapping present: you can move down the present, if possible. 
               # if not possible, break!
               diff = p.zpos - max(prev_layer.lefty_base,(up_p.zpos+up_p.z_depth))
               if diff > 0 and (p.zpos - diff) >= z_min:
                  p.zpos -= diff
                  #print "moved down", diff, "present",p.id, "coordinates:", p.xpos, p.ypos, p.xpos+p.width, p.ypos+p.height
                  #print "overlapping present:", up_p.id, "top coordinate:", up_p.zpos+up_p.z_depth-1
                  z_min = max(p.zpos, z_min)
               break
         z_min = max(p.zpos, z_min)
         self.z_max = max(self.z_max, p.zpos + p.z_depth - 1)
      return

   """ Finalize shelf: add coordinates for the plot """
   def finalize_shelf(self):
      if self.id <= MAX_LAYERS:
         for i,p in enumerate(self.presents):
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
   def write_short_shelf(self, writer):
      for p in self.presents:
         x1, x2, y1, y2, z1, z2 = p.xpos, p.xpos+p.width-1, p.ypos, p.ypos + p.height-1, p.zpos, p.zpos + p.z_depth-1
         list_vertices = [x1, x2, y1, y2, z1, z2]
         writer.writerow([p.id] + list_vertices)
      return 

   """ Write next line """
   def write_shelf(self, writer, maxz):
      for p in self.presents:
         x1, x2, y1, y2, z1, z2 = p.xpos, p.xpos+p.width-1, p.ypos, p.ypos + p.height-1, p.zpos, p.zpos + p.z_depth-1
         z1 = maxz - z1 + 1
         z2 = maxz - z2 + 1

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

def write_present(row, writer, maxz):
   _id = row[0]
   x1, x2, y1, y2, z1, z2 = int(row[1]), int(row[2]), int(row[3]), int(row[4]), int(row[5]), int(row[6])
   z1 = maxz - z1 + 1
   z2 = maxz - z2 + 1

   list_vertices = [x1, y1, z1]
   list_vertices += [x1, y2, z1]
   list_vertices += [x2, y1, z1]
   list_vertices += [x2, y2, z1]
   list_vertices += [x1, y1, z2]
   list_vertices += [x1, y2, z2]
   list_vertices += [x2, y1, z2]
   list_vertices += [x2, y2, z2]
   writer.writerow([_id] + list_vertices)
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


def repair_solution():
   path = '.'
   presentsFilename = os.path.join(path, 'presents.csv')
   tmpFilename = os.path.join(path, 'tmpfile.csv')
   submissionFilename = os.path.join(path, 'lastlayer.csv')
   print tmpFilename, submissionFilename

   # create header for submission file: PresentId, x1,y1,z1, ... x8,y8,z8
   header = ['PresentId']
   for i in xrange(1,9):
       header += ['x' + str(i), 'y' + str(i), 'z' + str(i)]
    
   layer = Layer(1,1,[])
   prev_layer = None
   maxz = 1
   totScore=0.
   layers=0.

   last_id = 999844 
   maxz = 1018209
   random.seed(1)
   with open(presentsFilename, 'rb') as f:
      with open(tmpFilename, 'wb') as w:
         f.readline() # header
         fcsv = csv.reader(f)
         tmpwcsv = csv.writer(w)
         cumul_area = 0
         for row in fcsv:
            if int(row[0])%5000 == 0:
               print row[0], "layer:", layer.id, "height:",layer.z_max,"avg:", 0 if layers==0 else totScore/layers

            present = Present(row)
            if present.id == 700000:
               TRIES = 5
               print "Now using", TRIES, "tries" 
            if present.id <= last_id:
               continue
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
               
               # compact shelf down (if possible), preserving order
               if prev_layer is not None:
                  layer.compact(prev_layer)
               
               # store coordinates for plotting
               if PLOT:
                  layer.finalize_shelf()
               

#            if len(leftovers)>0:
#               del leftovers[:layer.try_fit_rectangle(leftovers)]

               layer.write_short_shelf(tmpwcsv)
               
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
               
               # reflect even layers
               if layer.id % 2 == 0:
               #   print "Reflected shelf"
                  layer.reflect_shelf()
               
               # compact shelf down (if possible), preserving order
               if prev_layer is not None:
                  layer.compact(prev_layer)
               
               # store coordinates for plotting
               if PLOT:
                  layer.finalize_shelf()
               
#            if len(leftovers)>0:
#               del leftovers[:layer.try_fit_rectangle(leftovers)]

               layer.write_short_shelf(tmpwcsv)

               
               #however, it can still have leftovers
               if len(leftovers)>0: 
                  prev_layer = layer
                  layer = Layer(prev_layer.id+1, prev_layer.z_max+1, leftovers)
                  print "Packing leftovers", len(leftovers)
                  leftovers = layer.pack()
                  if len(leftovers) > 0:
                     print "even more leftovers!"

   maxz = layer.z_max

   print "Max z =", maxz
   print "Last present packed", layer.presents[-1].id

   if WRITE:
      print "Writing file"
      layer = Layer(1,1,[])
      prev_layer = None
      random.seed(1)
      with open(tmpFilename, 'rb') as f:
         with open(submissionFilename, 'wb') as w:
            fcsv = csv.reader(f)
            wcsv = csv.writer(w)
            for row in fcsv:
               write_present(row, wcsv, maxz) 

   print 'Done'


if __name__ == "__main__":
   #repair_solution()
   #exit()
   
   path = '.'
   presentsFilename = os.path.join(path, 'presents.csv')
   tmpFilename = os.path.join(path, 'tmpSmart5000-5-6.csv')
   submissionFilename = os.path.join(path, 'OnePassSmart5000-5-6.csv')
   print tmpFilename, submissionFilename

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
      with open(tmpFilename, 'wb') as w:
         f.readline() # header
         fcsv = csv.reader(f)
         tmpwcsv = csv.writer(w)
         cumul_area = 0
         for row in fcsv:
            if int(row[0])%5000 == 0:
               print row[0], "layer:", layer.id, "height:",layer.z_max,"avg:", 0 if layers==0 else totScore/layers,time.strftime("%d/%m/%Y - %H:%M:%S")

            present = Present(row)
            if present.id == 700000:
               TRIES = 5
               print "Now using", TRIES, "tries" 

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
               
               # compact shelf down (if possible), preserving order
               if prev_layer is not None:
                  layer.compact(prev_layer)
               
               # store coordinates for plotting
               if PLOT:
                  layer.finalize_shelf()
               

               #if len(leftovers)>0:
               #   del leftovers[:layer.try_fit_rectangle(leftovers)]

               layer.write_short_shelf(tmpwcsv)
               
               # open new shelf and add current present
               cumul_area = sum(p.area for p in leftovers)
               prev_layer = layer
               if layer.id >= MAX_LAYERS:
                  break
               layer = Layer(prev_layer.id+1, prev_layer.z_max+1, leftovers)
               #print "New layer", layer.id, layer.z_base
               added_present = layer.add_present(present)
               cumul_area += present.area

            if not added_present:
               print "Something wrong"

         if added_present == True:
               # rows are over. 
               # last layer was not "full" (area-wise), so it has not been packed yet!
               print "Packing last layer?"

               leftovers = layer.pack()
               
               # reflect even layers
               if layer.id % 2 == 0:
               #   print "Reflected shelf"
                  layer.reflect_shelf()
               
               # compact shelf down (if possible), preserving order
               if prev_layer is not None:
                  layer.compact(prev_layer)
               
               # store coordinates for plotting
               if PLOT:
                  layer.finalize_shelf()
               
               #if len(leftovers)>0:
               #   del leftovers[:layer.try_fit_rectangle(leftovers)]

               layer.write_short_shelf(tmpwcsv)

               
               #however, it can still have leftovers
               if len(leftovers)>0: 
                  prev_layer = layer
                  layer = Layer(prev_layer.id+1, prev_layer.z_max+1, leftovers)
                  print "Packing leftovers", len(leftovers)
                  leftovers = layer.pack()
                  if len(leftovers) > 0:
                     print "even more leftovers!"

   maxz = layer.z_max

   print "Max z =", maxz
   print "Last present packed", layer.presents[-1].id

   if WRITE:
      print "Writing file"
      layer = Layer(1,1,[])
      prev_layer = None
      random.seed(1)
      with open(tmpFilename, 'rb') as f:
         with open(submissionFilename, 'wb') as w:
            fcsv = csv.reader(f)
            wcsv = csv.writer(w)
            wcsv.writerow(header) #write header
            for row in fcsv:
               write_present(row, wcsv, maxz) 

   print 'Done'
