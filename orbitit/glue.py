#!/usr/bin/env python
#
# Copyright (C) 2010 Marcel Tunnissen
#
# License: GNU Public License version 2
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not,
# check at http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# or write to the Free Software Foundation,
#
#------------------------------------------------------------------
#
# I am not sure where to put these functions. These convert objects from A to
# B. Should they be in A or in B?

import logging
import math

from orbitit import geomtypes

def getVUsageIn1D(vs, es, vUsage = None):
    """
    Check how often the vertices in vs are referred through the 1D array es

    Returns an array of lenth vs with the amount.
    vUsage (of length vs) can be used as initialisation value for this array.
    """
    if vUsage == None:
        vUsage = [0 for v in vs]
    for vIndex in es:
        vUsage[vIndex] = vUsage[vIndex] + 1
    return vUsage

def getVUsageIn2D(vs, fs, vUsage = None):
    """
    Check how often the vertices in vs are referred through the 2D array fs

    Returns an array of lenth vs with the amount.
    vUsage (of length vs) can be used as initialisation value for this array.
    """
    if vUsage == None:
        vUsage = [0 for v in vs]
    for f in fs:
        for vIndex in f:
            vUsage[vIndex] = vUsage[vIndex] + 1
    return vUsage

def cleanUpVsFs(vs, fs):
    """cleanup vs and update fs by removing unused vertices.

    Note that the arrays themselves are updated. If this is not wanted, send in
    copies.
    It returns an array with tuples expressing which vertices are deleted. This
    array can be used as input to filterEs
    """
    # The clean up is done as follows:
    # first construct an array of unused vertex indices
    # remove all unused indices from vs and subtract the approproate amount
    # from the indices in fs that are bigger
    # vUsage contains for each vertex a tuple that expresses:
    # - how ofter the vertex is used:
    # After the unused vertices are deleted, vReoved will contain:
    # - how many vertices that come before this (vertex) index are deleted.
    #
    vUsage = getVUsageIn2D(vs, fs)
    vRemoved = [0 for x in vUsage]
    notUsed = 0 # counts the amount of vertices that are not used until vertex i
    for i in range(len(vUsage)):
        # If the vertex is not used
        if vUsage[i - notUsed] == 0:
            del vs[i - notUsed]
            del vUsage[i - notUsed]
            notUsed += 1
        # change the value of vUsage to the amount of vertices that are (not
        # used and from now on) deleted until vertex i
        vRemoved[i] = notUsed
    for f in fs:
        for faceIndex in range(len(f)):
            f[faceIndex] = f[faceIndex] - vRemoved[f[faceIndex]]
    return vUsage

def mergeVs(vs, fs, precision=12):
    """
    Merges vertices that are equal into one vertex.

    Note that this might change the content of fs and es.
    Note that vs is not cleaned up. This means that some vertices might not be
    used. The return value indicates if some vertices are unused now.
    """
    replaced = False
    replace_by = [-1 for v in vs]
    # first build up an array that expresses for each vertex by which vertex it
    # can be replaced.
    geomtypes.set_eq_float_margin(math.pow(10, -precision))
    logging.info("Find multiple occurences of vertices")
    log_handler = logging.getLogger().handlers[0]
    end_bac, log_handler.terminator = log_handler.terminator, '\r'

    for i in range(len(vs) - 1, -1, -1):
        logging.info(f"checking vertex {len(vs) - i} (of {len(vs)})")
        v = vs[i]
        for j in range(i):
            if v == vs[j]:
                replaced = True
                replace_by[i] = j
                break
    geomtypes.reset_eq_float_margin()
    # Apply the changes now. Don't delete the vertices, since that means
    # re-indexing
    log_handler.terminator = end_bac
    logging.info("")
    logging.info("Clean up fs")
    for f_i in range(len(fs) - 1, -1, -1):
        f = fs[f_i]
        face_vertices = []  # array holding unique face vertices
        for i in range(len(f)):
            if replace_by[f[i]] > -1:
                f[i] = replace_by[f[i]]
            if not f[i] in face_vertices:
                face_vertices.append(f[i])
        # remove any faces with only 2 (or less) unique vertices
        if len(face_vertices) < 3:
            del(fs[f_i])
#    for i in range(len(es)):
#       if replace_by[es[i]] > -1:
#           es[i] = replace_by[es[i]]
    return replaced
