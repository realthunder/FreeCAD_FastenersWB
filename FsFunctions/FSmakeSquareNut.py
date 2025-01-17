# -*- coding: utf-8 -*-
"""
***************************************************************************
*   Copyright (c) 2022                                                    *
*   Shai Seger <shaise[at]gmail>                                          *
*                                                                         *
*   This file is a supplement to the FreeCAD CAx development system.      *
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU Lesser General Public License (LGPL)    *
*   as published by the Free Software Foundation; either version 2 of     *
*   the License, or (at your option) any later version.                   *
*   for detail see the LICENCE text file.                                 *
*                                                                         *
*   This software is distributed in the hope that it will be useful,      *
*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
*   GNU Library General Public License for more details.                  *
*                                                                         *
*   You should have received a copy of the GNU Library General Public     *
*   License along with this macro; if not, write to the Free Software     *
*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
*   USA                                                                   *
*                                                                         *
***************************************************************************
"""
from screw_maker import *
import FastenerBase

tan30 = math.tan(math.radians(30.0))

def makeSquareTool(s, m):
    # makes a cylinder with an inner square hole, used as cutting tool
    # create square face
    msq = Base.Matrix()
    msq.rotateZ(math.radians(90.0))
    polygon = []
    vsq = Base.Vector(s / 2.0, s / 2.0, -m * 0.1)
    for i in range(4):
        polygon.append(vsq)
        vsq = msq.multiply(vsq)
    polygon.append(vsq)
    square = Part.makePolygon(polygon)
    square = Part.Face(square)

    # create circle face
    circ = Part.makeCircle(s * 3.0, Base.Vector(0.0, 0.0, -m * 0.1))
    circ = Part.Face(Part.Wire(circ))

    # Create the face with the circle as outline and the square as hole
    face = circ.cut(square)

    # Extrude in z to create the final cutting tool
    exSquare = face.extrude(Base.Vector(0.0, 0.0, m * 1.2))
    # Part.show(exHex)
    return exSquare


def sqnutMakeFace(do, di, dw, s, m, shellOnly):
    do = do / 2
    dw = dw / 2
    di = di / 2
    ch1 = do - di
    ch2 = (s - dw) * tan30

    fm = FastenerBase.FSFaceMaker()
    if not shellOnly:
        fm.AddPoint(di, ch1)
    fm.AddPoints((do, 0), (s, 0))
    if dw > 0:
        fm.AddPoints((s, m - ch2), (dw, m))
    else:
        fm.AddPoint(s, m)
    fm.AddPoint(do, m)
    if shellOnly:
        return fm.GetWire()
    fm.AddPoint(di, m - ch1)
    return fm.GetFace()


def makeSquareNut(self, fa):
    SType = fa.type
    dia = self.getDia(fa.calc_diam, True)

    # FreeCAD.Console.PrintMessage(SType + "\n")
    if SType == 'DIN557':
        s, m, di, dw, P = fa.dimTable
    elif SType == 'DIN562':
        s, m, di, P = fa.dimTable
        dw = 0
    do = dia * 1.1

    residue, turns = math.modf(m / P)
    if residue > 0.0:
        turns += 1.0

    if fa.thread:
        threadShell = self.makeInnerThread_2(dia, P, int(turns), do, m)
            
    section = sqnutMakeFace(do, di, dw, s, m, fa.thread and threadShell is not None)
    nutSolid = self.RevolveZ(section)
    if fa.thread:
        if threadShell is None:
            # thread shell method failed, use slower method
            FreeCAD.Console.PrintLog("Revert to slow thread generation\n")
            turns += 1
            threadCutter = self.makeInnerThread_2(dia, P, int(turns), None, m)
            threadCutter.translate(Base.Vector(0.0, 0.0, m + P))
            # Part.show(threadCutter, 'threadCutter')
            nutSolid = nutSolid.cut(threadCutter)
        else:
            # FreeCAD.Console.PrintMessage(str((dia, P, int(turns), do, m)) + "\n")
            nutFaces = nutSolid.Faces
            nutFaces.extend(threadShell.Faces)
            nutShell = Part.Shell(nutFaces)
            nutSolid = Part.Solid(nutShell)
    htool = makeSquareTool(s, m)
    nutSolid = nutSolid.cut(htool)
    return nutSolid
