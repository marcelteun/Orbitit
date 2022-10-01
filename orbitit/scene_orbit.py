#!/usr/bin/env python
"""
The main scene: create 3D objects by using symmetry orbits

Import an 3D object or define it by vertices and faces. Then add symmetry by
defining and orienting the symmetry. If the initial object itself (aka the
descriptive) shares symmetries with the final symmetry, you will need to define
and orient that as the stabiliser symmetry.

Then you can divide colours regularly by using the symmetry. The symmetry you
choose will be the symmetry group of one colour. Each different colour can also
be mapped another colour by a symmetry of the final symmetry..

Finally you can rotate the descriptive around an axis (while it still shared
the same symmetries with the final symmetry as specified in the stabiliser
symmetry)
"""
#
# Copyright (C) 2010-2019 Marcel Tunnissen
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
# ------------------------------------------------------------------
# Old sins:
# pylint: disable=exec-used,too-many-instance-attributes,too-few-public-methods
# pylint: disable=too-many-statements,too-many-locals,too-many-branches


import os
import wx
import wx.lib.colourselect as wxLibCS

from orbitit import base, Geom3D, geom_gui, geomtypes, isometry, orbit, rgb

TITLE = 'Create Polyhedron by Orbiting'

LOG_DBG = 1
LOG_INFO = 2
LOG_WARN = 3
LOG_ERR = 4

LOG_TXT = {
    LOG_DBG:  'DEBUG',
    LOG_INFO: 'INFO',
    LOG_WARN: 'WARNING',
    LOG_ERR:  'ERROR',
}

LOG_STDOUT_LVL = LOG_INFO  # or WARN?
LOG_BAR_LVL = LOG_INFO


class Shape(Geom3D.CompoundShape):
    """Simple wrapper for the Shape being used."""
    def __init__(self):
        super().__init__([Geom3D.SimpleShape([], [])])

    #def glInit(self):
    #    super().glInit()
    #    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    #    glEnable(GL_BLEND)


class CtrlWin(wx.Frame):
    """Window with all the controls for the symmetry orbit

    Here you can define (or import):
      - the vertices and faces.
      - the symmetry of the final object
      - the stabiliser symmetry
      - the colours
      - any rotation for the stabiliser
    """
    def __init__(self, shape, canvas, *args, **kwargs):
        self.shape = shape
        self.name = shape.name
        self.canvas = canvas
        kwargs['title'] = TITLE
        wx.Frame.__init__(self, *args, **kwargs)
        self.no_of_cols = 1
        # save which colour alternative was chosen per final symmetry and
        # stabiliser symmetry. This to be able to switch to the one that was
        # chosen before when the user changes back to one that was chosen
        # previously.
        # Each selection contains two indices:
        # - the index of the symmetry of the colour stabiliser
        # - the index of the alternative
        self.col_select = None
        self.final_sym_setup = None
        self.stab_sym_setup = None
        self.cur_sym_idx = None
        self.stat_bar = self.CreateStatusBar()
        self.panel = wx.Panel(self, -1)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(
            self.create_ctrl_sizer(),
            1, wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_LEFT)
        self.set_default_size((582, 741))
        self.panel.SetAutoLayout(True)
        self.panel.SetSizer(self.main_sizer)
        self.Show(True)
        self.panel.Layout()
        self.import_dir_name = '.'
        self.cols = []
        self.select_col_guis = []
        self.orbit = None
        self.fs_orbit = None
        self.fs_orbit_org = None
        self.col_final_sym = None
        self.col_sizer = None
        self.col_guis = None
        self.col_gui_box = None
        self.col_syms = None
        self.col_alt = None
        self.select_col_sizer = None
        self._no_of_cols_gui_idx = None
        self.set_default_cols()

    def set_default_cols(self):
        """Fill colours with some default values"""
        def c(rgb_col):
            """Map rgb colour on wxWidgets colour"""
            return [c*255 for c in rgb_col]
        self.cols = [c(rgb.royalBlue),
                     c(rgb.yellowGreen),
                     c(rgb.plum),
                     c(rgb.gold),
                     c(rgb.firebrick),
                     c(rgb.tan),
                     c(rgb.lightSkyBlue),
                     c(rgb.lightSeaGreen),
                     c(rgb.slateBlue),
                     c(rgb.yellow),
                     c(rgb.indianRed),
                     c(rgb.saddleBrown),
                     c(rgb.midnightBlue),
                     c(rgb.darkGreen),
                     c(rgb.blueViolet),
                     c(rgb.lemonChiffon),
                     c(rgb.red),
                     c(rgb.peru),
                     c(rgb.steelBlue),
                     c(rgb.limeGreen),
                     c(rgb.seashell),
                     c(rgb.khaki),
                     c(rgb.peachPuff),
                     c(rgb.orange),
                     c(rgb.azure),
                     c(rgb.darkOliveGreen),
                     c(rgb.lavender),
                     c(rgb.lightGoldenrod),
                     c(rgb.lightCoral),
                     c(rgb.darkGoldenrod)]

    def create_ctrl_sizer(self):
        """Create and return a wxWidget sizer with all the controls"""
        ctrl_sizer = wx.BoxSizer(wx.VERTICAL)

        self.show_gui = []

        face_sizer = wx.StaticBoxSizer(
            wx.StaticBox(self.panel, label='Face(s) Definition'),
            wx.VERTICAL
        )
        ctrl_sizer.Add(face_sizer, 0, wx.EXPAND)

        data_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # VERTICES
        self.show_gui.append(wx.StaticBox(self.panel, label='Vertices'))
        b_sizer = wx.StaticBoxSizer(self.show_gui[-1])
        self.show_gui.append(geom_gui.Vector3DSetDynamicPanel(
            self.panel, rel_xtra_space=3))
        self._vs_gui_idx = len(self.show_gui) - 1
        b_sizer.Add(self.show_gui[-1], 1, wx.EXPAND)
        data_sizer.Add(b_sizer, 1, wx.EXPAND)

        # FACES
        self.show_gui.append(wx.StaticBox(self.panel, label='Faces'))
        b_sizer = wx.StaticBoxSizer(self.show_gui[-1])
        self.show_gui.append(
            geom_gui.FaceSetDynamicPanel(self.panel, 0, face_len=3))
        self._fs_gui_idx = len(self.show_gui) - 1
        b_sizer.Add(self.show_gui[-1], 1, wx.EXPAND)
        data_sizer.Add(b_sizer, 1, wx.EXPAND)
        face_sizer.Add(data_sizer, 0, wx.EXPAND)

        # Import
        self.show_gui.append(wx.Button(self.panel, wx.ID_ANY, "Import"))
        self.panel.Bind(wx.EVT_BUTTON, self.on_import,
                        id=self.show_gui[-1].GetId())
        face_sizer.Add(self.show_gui[-1], 0)

        # Rotate Axis
        # - rotate axis and set angle (button and float input)
        self.rot_sizer = geom_gui.AxisRotateSizer(
            self.panel,
            self.on_rot,
            min_angle=-180,
            max_angle=180,
            initial_angle=0
        )
        face_sizer.Add(self.rot_sizer)

        # SYMMETRY
        self.show_gui.append(geom_gui.SymmetrySelect(
            self.panel, 'Final Symmetry',
            on_sym_select=self.on_final_sym_select,
            on_get_sym_setup=self.on_get_final_sym_setup))
        self._final_sym_gui_idx = len(self.show_gui) - 1
        ctrl_sizer.Add(self.show_gui[-1], 0, wx.EXPAND)
        if self.col_select is None:
            self.col_select = [None for _ in range(self.show_gui[-1].length)]
            self.final_sym_setup = self.col_select[:]
            self.stab_sym_setup = self.col_select[:]

        # Stabiliser
        stab_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.show_gui.append(wx.Button(self.panel, wx.ID_ANY, ""))
        self.panel.Bind(wx.EVT_BUTTON,
                        self.on_generate_stab_list,
                        id=self.show_gui[-1].GetId())
        stab_sizer.Add(self.show_gui[-1], 1, wx.TOP)
        self._gen_stab_sym_gui_idx = len(self.show_gui) - 1
        self.show_gui.append(geom_gui.SymmetrySelect(
            self.panel,
            'Stabiliser Symmetry',
            self.show_gui[self._final_sym_gui_idx].get_sym_class(
                apply_order=True).subgroups,
            on_get_sym_setup=self.on_get_stab_sym_setup))
        self._stab_sym_gui_idx = len(self.show_gui) - 1
        stab_sizer.Add(self.show_gui[-1], 2, wx.EXPAND)
        self.hide_stab_list()
        ctrl_sizer.Add(stab_sizer, 0, wx.EXPAND)

        self.show_gui.append(wx.Button(self.panel,
                                       wx.ID_ANY, "Apply Symmetry"))
        self.panel.Bind(wx.EVT_BUTTON,
                        self.on_apply_sym,
                        id=self.show_gui[-1].GetId())
        ctrl_sizer.Add(self.show_gui[-1], 0, wx.EXPAND)

        self.show_gui[self._final_sym_gui_idx].set_selected(0)
        self.on_final_sym_select(
            self.show_gui[self._final_sym_gui_idx].get_sym_class())

        self.ctrl_sizer = ctrl_sizer
        return ctrl_sizer

    def add_col_gui(self):
        """
        Add colour GUI to the control window

        The colour GUI can be added as soon as the final symmetry and the
        stabiliser symmetries are known.
        """
        try:
            self.col_sizer.Clear(True)
            self.select_col_sizer = None
        except AttributeError:
            self.col_gui_box = wx.StaticBox(self.panel, label='Colour Setup')
            self.col_sizer = wx.StaticBoxSizer(self.col_gui_box, wx.VERTICAL)
            self.ctrl_sizer.Add(self.col_sizer, 0, wx.EXPAND)
        self.orbit = orbit.Orbit((
            self.show_gui[self._final_sym_gui_idx].get_selected(),
            self.show_gui[self._stab_sym_gui_idx].get_selected()
        ))
        no_of_cols_choice_lst = [
            f"{p['index']} (based on {p['class'].__name__})"
            for p in self.orbit.higherOrderStabiliserProps
        ]
        no_of_cols_choice_lst.extend([
            f"{p['index']} (based on {p['class'].__name__})"
            for p in self.orbit.lowerOrderStabiliserProps
        ])
        self.col_guis = []
        self.col_guis.append(
            wx.Choice(self.panel, wx.ID_ANY, choices=no_of_cols_choice_lst)
        )
        self.col_sizer.Add(self.col_guis[-1], 0, wx.EXPAND)
        self.panel.Bind(wx.EVT_CHOICE,
                        self.on_no_of_col_select,
                        id=self.col_guis[-1].GetId())
        # col_alt[0]: index for no of colors
        # col_atl[1]: index for alternative number with that amount of colors
        self.col_alt = self.col_select[
            self.show_gui[self._final_sym_gui_idx].get_selected_idx()
        ][
            self.show_gui[self._stab_sym_gui_idx].get_selected_idx()
        ]
        self.col_guis[-1].SetSelection(self.col_alt[0])
        self._no_of_cols_gui_idx = len(self.col_guis)-1
        self.on_no_of_col_select(self.col_guis[-1])

    def on_get_final_sym_setup(self, sym_idx):
        """Return the orientation of the final symmetry"""
        try:
            return self.final_sym_setup[sym_idx]
        except TypeError:
            print('Note: ignoring error at on_get_final_sym_setup: '
                  '1st time = ok')
            return None

    def on_get_stab_sym_setup(self, sym_idx):
        """Return the orientation of the stabiliser symmetry"""
        final_sym_idx = self.show_gui[
            self._final_sym_gui_idx].get_selected_idx()
        try:
            return self.stab_sym_setup[final_sym_idx][sym_idx]
        except TypeError:
            print('Note: ignoring error at on_get_stab_sym_setup: '
                  '1st time = ok')
            return None

    def on_final_sym_select(self, sym):
        """Handle when the final symmetry is selected"""
        final_sym_gui = self.show_gui[self._final_sym_gui_idx]
        stab_syms = sym.subgroups
        i = final_sym_gui.get_selected_idx()
        # initialise stabiliser setup before setting the list.
        if self.stab_sym_setup[i] is None:
            self.stab_sym_setup[i] = [None for _ in stab_syms]
        self.show_gui[self._stab_sym_gui_idx].set_lst(stab_syms)
        no_of_stabs = self.show_gui[self._stab_sym_gui_idx].length
        if self.col_select[i] is None:
            # col_select[i][0]: index for no of colors
            # col_select[i][1]: index for alternative number with that amount of colors
            self.col_select[i] = [[0, 0] for _ in range(no_of_stabs)]
            self.stab_sym_setup[i] = [None for _ in range(no_of_stabs)]
        final_sym_idx = final_sym_gui.get_selected_idx()
        if self.cur_sym_idx != final_sym_idx or not self.cur_sym_idx:
            self.cur_sym_idx = final_sym_idx
            self.hide_stab_list()

    def hide_stab_list(self):
        """Hide gui with stabilisers, not to confuse the user"""
        self.show_gui[self._stab_sym_gui_idx].ShowItems(False)
        self.show_gui[self._gen_stab_sym_gui_idx].SetLabel("Show Stabilisers")
        self.panel.Layout()

    def on_generate_stab_list(self, _):
        """Generate which subgroups there are for the selected symmetries

        This is only important for the cyclic and the dihedral groups where the
        subgroups and thus the stabilisers are dependent on the order n.
        """
        label = "Regenerate Stabilisers"
        cur_label = self.show_gui[self._gen_stab_sym_gui_idx].GetLabel()
        if cur_label != label:
            self.show_gui[self._gen_stab_sym_gui_idx].SetLabel(label)
            self.show_gui[self._stab_sym_gui_idx].ShowItems(True)
        # get the subgroups again since the setup of cyclic and dihedral groups
        # might have been updated
        final_sym_gui = self.show_gui[self._final_sym_gui_idx]
        final_sym_obj = final_sym_gui.get_selected()
        final_sym_idx = final_sym_gui.get_selected_idx()
        stab_syms = final_sym_obj.subgroups
        self.stab_sym_setup[final_sym_idx] = [None for _ in stab_syms]
        self.col_select[final_sym_idx] = [[0, 0] for _ in stab_syms]
        self.show_gui[self._stab_sym_gui_idx].set_lst(stab_syms)

    def on_apply_sym(self, e):
        """Apply the symmetries to the descriptive"""
        # Check these first before you retrieve values. E.g. if the 'n' in Cn
        # symmetry is updated, then the class is updated. As soon as you
        # retrieve the value, val_updated will be reset.
        updated0 = self.show_gui[
            self._final_sym_gui_idx].is_sym_class_updated()
        updated1 = self.show_gui[
            self._stab_sym_gui_idx].is_sym_class_updated()
        verts = self.show_gui[self._vs_gui_idx].get()
        faces = self.show_gui[self._fs_gui_idx].get()
        if faces == []:
            self.status_text('No faces defined!', LOG_ERR)
            return
        final_sym_gui = self.show_gui[self._final_sym_gui_idx]
        final_sym_obj = final_sym_gui.get_selected()
        final_sym_idx = final_sym_gui.get_selected_idx()
        stab_sym_gui = self.show_gui[self._stab_sym_gui_idx]
        stab_sym = stab_sym_gui.get_selected()
        stab_sym_idx = stab_sym_gui.get_selected_idx()
        self.final_sym_setup[final_sym_idx] = final_sym_obj.setup
        self.stab_sym_setup[final_sym_idx][stab_sym_idx] = stab_sym.setup
        try:
            self.shape = Geom3D.OrbitShape(
                verts,
                faces,
                final_sym=final_sym_obj,
                stab_sym=stab_sym,
                name=self.name
            )
        except isometry.ImproperSubgroupError:
            self.status_text(
                'Stabiliser not a subgroup of final symmetry!', LOG_ERR)
            if e is not None:
                e.Skip()
            return
        self.fs_orbit = self.shape.isometries
        self.fs_orbit_org = True
        self.shape.regen_edges()
        self.update_orientation(
            self.rot_sizer.get_angle(), self.rot_sizer.get_axis())
        self.canvas.panel.shape = self.shape
        # Note the functions above need to be called to update the latest
        # status. I.e. don't call them in the or below, because the second will
        # not be called if the first is true.
        if (updated0 or updated1):
            self.add_col_gui()
        else:
            self.on_no_of_col_select(self.col_guis[self._no_of_cols_gui_idx])
        self.panel.Layout()
        self.status_text(
            f"{self.shape.order} symmetries applied: choose colours!",
            LOG_INFO,
        )
        if not self.cols:
            self.cols = [(255, 100, 0)]
        if e is not None:
            e.Skip()

    def status_text(self, txt, lvl=LOG_INFO):
        """Set the status bar log to specified text"""
        txt = f"{LOG_TXT[lvl]}: {txt}"
        if lvl >= LOG_STDOUT_LVL:
            print(txt)
        if lvl >= LOG_BAR_LVL:
            self.stat_bar.SetStatusText(txt)

    def update_orientation(self, angle, axis):
        """Handle when the orientation of a symmetry is updated"""
        if axis == geomtypes.Vec3([0, 0, 0]):
            rot = geomtypes.E
            self.status_text(
                'Rotation axis is the null-vector: applying identity',
                LOG_INFO
            )
        else:
            rot = geomtypes.Rot3(
                axis=axis,
                angle=Geom3D.Deg2Rad * angle
            )
        try:
            self.shape.setBaseOrientation(rot)
        except AttributeError:
            self.status_text(
                'Apply symmetry first, before pulling the slide-bar',
                LOG_WARN
            )

    def on_rot(self, angle, axis):
        """Handle when the descriptive is rotated"""
        self.update_orientation(angle, axis)
        self.canvas.panel.shape = self.shape

    def on_no_of_col_select(self, e):
        """Handle when the colour symmetry is chosen"""
        try:
            self.select_col_sizer.Clear(True)
        except AttributeError:
            self.select_col_sizer = wx.BoxSizer(wx.VERTICAL)
            self.col_sizer.Add(self.select_col_sizer, 0, wx.EXPAND)
            next_prev_col_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.col_guis.append(
                wx.Button(self.panel, wx.ID_ANY, "Previous Alternative"))
            self.panel.Bind(
                wx.EVT_BUTTON,
                self.on_prev_col_alt,
                id=self.col_guis[-1].GetId())
            next_prev_col_sizer.Add(self.col_guis[-1], 0, wx.EXPAND)
            self.col_guis.append(
                wx.Button(self.panel, wx.ID_ANY, "Next Alternative"))
            self.panel.Bind(
                wx.EVT_BUTTON,
                self.on_next_col_alt,
                id=self.col_guis[-1].GetId())
            next_prev_col_sizer.Add(self.col_guis[-1], 0, wx.EXPAND)
            next_prev_col_sizer.Add(wx.BoxSizer(wx.HORIZONTAL), 1, wx.EXPAND)
            self.col_guis.append(
                wx.Button(self.panel, wx.ID_ANY, "Reset Colours"))
            self.panel.Bind(wx.EVT_BUTTON,
                            self.on_reset_cols,
                            id=self.col_guis[-1].GetId())
            next_prev_col_sizer.Add(self.col_guis[-1], 0, wx.EXPAND)
            self.col_sizer.Add(next_prev_col_sizer, 0, wx.EXPAND)

        col_div_no = e.GetSelection()
        self.col_alt[0] = col_div_no
        l0 = len(self.orbit.higherOrderStabiliserProps)
        assert l0 != 0, 'no higher order stabilisers found'
        if col_div_no < l0:
            self.col_final_sym = self.orbit.final
            self.col_syms = self.orbit.higherOrderStabiliser(col_div_no)
            no_of_cols = self.orbit.higherOrderStabiliserProps[
                col_div_no]['index']
        else:
            self.col_final_sym = self.orbit.altFinal
            self.col_syms = self.orbit.lowerOrderStabiliser(col_div_no - l0)
            no_of_cols = self.orbit.lowerOrderStabiliserProps[
                col_div_no - l0]['index']
            # now the fs_orbit might contain isometries that are not part of
            # the colouring isometries. Recreate the shape with isometries that
            # only have these:
            if self.fs_orbit_org:
                final_sym = self.orbit.altFinal
                stab_sym = self.orbit.altStab
                verts = self.shape.getBaseVertexProperties()['Vs']
                faces = self.shape.getBaseFaceProperties()['Fs']
                self.shape = Geom3D.OrbitShape(
                    verts,
                    faces,
                    final_sym=final_sym,
                    stab_sym=stab_sym,
                    name=self.name
                )
                self.fs_orbit = self.shape.isometries
                self.shape.regen_edges()
                self.canvas.panel.shape = self.shape
                self.fs_orbit_org = False  # and do this only once
        assert self.col_syms
        init_col = (255, 255, 255)
        max_col_per_row = 20
        # Add buttons for choosing individual colours:
        self.select_col_guis = []
        for i in range(no_of_cols):
            try:
                col = self.cols[i]
            except IndexError:
                col = init_col
                self.cols.append(col)
            if i % max_col_per_row == 0:
                sel_col_sizer_row = wx.BoxSizer(wx.HORIZONTAL)
                self.select_col_sizer.Add(sel_col_sizer_row, 0, wx.EXPAND)
            self.select_col_guis.append(
                wxLibCS.ColourSelect(self.panel, wx.ID_ANY, colour=col,
                                     size=(40, 30))
            )
            self.panel.Bind(wxLibCS.EVT_COLOURSELECT, self.on_col_select)
            sel_col_sizer_row.Add(self.select_col_guis[-1], 0, wx.EXPAND)
        self.no_of_cols = no_of_cols
        # replace invalid index of colour alternative with the last possible
        if self.col_alt[1] >= len(self.col_syms):
            self.col_alt[1] = len(self.col_syms) - 1
        self.update_shape_cols()
        self.panel.Layout()

    def on_col_select(self, e):
        """
        Handle when a colour is selected.

        Update the shape with correct colours
        """
        col = e.GetValue().Get()
        gui_idx = e.GetId()
        for i, gui in zip(list(range(len(self.select_col_guis))),
                          self.select_col_guis):
            if gui.GetId() == gui_idx:
                self.cols[i] = col
                self.update_shape_cols()
                break

    def update_shape_cols(self):
        """Apply symmetry on colours"""
        final_sym = self.col_final_sym
        col_quotient_set = final_sym / self.col_syms[self.col_alt[1]]
        col_per_isom = []
        for isom in self.fs_orbit:
            for sub_set, i in zip(col_quotient_set,
                                  list(range(len(col_quotient_set)))):
                if isom in sub_set:
                    col_per_isom.append(self.cols[i])
                    break
        cols = [
            [float(colCh)/255 for colCh in col]
            for col in col_per_isom
        ]
        self.shape.setFaceColors(cols)
        self.status_text(
            f"Colour alternative {self.col_alt[1] + 1} of {len(self.col_syms)} applied",
            LOG_INFO)
        self.canvas.paint()

    # move to general class
    def set_default_size(self, size):
        """Set the default window size"""
        self.SetMinSize(size)
        # Needed for Dapper, not for Feisty:
        # (I believe it is needed for Windows as well)
        self.SetSize(size)

    def on_next_col_alt(self, _):
        """Handle when the next colour setup is chosen"""
        self.col_alt[1] += 1
        if self.col_alt[1] >= len(self.col_syms):
            self.col_alt[1] -= len(self.col_syms)
        self.update_shape_cols()

    def on_reset_cols(self, _):
        """Handle a that the button "Reset Colours" is pressed

        In this case the default palette of colours is used.
        """
        self.set_default_cols()
        for i in range(self.no_of_cols):
            self.select_col_guis[i].SetColour(self.cols[i])
        self.update_shape_cols()

    def on_prev_col_alt(self, _):
        """Handle when the previous colour setup is chosen"""
        self.col_alt[1] -= 1
        if self.col_alt[1] < 0:
            self.col_alt[1] += len(self.col_syms)
        self.update_shape_cols()

    def import_json(self, filename):
        shape = base.Orbitit.from_json_file(filename)
        if not isinstance(shape, Geom3D.SimpleShape) and\
               not isinstance(shape, Geom3D.CompoundShape):
            self.status_text("The JSON file doesn't represent a shape", LOG_ERR)
        # For Compound derived shapes (isinstance) use merge:
        if isinstance(shape, Geom3D.OrbitShape):
            final_sym = shape.final_sym
            stab_sym = shape.stab_sym
            self.show_gui[self._final_sym_gui_idx].set_selected_class(type(final_sym))
            self.show_gui[self._final_sym_gui_idx].on_set_sym(None)
            self.show_gui[self._final_sym_gui_idx].setup_sym(final_sym.setup)
            self.show_gui[self._stab_sym_gui_idx].set_selected_class(type(stab_sym))
            self.show_gui[self._stab_sym_gui_idx].on_set_sym(None)
            self.show_gui[self._stab_sym_gui_idx].setup_sym(stab_sym.setup)
            # TODO: set the colours
            shape = shape.base_shape
        if isinstance(shape, Geom3D.CompoundShape):
            shape = shape.simple_shape
        return shape

    def on_import(self, _):
        """Handle the import of a file

        The file can specify the descriptive and its orientation and the
        symmetries
        """
        wildcard = "OFF shape (*.off)|*.off|Python shape (*.json)|*.json"
        dlg = wx.FileDialog(self,
                            'New: Choose a file', self.import_dir_name,
                            '', wildcard, wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            self.import_dir_name = dlg.GetDirectory()
            print("opening file:", filename)
            filepath = os.path.join(self.import_dir_name, filename)
            if filename[-5:] == '.json':
                shape = self.import_json(filepath)
            else:
                with  open(filename) as fd:
                    shape = Geom3D.read_off_file(fd, regen_edges=False)
            verts = shape.Vs
            faces = shape.Fs
            print('read ', len(verts), ' Vs and ', len(faces), ' Fs.')
            self.show_gui[self._vs_gui_idx].set(verts)
            self.show_gui[self._fs_gui_idx].set(faces)
            self.name = filename
        dlg.Destroy()


class Scene(Geom3D.Scene):
    """Implementation of the scene: control window and the shape"""
    def __init__(self, parent, canvas):
        Geom3D.Scene.__init__(self, Shape, CtrlWin, parent, canvas)
