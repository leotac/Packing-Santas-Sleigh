"""
Packing Santa's Sleigh -- Submission 3d viewer
"""

import os, sys
import csv
from matplotlib import cm
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

SLEIGH_LENGTH = 1000
MAX_ROW = 400   

# Plotting
xpos, ypos, zpos, dx, dy, dz = [],[],[],[],[],[]
colors = []

if __name__ == "__main__":
    
   path = '.'
   presentsFilename = os.path.join(path, 'presents.csv')
   submissionFilename = os.path.join(path, sys.argv[1])
   if len(sys.argv) > 2:
      max_row = int(sys.argv[2])
   else:
      max_row = MAX_ROW
   z_layer = 0
   with open(submissionFilename, 'rb') as f:
            f.readline() # header
            fcsv = csv.reader(f)
            for row in fcsv:
               i = int(row[0])
               if i >= max_row:
                  break
               x1, y1, z1 = int(row[1]), int(row[2]), int(row[3])
               y2 = int(row[5])
               x2 = int(row[7])
               z2 = int(row[15])
               
               if(max(z1,z2) != z_layer):
                  z_layer = max(z1,z2)
                  layer_cardinality = 1
               else:
                  layer_cardinality += 1

               xpos.append(min(x1,x2))
               ypos.append(min(y1,y2))
               zpos.append(min(z1,z2))
               dx.append(abs(x1-x2))
               dy.append(abs(y1-y2))
               dz.append(abs(z1-z2))
               colors.append(cm.jet(float(i)/max_row))


   fig = plt.figure()
   ax = fig.add_subplot(111, projection='3d')
   ax.bar3d(xpos,ypos,zpos,dx,dy,dz,color=colors)
   #ax.bar3d(xpos,ypos,zpos,dx,dy,dz,color='r')
   ax.set_xlim3d(0, 1000)
   ax.set_ylim3d(0, 1000)
   #ax.set_zlim3d(0, 1000)
   print "Plotting"
   plt.show()

   print 'Done'
