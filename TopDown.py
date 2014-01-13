# -*- coding: utf-8 -*-
"""
Packing Santa's Sleigh -- Sample Submission
Create a sample submission for Packing Santa's Sleigh using top-down approach.
Approach: 
- Sort presents in correct order so that smallest PresentId gets packed first.
- Start packing the sleigh at (1000,1000,1). Pack along y=1000, z=1 until full
- Move y to min_occupied_y. Pack until full.
- When y is full, move to z = max_occupied_z.

@author: Joyce Noah-Vanhoucke
@Created: Fri Nov 29 14:28:32 2013
"""

import os
import csv

SLEIGH_LENGTH = 1000


def simple_packing(cursor, present):
    """ Given the sleigh and present, packs the present in the sleigh using simple
        filling procedure.
        - Start at (1000,1000,1). Pack along y=1000, z=1 until full
        - Move y = min_occupied_y. Pack until full
        - When y is full, move to z = max_occupied_z.
    Arguments:
        cursor: Object to keep track of current position in the sleigh and max 
            values reached so far
        present: row from the present file: id, length_x, length_y, length_z
    Returns:
        [x1, x2, y1, y2, z1, z2]
    """
    # if present exceeds x only, update cursor to (1000, miny-1, iz)
    if (cursor.ix - int(present[1]) + 1) < 1:
        cursor.ix = SLEIGH_LENGTH 
        cursor.minx = SLEIGH_LENGTH 
        cursor.iy = cursor.miny - 1
    
    # if present exceeds in y only, update cursor to (1000,1000, maxz+1)
    if (cursor.iy - int(present[2]) + 1) < 1:
        cursor.ix = SLEIGH_LENGTH 
        cursor.minx = SLEIGH_LENGTH 
        cursor.iy = SLEIGH_LENGTH 
        cursor.miny = SLEIGH_LENGTH 
        cursor.iz = cursor.maxz + 1
        
    # if present can be placed in both x and y directions, place present
    if (cursor.ix - int(present[1]) + 1) >= 1 \
        and (cursor.iy - int(present[2]) + 1) >= 1:
            x1 = cursor.ix
            y1 = cursor.iy
            z1 = cursor.iz
            x2 = x1 - int(present[1]) + 1
            y2 = y1 - int(present[2]) + 1
            z2 = z1 + int(present[3]) - 1
            cursor.ix = x2 - 1
            
            if x2 < cursor.minx:
                cursor.minx = x2
            if y2 < cursor.miny:
                cursor.miny = y2
            if z2 > cursor.maxz:
                cursor.maxz = z2

    return [x1, x2, y1, y2, z1, z2]


def fake_pack_present(cursor, present):
    [x1, x2, y1, y2, z1, z2] = simple_packing(cursor, present)
    return z2    

def pack_present(cursor, present):
    """ 
    Vertex convention: x1 y1 z1
                       x1 y2 z1
                       x2 y1 z1
                       x2 y2 z1
                       x1 y1 z2
                       x1 y2 z2
                       x2 y1 z2
                       x2 y2 z2
    Arguments:
        sleigh: 3D tensor representing the sleigh
        present: row from the present file: id, length_x, length_y, length_z
    Returns:
        list_vertices: list of the 8 vertices of the packed present
    """
    [x1, x2, y1, y2, z1, z2] = simple_packing(cursor, present)
    list_vertices = [x1, y1, z1]
    list_vertices += [x1, y2, z1]
    list_vertices += [x2, y1, z1]
    list_vertices += [x2, y2, z1]
    list_vertices += [x1, y1, z2]
    list_vertices += [x1, y2, z2]
    list_vertices += [x2, y1, z2]
    list_vertices += [x2, y2, z2]
    return list_vertices    

def pack_present(cursor, present, maxz):
    """ 
    Vertex convention: x1 y1 z1
                       x1 y2 z1
                       x2 y1 z1
                       x2 y2 z1
                       x1 y1 z2
                       x1 y2 z2
                       x2 y1 z2
                       x2 y2 z2
    Arguments:
        sleigh: 3D tensor representing the sleigh
        present: row from the present file: id, length_x, length_y, length_z
    Returns:
        list_vertices: list of the 8 vertices of the packed present
    """
    [x1, x2, y1, y2, z2, z1] = simple_packing(cursor, present)
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
    return list_vertices    

class Cursor:
    """ Object to keep track of present position and max extent in sleigh so far. """    
    def __init__(self):
        self.ix = SLEIGH_LENGTH # ix, iy, iz used to give current "cursor" position in tensor.
        self.iy = SLEIGH_LENGTH
        self.iz = 1
        self.minx = SLEIGH_LENGTH
        self.miny = SLEIGH_LENGTH 
        self.maxz = 1
        self.pack_along_x = True


if __name__ == "__main__":
    
    path = '.'
    presentsFilename = os.path.join(path, 'presents.csv')
    submissionFilename = os.path.join(path, 'topdown.csv')
    
    # create header for submission file: PresentId, x1,y1,z1, ... x8,y8,z8
    header = ['PresentId']
    for i in xrange(1,9):
        header += ['x' + str(i), 'y' + str(i), 'z' + str(i)]
     
    myCursor = Cursor()
    with open(presentsFilename, 'rb') as f:
            f.readline() # header
            fcsv = csv.reader(f)
            maxz = 1
            for row in fcsv:
                maxz = max(maxz,fake_pack_present(myCursor, row))
    print "Max z =", maxz
    myCursor = Cursor()
    with open(presentsFilename, 'rb') as f:
        with open(submissionFilename, 'wb') as w:
            f.readline() # header
            fcsv = csv.reader(f)
            wcsv = csv.writer(w)
            wcsv.writerow(header)
            for row in fcsv:
                wcsv.writerow([row[0]] + pack_present(myCursor, row, maxz))


    print 'Done'
