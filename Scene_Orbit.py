#!/usr/bin/python
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
#-------------------------------------------------------------------
# Old sins:
# pylint: disable=unused-wildcard-import
from __future__ import print_function

import os
import wx
import wx.lib.colourselect as wxLibCS

from OpenGL.GL import *

import rgb
import Geom3D
import GeomGui
import geomtypes
import isometry
import orbit

TITLE = 'Create Polyhedron by Orbiting'

LOG_DBG  = 1
LOG_INFO = 2
LOG_WARN = 3
LOG_ERR  = 4

LOG_TXT  = {
    LOG_DBG:    'DEBUG',
    LOG_INFO:   'INFO',
    LOG_WARN:   'WARNING',
    LOG_ERR:    'ERROR',
}

LOG_STDOUT_LVL = LOG_INFO # or WARN?
LOG_BAR_LVL    = LOG_INFO

class Shape(Geom3D.SimpleShape):
    def __init__(this):
        Geom3D.SimpleShape.__init__(this, [], [])
        #this.dbgTrace = True

    def glInit(this):
        Geom3D.SimpleShape.glInit(this)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        #glEnable(GL_BLEND)
        pass

class CtrlWin(wx.Frame):
    def __init__(this, shape, canvas, *args, **kwargs):
        this.shape = shape
        this.name = shape.name
        this.canvas = canvas
        kwargs['title'] = TITLE
        wx.Frame.__init__(this, *args, **kwargs)
        this.set_default_cols()
        this.no_of_cols = 1
        # save which colour alternative was chosen per final symmetry and
        # stabiliser symmetry. This to be able to switch to the one that was
        # chosen before when the user changes back to one that was chosen
        # previously.
        # Each selection contains two indices:
        # - the index of the symmetry of the colour stabiliser
        # - the index of the alternative
        this.col_select = None
        this.final_sym_setup = None
        this.stab_sym_setup = None
        this.stat_bar = this.CreateStatusBar()
        this.panel = wx.Panel(this, -1)
        this.main_sizer = wx.BoxSizer(wx.VERTICAL)
        this.main_sizer.Add(
                this.create_ctrl_sizer(),
                1, wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_LEFT
            )
        this.set_default_size((582, 741))
        this.panel.SetAutoLayout(True)
        this.panel.SetSizer(this.main_sizer)
        this.Show(True)
        this.panel.Layout()
        this.import_dir_name = '.'

    def set_default_cols(this):
        c = lambda rgb_col: [c*255 for c in rgb_col]
        this.cols = [
                c(rgb.gold),       c(rgb.forestGreen),
                c(rgb.red4),       c(rgb.deepSkyBlue),
                c(rgb.khaki4),     c(rgb.midnightBlue),
                c(rgb.chocolate1), c(rgb.burlywood1),
                c(rgb.chocolate4), c(rgb.yellow),
                c(rgb.aquamarine), c(rgb.indianRed1)
            ]

    def create_ctrl_sizer(this):
        ctrl_sizer = wx.BoxSizer(wx.VERTICAL)

        this.show_gui = []

        face_sizer = wx.StaticBoxSizer(
            wx.StaticBox(this.panel, label = 'Face(s) Definition'),
            wx.VERTICAL
        )
        ctrl_sizer.Add(face_sizer, 0, wx.EXPAND)

        data_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #VERTICES
        this.show_gui.append(wx.StaticBox(this.panel, label = 'Vertices'))
        b_sizer = wx.StaticBoxSizer(this.show_gui[-1])
        this.show_gui.append(GeomGui.Vector3DSetDynamicPanel(
            this.panel, relExtraSpace = 3
        ))
        this._vs_gui_idx = len(this.show_gui) - 1
        b_sizer.Add(this.show_gui[-1], 1, wx.EXPAND)
        data_sizer.Add(b_sizer, 1, wx.EXPAND)

        # FACES
        this.show_gui.append(wx.StaticBox(this.panel, label = 'Faces'))
        b_sizer = wx.StaticBoxSizer(this.show_gui[-1])
        this.show_gui.append(
            GeomGui.FaceSetDynamicPanel(this.panel, 0, faceLen = 3)
        )
        this._fs_gui_idx = len(this.show_gui) - 1
        b_sizer.Add(this.show_gui[-1], 1, wx.EXPAND)
        data_sizer.Add(b_sizer, 1, wx.EXPAND)
        face_sizer.Add(data_sizer, 0, wx.EXPAND)

        # Import
        this.show_gui.append(wx.Button(this.panel, wx.ID_ANY, "Import"))
        this.panel.Bind(wx.EVT_BUTTON, this.on_import,
                id = this.show_gui[-1].GetId())
        face_sizer.Add(this.show_gui[-1], 0)

        # Rotate Axis
        # - rotate axis and set angle (button and float input)
        this.rot_sizer = GeomGui.AxisRotateSizer(
            this.panel,
            this.on_rot,
            min_angle=-180,
            max_angle=180,
            initial_angle=0
        )
        face_sizer.Add(this.rot_sizer)

        # SYMMETRY
        this.show_gui.append(
            GeomGui.SymmetrySelect(this.panel,
                'Final Symmetry',
                onSymSelect   = lambda a: this.on_sym_select(a),
                onGetSymSetup = lambda a: this.on_final_sym_select(a)
            )
        )
        this._final_sym_gui_idx = len(this.show_gui) - 1
        ctrl_sizer.Add(this.show_gui[-1], 0, wx.EXPAND)
        if this.col_select == None:
            this.col_select = [None for i in range(this.show_gui[-1].length)]
            this.final_sym_setup = this.col_select[:]
            this.stab_sym_setup = this.col_select[:]

        # Stabiliser
        this.show_gui.append(
            GeomGui.SymmetrySelect(this.panel,
                'Stabiliser Symmetry',
                this.show_gui[
                    this._final_sym_gui_idx
                ].getSymmetryClass(applyOrder = True).subgroups,
                onGetSymSetup = lambda a: this.on_stab_sym_select(a)
            )
        )
        this._stab_sym_gui_idx = len(this.show_gui) - 1
        ctrl_sizer.Add(this.show_gui[-1], 0, wx.EXPAND)

        this.show_gui.append(wx.Button(this.panel, wx.ID_ANY, "Apply Symmetry"))
        this.panel.Bind(
            wx.EVT_BUTTON, this.on_apply_sym, id = this.show_gui[-1].GetId())
        ctrl_sizer.Add(this.show_gui[-1], 0, wx.EXPAND)

        this.show_gui[this._final_sym_gui_idx].SetSelected(0)
        this.on_sym_select(
                this.show_gui[this._final_sym_gui_idx].getSymmetryClass()
            )

        this.ctrl_sizer = ctrl_sizer
        return ctrl_sizer

    def add_col_gui(this):
        try:
            this.col_sizer.Clear(True)
        except AttributeError:
            this.col_gui_box = wx.StaticBox(this.panel, label = 'Colour Setup')
            this.col_sizer = wx.StaticBoxSizer(this.col_gui_box, wx.VERTICAL)
            this.ctrl_sizer.Add(this.col_sizer, 0, wx.EXPAND)
        this.orbit = orbit.Orbit((
            this.show_gui[this._final_sym_gui_idx].GetSelected(),
            this.show_gui[this._stab_sym_gui_idx].GetSelected()
        ))
        no_of_cols_choice_lst = [
            '%d (based on %s)' % (p['index'], p['class'].__name__)
            for p in this.orbit.higherOrderStabiliserProps
        ]
        no_of_cols_choice_lst.extend([
            '%d (based on %s)' % (p['index'], p['class'].__name__)
            for p in this.orbit.lowerOrderStabiliserProps
        ])
        this.col_guis = []
        this.col_guis.append(
            wx.Choice(this.panel, wx.ID_ANY, choices = no_of_cols_choice_lst)
        )
        this.col_sizer.Add(this.col_guis[-1], 0, wx.EXPAND)
        this.panel.Bind(wx.EVT_CHOICE,
            this.on_no_of_col_select, id = this.col_guis[-1].GetId())
        this.col_alt = this.col_select[
            this.show_gui[this._final_sym_gui_idx].getSelectedIndex()
        ][
            this.show_gui[this._stab_sym_gui_idx].getSelectedIndex()
        ]
        this.col_guis[-1].SetSelection(this.col_alt[0])
        this._no_of_cols_gui_idx = len(this.col_guis)-1
        this.on_no_of_col_select(this.col_guis[-1])

    def on_final_sym_select(this, sym_idx):
        try:
            return this.final_sym_setup[sym_idx]
        except TypeError:
            print('Note: ignoring error at on_final_sym_select: 1st time = ok')
            return None

    def on_stab_sym_select(this, sym_idx):
        final_sym_idx = this.show_gui[this._final_sym_gui_idx].getSelectedIndex()
        try:
            return this.stab_sym_setup[final_sym_idx][sym_idx]
        except TypeError:
            print('Note: ignoring error at on_stab_sym_select: 1st time = ok')
            return None

    def on_sym_select(this, sym):
        final_sym_gui = this.show_gui[this._final_sym_gui_idx]
        stab_syms = sym.subgroups
        i = final_sym_gui.getSelectedIndex()
        # initialise stabiliser setup before setting the list.
        if this.stab_sym_setup[i] == None:
            this.stab_sym_setup[i] = [None for x in stab_syms]
        this.show_gui[this._stab_sym_gui_idx].setList(stab_syms)
        no_of_stabs = this.show_gui[this._stab_sym_gui_idx].length
        if this.col_select[i] == None:
            this.col_select[i] = [[0, 0] for j in range(no_of_stabs)]
            this.stab_sym_setup[i] = [None for j in range(no_of_stabs)]

    def on_apply_sym(this, e):
        # Check these first before you retrieve values. E.g. if the 'n' in Cn
        # symmetry is updated, then the class is updated. As soon as you
        # retrieve the value, val_updated will be reset.
        updated0 = this.show_gui[this._final_sym_gui_idx].isSymClassUpdated()
        updated1 = this.show_gui[this._stab_sym_gui_idx].isSymClassUpdated()
        verts = this.show_gui[this._vs_gui_idx].get()
        faces = this.show_gui[this._fs_gui_idx].get()
        if faces == []:
            this.status_text('No faces defined!', LOG_ERR)
            return
        final_sym_gui = this.show_gui[this._final_sym_gui_idx]
        final_sym = final_sym_gui.GetSelected()
        final_sym_idx = final_sym_gui.getSelectedIndex()
        stab_sym_gui = this.show_gui[this._stab_sym_gui_idx]
        stab_sym = stab_sym_gui.GetSelected()
        stab_sym_idx = stab_sym_gui.getSelectedIndex()
        this.final_sym_setup[final_sym_idx] = final_sym.setup             # copy?
        this.stab_sym_setup[final_sym_idx][stab_sym_idx] = stab_sym.setup # copy?
        try:
            this.shape = Geom3D.SymmetricShape(verts, faces,
                    finalSym=final_sym, stabSym=stab_sym, name=this.name
                )
        except isometry.ImproperSubgroupError:
            this.status_text(
                'Stabiliser not a subgroup of final symmetry!', LOG_ERR)
            if e != None:
                e.Skip()
            return
        this.fs_orbit = this.shape.getIsometries()['direct']
        this.fs_orbit_org = True
        this.shape.recreateEdges()
        this.update_orientation(
            this.rot_sizer.get_angle(), this.rot_sizer.get_axis())
        this.canvas.panel.setShape(this.shape)
        # Note the functions above need to be called to update the latest
        # status. I.e. don't call them in the or below, because the second will
        # not be called if the first is true.
        if (updated0 or updated1):
            this.add_col_gui()
        else:
            this.on_no_of_col_select(this.col_guis[this._no_of_cols_gui_idx])
        this.panel.Layout()
        this.status_text('Symmetry applied: choose colours!', LOG_INFO)
        try:
            tst = this.cols
        except AttributeError:
            this.cols = [(255, 100, 0)]
        if e != None:
            e.Skip()

    def status_text(this, txt, lvl = LOG_INFO):
        txt = '%s: %s' % (LOG_TXT[lvl], txt)
        if lvl >= LOG_STDOUT_LVL:
            print(txt)
        if lvl >= LOG_BAR_LVL:
            this.stat_bar.SetStatusText(txt)

    def update_orientation(this, angle, axis):
        if axis == geomtypes.Vec3([0, 0, 0]):
            rot = geomtypes.E
            this.status_text(
                'Rotation axis is the null-vector: applying identity',
                LOG_INFO
            )
        else:
            rot = geomtypes.Rot3(
                axis=axis,
                angle=Geom3D.Deg2Rad * angle
            )
        try:
            this.shape.setBaseOrientation(rot)
        except AttributeError:
            this.status_text(
                'Apply symmetry first, before pulling the slide-bar',
                LOG_WARN
            )

    def on_rot(this, angle, axis):
        this.update_orientation(angle, axis)
        this.canvas.panel.setShape(this.shape)

    def on_no_of_col_select(this, e):
        try:
            this.select_col_sizer.Clear(True)
        except AttributeError:
            this.select_col_sizer = wx.BoxSizer(wx.VERTICAL)
            this.col_sizer.Add(this.select_col_sizer, 0, wx.EXPAND)
            next_prev_col_sizer = wx.BoxSizer(wx.HORIZONTAL)
            this.col_guis.append(
                wx.Button(this.panel, wx.ID_ANY, "Previous Alternative"))
            this.panel.Bind(
                wx.EVT_BUTTON, this.on_prev_col_alt, id = this.col_guis[-1].GetId())
            next_prev_col_sizer.Add(this.col_guis[-1], 0, wx.EXPAND)
            this.col_guis.append(
                wx.Button(this.panel, wx.ID_ANY, "Next Alternative"))
            this.panel.Bind(
                wx.EVT_BUTTON, this.on_next_col_alt, id = this.col_guis[-1].GetId())
            next_prev_col_sizer.Add(this.col_guis[-1], 0, wx.EXPAND)
            next_prev_col_sizer.Add(wx.BoxSizer(wx.HORIZONTAL), 1, wx.EXPAND)
            this.col_guis.append(
                wx.Button(this.panel, wx.ID_ANY, "Reset Colours"))
            this.panel.Bind(
                wx.EVT_BUTTON, this.on_reset_cols, id = this.col_guis[-1].GetId())
            next_prev_col_sizer.Add(this.col_guis[-1], 0, wx.EXPAND)
            this.col_sizer.Add(next_prev_col_sizer, 0, wx.EXPAND)

        col_div_no = e.GetSelection()
        this.col_alt[0] = col_div_no
        l0 = len(this.orbit.higherOrderStabiliserProps)
        assert l0 != 0, 'no higher order stabilisers found'
        if col_div_no < l0:
            this.col_final_sym = this.orbit.final
            this.col_syms = this.orbit.higherOrderStabiliser(col_div_no)
            no_of_cols = this.orbit.higherOrderStabiliserProps[col_div_no]['index']
        else:
            this.col_final_sym = this.orbit.altFinal
            this.col_syms = this.orbit.lowerOrderStabiliser(col_div_no - l0)
            no_of_cols = this.orbit.lowerOrderStabiliserProps[col_div_no - l0]['index']
            # now the fs_orbit might contain isometries that are not part of the
            # colouring isometries. Recreate the shape with isometries that only
            # have these:
            if this.fs_orbit_org:
                final_sym = this.orbit.altFinal
                stab_sym = this.orbit.altStab
                verts = this.shape.getBaseVertexProperties()['Vs']
                faces = this.shape.getBaseFaceProperties()['Fs']
                this.shape = Geom3D.SymmetricShape(verts, faces,
                        finalSym=final_sym, stabSym=stab_sym, name=this.name
                    )
                this.fs_orbit = this.shape.getIsometries()['direct']
                this.shape.recreateEdges()
                this.canvas.panel.setShape(this.shape)
                this.fs_orbit_org = False # and do this only once
        assert len(this.col_syms) != 0
        this.select_col_guis = []
        init_col = (255, 255, 255)
        maxColPerRow = 12
        # Add buttons for choosing individual colours:
        for i in range(no_of_cols):
            try:
                col = this.cols[i]
            except IndexError:
                col = init_col
                this.cols.append(col)
            if i % maxColPerRow == 0:
                sel_col_sizer_row = wx.BoxSizer(wx.HORIZONTAL)
                this.select_col_sizer.Add(sel_col_sizer_row, 0, wx.EXPAND)
            this.select_col_guis.append(
                wxLibCS.ColourSelect(this.panel, wx.ID_ANY, colour = col)
            )
            this.panel.Bind(wxLibCS.EVT_COLOURSELECT, this.on_col_select)
            sel_col_sizer_row.Add(this.select_col_guis[-1], 0, wx.EXPAND)
        this.no_of_cols = no_of_cols
        # replace invalid index of colour alternative with the last possible
        if this.col_alt[1] >= len(this.col_syms):
            this.col_alt[1] = len(this.col_syms) - 1
        this.update_shape_cols()
        this.panel.Layout()

    def on_col_select(this, e):
        col = e.GetValue().Get()
        gui_idx = e.GetId()
        for i, gui in zip(range(len(this.select_col_guis)), this.select_col_guis):
            if gui.GetId() == gui_idx:
                this.cols[i] = col
                this.update_shape_cols()
                break

    def update_shape_cols(this):
        """apply symmetry on colours
        """
        final_sym = this.col_final_sym
        col_quotient_set = final_sym  / this.col_syms[this.col_alt[1]]
        col_per_isom = []
        for isom in this.fs_orbit:
            for sub_set, i in zip(col_quotient_set,
                                 range(len(col_quotient_set))):
                if isom in sub_set:
                    col_per_isom.append(this.cols[i])
                    break
        cols = [
                ([[float(colCh)/255 for colCh in col]], [])
                for col in col_per_isom
            ]
        this.shape.setFaceColors(cols)
        this.status_text('Colour alternative %d of %d applied' % (
                this.col_alt[1] + 1, len(this.col_syms)
            ), LOG_INFO
        )
        this.canvas.paint()

    # move to general class
    def set_default_size(this, size):
        this.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        this.SetSize(size)

    def on_next_col_alt(this, e):
        this.col_alt[1] += 1
        if this.col_alt[1] >= len(this.col_syms):
            this.col_alt[1] -= len(this.col_syms)
        this.update_shape_cols()

    def on_reset_cols(this, e):
        this.set_default_cols()
        for i in range(this.no_of_cols):
            this.select_col_guis[i].SetColour(this.cols[i])
        this.update_shape_cols()

    def on_prev_col_alt(this, e):
        this.col_alt[1] -= 1
        if this.col_alt[1] < 0:
            this.col_alt[1] += len(this.col_syms)
        this.update_shape_cols()

    def on_import(this, e):
        wildcard = "OFF shape (*.off)|*.off|Python shape (*.py)|*.py"
        dlg = wx.FileDialog(this,
            'New: Choose a file', this.import_dir_name, '', wildcard, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            this.import_dir_name  = dlg.GetDirectory()
            print("opening file:", filename)
            fd = open(os.path.join(this.import_dir_name, filename), 'r')
            if filename[-3:] == '.py':
                shape = Geom3D.readPyFile(fd)
                # For Compound derived shapes (isinstance) use merge:
                try:
                    shape = shape.SimpleShape
                except AttributeError:
                    # probably a SimpleShape
                    pass
            else:
                shape = Geom3D.readOffFile(fd, recreateEdges = False)
            fd.close()
            if isinstance(shape, Geom3D.IsometricShape):
                verts = shape.baseShape.Vs
                faces = shape.baseShape.Fs
            else:
                verts = shape.Vs
                faces = shape.Fs
            print('read ', len(verts), ' Vs and ', len(faces), ' Fs.')
            this.show_gui[this._vs_gui_idx].set(verts)
            this.show_gui[this._fs_gui_idx].set(faces)
            # With a python file it is possible to set the other properties as
            # well: e.g.
            # final_sym = isometry.S4xI
            # final_sym_setup = [ [1, 0, 0], [0, 0, 1] ]
            # stab_sym = isometry.C3xI
            # stab_sym_setup = [ [0, 0, 1] ]
            # rotAxis = [1, 1, 1]
            # rotAngle = 30
            #   where the angle is in degrees (floating point)
            if filename[-3:] == '.py':
                fd = open(os.path.join(this.import_dir_name, filename), 'r')
                ed = {}
                exec(fd.read(), ed)
                more_settings = 0
                key_err_str = 'Note: KeyError while looking for'
                key = 'final_sym'
                # to prevent accepting keyErrors in other code than ed[key]:
                key_defined = False
                try:
                    final_sym = ed[key]
                    key_defined = True
                except KeyError:
                    print(key_err_str, key)
                    pass
                if key_defined:
                    more_settings += 1
                    this.show_gui[this._final_sym_gui_idx].SetSelectedClass(
                        final_sym
                    )
                    this.show_gui[this._final_sym_gui_idx].onSetSymmetry(None)
                    key = 'final_sym_setup'
                    key_defined = False
                    try:
                        sym_setup = ed[key]
                        key_defined = True
                    except KeyError:
                        print(key_err_str, key)
                        pass
                    if key_defined:
                        more_settings += 1
                        this.show_gui[this._final_sym_gui_idx].SetupSymmetry(
                            sym_setup
                        )
                key = 'stab_sym'
                key_defined = False
                try:
                    stab_sym = ed[key]
                    key_defined = True
                except KeyError:
                    print(key_err_str, key)
                    pass
                if key_defined:
                    more_settings += 1
                    this.show_gui[this._stab_sym_gui_idx].SetSelectedClass(
                        stab_sym
                    )
                    this.show_gui[this._stab_sym_gui_idx].onSetSymmetry(None)
                    key = 'stab_sym_setup'
                    key_defined = False
                    try:
                        sym_setup = ed[key]
                        key_defined = True
                    except KeyError:
                        print(key_err_str, key)
                        pass
                    if key_defined:
                        more_settings += 1
                        this.show_gui[this._stab_sym_gui_idx].SetupSymmetry(
                            sym_setup
                        )
                if more_settings > 0:
                    this.on_apply_sym(None)
                key = 'rotAxis'
                key_defined = False
                try:
                    axis = ed[key]
                    key_defined = True
                except KeyError:
                    print(key_err_str, key)
                    pass
                if key_defined:
                    more_settings += 1
                    this.rot_sizer.set_axis(axis)
                key = 'rotAngle'
                key_defined = False
                try:
                    angle = ed[key]
                    key_defined = True
                except KeyError:
                    print(key_err_str, key)
                    pass
                if key_defined:
                    more_settings += 1
                    this.rot_sizer.set_angle(angle)
                    this.update_orientation(
                        this.rot_sizer.get_angle(), this.rot_sizer.get_axis())
                fd.close()
            this.name = filename
        dlg.Destroy()

class Scene(Geom3D.Scene):
    def __init__(this, parent, canvas):
        Geom3D.Scene.__init__(this, Shape, CtrlWin, parent, canvas)
