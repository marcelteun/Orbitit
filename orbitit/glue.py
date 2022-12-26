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

def getVUsageIn1D(Vs, Es, vUsage = None):
    """
    Check how often the vertices in Vs are referred through the 1D array Es

    Returns an array of lenth Vs with the amount.
    vUsage (of length Vs) can be used as initialisation value for this array.
    """
    if vUsage == None:
        vUsage = [0 for v in Vs]
    for vIndex in Es:
        vUsage[vIndex] = vUsage[vIndex] + 1
    return vUsage

def getVUsageIn2D(Vs, Fs, vUsage = None):
    """
    Check how often the vertices in Vs are referred through the 2D array Fs

    Returns an array of lenth Vs with the amount.
    vUsage (of length Vs) can be used as initialisation value for this array.
    """
    if vUsage == None:
        vUsage = [0 for v in Vs]
    for f in Fs:
        for vIndex in f:
            vUsage[vIndex] = vUsage[vIndex] + 1
    return vUsage

def cleanUpVsFs(Vs, Fs):
    """cleanup Vs and update Fs by removing unused vertices.

    Note that the arrays themselves are updated. If this is not wanted, send in
    copies.
    It returns an array with tuples expressing which vertices are deleted. This
    array can be used as input to filterEs
    """
    # The clean up is done as follows:
    # first construct an array of unused vertex indices
    # remove all unused indices from Vs and subtract the approproate amount
    # from the indices in Fs that are bigger
    # vUsage contains for each vertex a tuple that expresses:
    # - how ofter the vertex is used:
    # After the unused vertices are deleted, vReoved will contain:
    # - how many vertices that come before this (vertex) index are deleted.
    #
    vUsage = getVUsageIn2D(Vs, Fs)
    vRemoved = [0 for x in vUsage]
    notUsed = 0 # counts the amount of vertices that are not used until vertex i
    for i in range(len(vUsage)):
        # If the vertex is not used
        if vUsage[i - notUsed] == 0:
            del Vs[i - notUsed]
            del vUsage[i - notUsed]
            notUsed += 1
        # change the value of vUsage to the amount of vertices that are (not
        # used and from now on) deleted until vertex i
        vRemoved[i] = notUsed
    for f in Fs:
        for faceIndex in range(len(f)):
            f[faceIndex] = f[faceIndex] - vRemoved[f[faceIndex]]
    return vUsage

def mergeVs(Vs, Fs, precision=12):
    """
    Merges vertices that are equal into one vertex.

    Note that this might change the content of Fs and Es.
    Note that Vs is not cleaned up. This means that some vertices might not be
    used. The return value indicates if some vertices are unused now.
    """
    replaced = False
    replace_by = [-1 for v in Vs]
    # first build up an array that expresses for each vertex by which vertex it
    # can be replaced.
    geomtypes.set_eq_float_margin(math.pow(10, -precision))
    logging.info("Find multiple occurences of vertices")
    log_handler = logging.getLogger().handlers[0]
    end_bac, log_handler.terminator = log_handler.terminator, '\r'

    for i in range(len(Vs) - 1, -1, -1):
        logging.info(f"checking vertex {len(Vs) - i} (of {len(Vs)})")
        v = Vs[i]
        for j in range(i):
            if v == Vs[j]:
                replaced = True
                replace_by[i] = j
                break
    geomtypes.reset_eq_float_margin()
    # Apply the changes now. Don't delete the vertices, since that means
    # re-indexing
    log_handler.terminator = end_bac
    logging.info("")
    logging.info("Clean up Fs")
    for f_i in range(len(Fs) - 1, -1, -1):
        f = Fs[f_i]
        face_vertices = []  # array holding unique face vertices
        for i in range(len(f)):
            if replace_by[f[i]] > -1:
                f[i] = replace_by[f[i]]
            if not f[i] in face_vertices:
                face_vertices.append(f[i])
        # remove any faces with only 2 (or less) unique vertices
        if len(face_vertices) < 3:
            del(Fs[f_i])
#    for i in range(len(Es)):
#       if replace_by[Es[i]] > -1:
#           Es[i] = replace_by[Es[i]]
    return replaced
