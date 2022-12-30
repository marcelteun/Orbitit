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

import sys

from orbitit.geomtypes import f2s
from orbitit import glue


# TODO: Add standard page sizes here (and check if A4 is correct)
PageSizeA4 = (559, 774)

class doc:
    name  = "PS.doc"
    def __init__(this,
        originX=0,
        originY=0,
        width=595,
        height=842,
        title='Generated from Python',
        creator='PS.py written by marcelteun',
        pageSize=PageSizeA4,
        eps=False
    ):
        this.headerStr = '%%!PS-Adobe-2.0\n%%%%Title: %s\n%%%%Creator: %s' % (
                title, creator
            )
        this.setBBox(originX, originY, width, height)
        this.setupStr = ''
        this.eps = eps
        this.setPageProperties(pageSize)
        this.pagesStr = []
        this.resetPageValues()
        this.tailerStr = '\n%%Tailer'

    def setPageProperties(this,
            pageSize,
            leftMargin   = 10,
            rightMargin  = 10,
            bottomMargin = 25,
            topMargin    = 10,
            bboxSpaceX   = 5,
            bboxSpaceY   = 5,
        ):
        """
        Set some document page properties used by some functions

        pageSize: page size, e.g. PageSizeA4
        leftMargin: if the leftMargin is set then some functions, like addToPage
                    will take care that the left margin is respected.
        rightMargin: if the leftMargin is set then some functions, like
                     addToPage will take care that the right margin is
                     respected.
        bottomMargin: if the leftMargin is set then some functions, like
                      addToPage will take care that the bottom margin is
                      respected.
        topMargin: if the leftMargin is set then some functions, like addToPage
                   will take care that the top margin is respected.
        bboxSpaceX: When adding drawing objects by addToPage this is the amount
                    of horizontal space (in points) that is used between the
                    bounding boxes.
        bboxSpaceY: When adding drawing objects by addToPage this is the amount
                    of vertical space (in points) that is used between the
                    bounding boxes.
        """
        this.pageSize     = pageSize
        this.leftMargin   = leftMargin
        this.rightMargin  = rightMargin
        this.bottomMargin = bottomMargin
        this.topMargin    = topMargin
        this.bboxSpaceX   = bboxSpaceX
        this.bboxSpaceY   = bboxSpaceY

    def setBBox(this, originX, originY, width, height):
        this.bBoxStr = '\n%%%%BoundingBox: %d %d %d %d' % (
                originX, originY, originX + width, originX + height
            )

    def addSetupStr(this, str):
        this.setupStr = '%s\n%s' % (this.setupStr, str)

    def addTailerStr(this, str):
        this.tailerStr = '%s\n%s' % (this.tailerStr, str)

    def addNewPageStr(this, str):
        this.resetPageValues()
        this.pagesStr.append(str)

    # for backwards compatibility:
    def addPageStr(this, str):
        this.addNewPageStr(str)

    def appendPageStr(self, s):
        if (self.pagesStr == []):
            self.addNewPageStr(s)
        else:
            self.pagesStr[-1] = f"{self.pagesStr[-1]}{s}"

    def resetPageValues(this):
        # current point:
        this.cx = this.cy = 0
        # when drawing icons in boxes row for row.
        this.shiftUp = this.shiftRight = 0

    def toStr(this):
        nrOfPages = len(this.pagesStr)
        if this.eps:
            nrOfPagesStr = ''
        else:
            nrOfPagesStr = '\n%%%%Pages: %s 1' % (nrOfPages)
        str =  '%s%s%s\n%%%%EndComments\n%%%%BeginSetup%s\n%%%%EndSetup' % (
            this.headerStr, nrOfPagesStr, this.bBoxStr, this.setupStr
        )
        if this.eps and nrOfPages > 0:
            str = '%s\n%s' % (str, this.pagesStr[0])
        else:
            for pageNr in range(nrOfPages):
                pageStr = this.pagesStr[pageNr]
                pageNr += 1
                str = '%s\n%%%%Page: %d %d\n%%%%BeginPage\n%f %f translate\n%s\nshowpage\n%%%%EndPage' % (
                    str,
                    pageNr, pageNr,
                    this.leftMargin, this.rightMargin,
                    pageStr,
                )
        str = '%s\n%s\n%%%%EOF\n' %(str, this.tailerStr)
        return str

    def addLineSegments(this,
        vs, Lines,
        scaling = 1,
        precision = 5
    ):
        """
        Adds to the current page a PS string of the faces in Lines using the x
        and y coordinates from vs.

        vs: a list of coordinates
        Lines: a list of lines, each face is a list of vertex nrs and it may
               consist of several connected line segments.
        """
        vStr = '/vertices [\n'
        # use copies, for the cleanup
        vs = [[c for c in v] for v in vs]
        Lines = [[i for i in l] for l in Lines]
        # sometimes the vs contains many more vertices then needed: clean up:
        glue.cleanUpVsFs(vs, Lines)
        for i in range(len(vs)):
            v = vs[i]
            vStr = '%s  [%s %s] %% %d\n' % (
                vStr,
                f2s(v[0], precision),
                f2s(v[1], precision),
                i
            )
        vStr = '%s] def' % vStr
        fStr_ = ''
        maxX = maxY = -sys.maxsize-1 # 2-complement
        minX = minY =  sys.maxsize
        for partOfFace in Lines:
            oneFaceStr = ''
            for vNr in partOfFace:
                v = vs[vNr]
                if v[0] < minX: minX = v[0]
                if v[0] > maxX: maxX = v[0]
                if v[1] < minY: minY = v[1]
                if v[1] > maxY: maxY = v[1]
                oneFaceStr = '%s %d' % (oneFaceStr, vNr)
            fStr_ = '%s[%s]' % (fStr_, oneFaceStr[1:])
        bboxStr = '/bbox [%s %s %s %s] def' % (
            f2s(minX, precision),
            f2s(minY, precision),
            f2s(maxX, precision),
            f2s(maxY, precision)
        )
        fStr = '/faces [\n'
        break_limit = 78
        while len(fStr_) > break_limit:
            break_at = break_limit
            while fStr_[break_at] != '[':
                break_at -= 1
                assert break_at > 0, 'Not implemented, TODO: handle long line faces'
            fStr = '%s  %s\n' % (fStr, fStr_[:break_at])
            fStr_ = fStr_[break_at:]
        fStr = '%s  %s\n' % (fStr, fStr_)
        fStr = '%s] def' % fStr
        scalingStr = '/scalingSize %d def' % scaling
        addBBoxStr = ""
        if False:
            addBBoxStr = """
  %% draw origin
  %0 0 2 0 360 arc fill
  %% draw bbox
  %bbox 0 get scalingSize mul bbox 1 get scalingSize mul moveto
  %bbox 0 get scalingSize mul bbox 3 get scalingSize mul lineto
  %bbox 2 get scalingSize mul bbox 3 get scalingSize mul lineto
  %bbox 2 get scalingSize mul bbox 1 get scalingSize mul lineto
  %closepath stroke
"""
        # add vStr by + since it contains '%'s
        drawLinesStr = vStr + """
%s
%s
%s
.1 setlinewidth

/dx bbox 2 get bbox 0 get sub scalingSize mul def
/dy bbox 3 get bbox 1 get sub scalingSize mul def

gsave
  bbox 0 get scalingSize mul neg
  bbox 1 get scalingSize mul neg
  translate
  faces aload length { %%repeat
    dup 0 get
    vertices exch get
    aload pop
    scalingSize mul exch
    scalingSize mul exch
    moveto
    aload length 1 sub { %%repeat
      vertices exch get
      aload pop
      scalingSize mul exch
      scalingSize mul exch
      lineto
    } repeat
    pop
    closepath stroke
  } repeat

%s
grestore
""" % (fStr, bboxStr, scalingStr, addBBoxStr)

        this.addToPage(drawLinesStr,
            scaling*(maxX - minX),
            scaling*(maxY - minY)
        )

    def addToPage(this, drawStr, dX, dY):
        """
        Add a str for drawing to the page, if fits.

        The drawn object will draw from the current point towards up and left.
        drawStr: the str that will draw the object that is to be added to the
                 page
        dX: the object will not be draw further than the current point + dX in
            horizontal direction.
        dY: the object will not be draw further than the current point + dY in
            vertical direction.
        """
        newPage = False
        # get one pixel space between the b-boxes
        dX += this.bboxSpaceX
        dY += this.bboxSpaceY
        # if it fits on this row (on this page):
        if (
            this.cx + dX <= this.pageSize[0] - this.rightMargin
        ) and (
            this.cy + dY <= this.pageSize[1] - this.topMargin
        ):
            # if no pages created yet.
            this.appendPageStr(drawStr)
            this.appendPageStr("%f 0 translate\n" % (dX))
            this.shiftRight += dX
            this.cx += dX
            if this.shiftUp < dY: this.shiftUp = dY
        # else if it doesn't fit on the row:
        elif (this.cx + dX > this.pageSize[0] - this.rightMargin):
            # goto next row
            this.appendPageStr(
                "%f %f translate\n" % (-this.shiftRight, this.shiftUp)
            )
            this.cx -= this.shiftRight
            this.cy += this.shiftUp
            this.shiftRight = 0
            this.shiftUp    = 0
            # if it still fits on this page:
            if (this.cy + dY <= this.pageSize[1] - this.topMargin):
                this.appendPageStr(drawStr)
                this.appendPageStr("%f 0 translate\n" % (dX))
                this.cx += dX
                this.shiftRight += dX
                this.shiftUp = dY
            else:
                newPage = True
        else:
            newPage = True
        if newPage:
            this.addNewPageStr(drawStr)
            this.appendPageStr("%f 0 translate\n" % (dX))
            this.shiftRight += dX
            this.cx += dX
            this.shiftUp = dY
