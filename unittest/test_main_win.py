"""Unit tests for the main window helpers."""

import copy
import unittest
from unittest.mock import Mock, patch

import numpy as np
from OpenGL import GL

from orbitit import __main__ as app_main
from orbitit import geom_3d, geom_4d, geomtypes, main_win


class TestFrontFaceIsClockwise(unittest.TestCase):
    """Test conversion of OpenGL query values for wx controls."""

    def test_returns_python_bool_for_numpy_comparison(self):
        for gl_value, expected in (
            (GL.GL_CW, True),
            (GL.GL_CCW, False),
        ):
            with self.subTest(gl_value=gl_value):
                with patch(
                    "orbitit.main_win.GL.glGetIntegerv",
                    return_value=np.int32(gl_value),
                ):
                    actual = main_win._front_face_is_clockwise()

                self.assertIs(type(actual), bool)
                self.assertEqual(actual, expected)


class TestEdgeRadiusSettings(unittest.TestCase):
    """Test edge radius controls for shapes with different coordinate scales."""

    def test_radius_range_scales_with_shape(self):
        unit_shape = geom_3d.SimpleShape(
            vs=[
                geomtypes.Vec3([1, 0, 0]),
                geomtypes.Vec3([-1, 0, 0]),
            ],
            fs=[],
        )
        large_shape = geom_3d.SimpleShape(
            vs=[
                geomtypes.Vec3([300, 0, 0]),
                geomtypes.Vec3([-300, 0, 0]),
            ],
            fs=[],
        )

        self.assertEqual(main_win._edge_radius_bounds(unit_shape), (0.008, 0.08))
        self.assertEqual(main_win._edge_radius_bounds(large_shape), (2.4, 24.0))

    def test_zero_size_shape_uses_unit_radius_range(self):
        shape = geom_3d.SimpleShape(vs=[geomtypes.Vec3([0, 0, 0])], fs=[])

        self.assertEqual(main_win._edge_radius_bounds(shape), (0.008, 0.08))

    def test_radius_range_is_independent_of_shape_position(self):
        shape = geom_3d.SimpleShape(
            vs=[
                geomtypes.Vec3([300, 0, 0]),
                geomtypes.Vec3([301, 0, 0]),
            ],
            fs=[],
        )

        self.assertEqual(main_win._edge_radius_bounds(shape), (0.004, 0.04))

    def test_default_edge_option_uses_edge_radius(self):
        self.assertEqual(
            main_win._default_edge_option({"draw_edges": True, "radius": 0.02}),
            1,
        )
        self.assertEqual(
            main_win._default_edge_option({"draw_edges": True, "radius": -1}),
            2,
        )
        self.assertEqual(
            main_win._default_edge_option({"draw_edges": False, "radius": 0.02}),
            0,
        )


class TestVertexRadiusSettings(unittest.TestCase):
    """Test vertex radius controls for differently scaled shapes."""

    def test_radius_range_scales_with_shape(self):
        unit_shape = geom_3d.SimpleShape(
            vs=[
                geomtypes.Vec3([1, 0, 0]),
                geomtypes.Vec3([-1, 0, 0]),
            ],
            fs=[],
        )
        large_shape = geom_3d.SimpleShape(
            vs=[
                geomtypes.Vec3([300, 0, 0]),
                geomtypes.Vec3([-300, 0, 0]),
            ],
            fs=[],
        )

        self.assertEqual(main_win._vertex_radius_bounds(unit_shape), (0.01, 0.1))
        self.assertEqual(main_win._vertex_radius_bounds(large_shape), (3.0, 30.0))

    def test_default_visibility_uses_actual_vertex_radius(self):
        self.assertEqual(main_win._default_vertex_option({"radius": -1}), 0)
        self.assertEqual(main_win._default_vertex_option({"radius": 0.05}), 1)

    def test_radius_range_is_independent_of_shape_position(self):
        shape = geom_3d.SimpleShape(
            vs=[
                geomtypes.Vec3([300, 0, 0]),
                geomtypes.Vec3([301, 0, 0]),
            ],
            fs=[],
        )

        self.assertEqual(main_win._vertex_radius_bounds(shape), (0.005, 0.05))


class TestDisplayScaling(unittest.TestCase):
    """Ensure fit-to-view scales are render-only and shared by compounds."""

    def test_scale_factor_fits_simple_shape_without_changing_vertices(self):
        shape = geom_3d.SimpleShape(
            vs=[
                geomtypes.Vec3([300, 0, 0]),
                geomtypes.Vec3([-300, 0, 0]),
            ],
            fs=[],
        )
        original_vertices = list(shape.vs)
        original_off = shape.to_off()

        scale = app_main._display_scale_factor(shape)

        self.assertAlmostEqual(scale, 5.6 / 300)
        self.assertEqual(shape.vs, original_vertices)
        self.assertEqual(shape.to_off(), original_off)

    def test_compound_uses_one_scale_for_all_component_sizes(self):
        small = geom_3d.SimpleShape(
            vs=[geomtypes.Vec3([1, 0, 0]), geomtypes.Vec3([-1, 0, 0])],
            fs=[],
        )
        large = geom_3d.SimpleShape(
            vs=[geomtypes.Vec3([10, 0, 0]), geomtypes.Vec3([-10, 0, 0])],
            fs=[],
        )
        shape = geom_3d.CompoundShape([small, large], regen_edges=False)

        scale = app_main._display_scale_factor(shape)

        self.assertAlmostEqual(scale, 5.6 / 10)
        self.assertEqual(
            small.vs, [geomtypes.Vec3([1, 0, 0]), geomtypes.Vec3([-1, 0, 0])]
        )
        self.assertEqual(
            large.vs, [geomtypes.Vec3([10, 0, 0]), geomtypes.Vec3([-10, 0, 0])]
        )

    def test_canvas_applies_display_scale_during_drawing(self):
        canvas = Mock()
        canvas.panel.display_scale_factor = 0.5
        gl_calls = []

        with (
            patch.object(app_main.GL, "glClear"),
            patch.object(app_main.GL, "glPushMatrix") as push_matrix,
            patch.object(app_main.GL, "glEnable") as enable,
            patch.object(app_main.GL, "glScalef") as scale,
            patch.object(app_main.GL, "glPopMatrix") as pop_matrix,
        ):
            enable.side_effect = lambda *args: gl_calls.append(("enable", args))
            scale.side_effect = lambda *args: gl_calls.append(("scale", args))
            app_main.Canvas3DScene.on_paint(canvas)

        enable.assert_called_once_with(app_main.GL.GL_NORMALIZE)
        self.assertEqual(
            gl_calls,
            [
                ("enable", (app_main.GL.GL_NORMALIZE,)),
                ("scale", (0.5, 0.5, 0.5)),
            ],
        )
        scale.assert_called_once_with(0.5, 0.5, 0.5)
        push_matrix.assert_called_once_with()
        pop_matrix.assert_called_once_with()
        canvas.shape.gl_draw.assert_called_once_with()


class TestFourDimensionalSceneShapes(unittest.TestCase):
    """Ensure the main panel accepts native four-dimensional scene shapes."""

    def test_panel_shape_setter_preserves_four_dimensional_shape(self):
        shape = geom_4d.SimpleShape(
            vs=[geomtypes.Vec4([1, 0, 0, 0]), geomtypes.Vec4([-1, 0, 0, 0])],
            cells=[],
        )
        old_shape = Mock()
        old_shape.dimension = 3
        panel = Mock()
        panel.canvas.shape = old_shape

        with (
            patch.object(app_main.GL, "glDisable"),
            patch.object(app_main.GL, "glEnable"),
        ):
            app_main.MainPanel.shape.fset(panel, shape)

        self.assertIs(panel.canvas.shape, shape)
        self.assertEqual(panel.display_scale_factor, 5.6)
        panel.canvas.paint.assert_called_once_with()
        panel.parent.set_status_text.assert_called_once_with("Shape Updated")

    def test_builtin_four_dimensional_scenes_project(self):
        for module in (
            app_main.Scene_5Cell,
            app_main.Scene_8Cell,
            app_main.Scene_24Cell,
            app_main.Scene_Rectified8Cell,
            app_main.Scene_Rectified24Cell,
        ):
            with self.subTest(scene=module.TITLE):
                shape = module.Shape()
                shape.gl_draw_single_rm_unscaled_es()

                self.assertIsNotNone(shape.cell)
                self.assertTrue(
                    all(
                        isinstance(channel, int)
                        for channel in shape.cell.vertex_props["color"]
                    )
                )
                self.assertTrue(
                    all(
                        isinstance(channel, int)
                        for channel in shape.cell.edge_props["color"]
                    )
                )


class TestCoreTool(unittest.TestCase):
    """Test the Tools menu action for creating a convex core."""

    def test_replaces_current_shape_with_core(self):
        core = Mock()
        source_shape = Mock()
        source_shape.dimension = 3
        source_shape.get_core.return_value = core
        window = Mock()
        window._undo_history = []
        window.undo_menu_item = Mock()
        window.panel.shape = source_shape
        window.GetTitle.return_value = "Source"

        app_main.MainWindow.on_core(window, None)

        self.assertIs(window.panel.shape, core)
        window.SetTitle.assert_called_once_with("Core(Source)")

    def test_reports_core_geometry_errors(self):
        source_shape = Mock()
        source_shape.dimension = 3
        source_shape.get_core.side_effect = ValueError("open mesh")
        window = Mock()
        window._undo_history = []
        window.undo_menu_item = Mock()
        window.panel.shape = source_shape

        with patch.object(app_main.wx, "MessageBox") as message_box:
            app_main.MainWindow.on_core(window, None)

        message_box.assert_called_once_with(
            "open mesh",
            "Core unavailable",
            app_main.wx.OK | app_main.wx.ICON_ERROR,
            window,
        )
        window.SetTitle.assert_not_called()


class TestUndo(unittest.TestCase):
    """Test the main-window undo history."""

    def test_undo_menu_item_is_disabled_after_it_is_attached(self):
        operations = []
        menu = Mock()
        menu.Append.side_effect = lambda item: operations.append(("append", item))
        undo_item = Mock()
        undo_item.GetId.return_value = 42
        undo_item.Enable.side_effect = lambda enabled: operations.append(
            ("enable", enabled)
        )
        wx_menu = Mock(return_value=menu)
        wx_menu_item = Mock(return_value=undo_item)
        window = Mock()

        with (
            patch.object(app_main.wx, "Menu", wx_menu),
            patch.object(app_main.wx, "MenuItem", wx_menu_item),
        ):
            app_main.MainWindow.create_edit_menu(window)

        self.assertLess(operations.index(("append", undo_item)), operations.index(("enable", False)))

    def test_undo_restores_shape_snapshot_and_title(self):
        original = geom_3d.SimpleShape(
            vs=[[0, 0, 0], [1, 0, 0], [0, 1, 0]],
            fs=[[0, 1, 2]],
        )
        changed = copy.deepcopy(original)
        changed.vs[0] = geomtypes.Vec3([9, 9, 9])
        window = Mock()
        window._undo_history = [(original, "Before")]
        window.undo_menu_item = Mock()
        window.panel.shape = changed

        app_main.MainWindow.on_undo(window, None)

        self.assertEqual(window.panel.shape.vs, original.vs)
        window.SetTitle.assert_called_once_with("Before")
        window.undo_menu_item.Enable.assert_called_once_with(False)

    def test_record_undo_keeps_a_snapshot(self):
        shape = geom_3d.SimpleShape(
            vs=[[0, 0, 0], [1, 0, 0], [0, 1, 0]],
            fs=[[0, 1, 2]],
        )
        window = Mock()
        window._undo_history = []
        window.undo_menu_item = Mock()
        window.GetTitle.return_value = "Shape"

        app_main.MainWindow.record_undo(window, shape)
        shape.vs[0] = geomtypes.Vec3([9, 9, 9])

        self.assertEqual(
            window._undo_history[0][0].vs[0],
            geomtypes.Vec3([0, 0, 0]),
        )
        window.undo_menu_item.Enable.assert_called_once_with(True)

    def test_transform_apply_commits_one_undo_step(self):
        before_apply = geom_3d.SimpleShape(
            vs=[[0, 0, 0], [1, 0, 0], [0, 1, 0]],
            fs=[[0, 1, 2]],
        )
        window = Mock()
        window._has_pending_changes = True
        window._on_commit = Mock()
        window._undo_shape = before_apply
        window.canvas.shape.vertex_props = {"vs": []}
        window.rot_sizer.set_angle = Mock()
        window.scale_factor_gui.SetValue = Mock()
        window.set_status_text = Mock()

        main_win.TransformWindow.on_apply(window)

        window._on_commit.assert_called_once_with(before_apply)
        self.assertFalse(window._has_pending_changes)

    def test_transform_done_commits_pending_changes(self):
        before_transform = geom_3d.SimpleShape(
            vs=[[0, 0, 0], [1, 0, 0], [0, 1, 0]],
            fs=[[0, 1, 2]],
        )
        window = Mock()
        window._has_pending_changes = True
        window._on_commit = Mock()
        window._undo_shape = before_transform

        main_win.TransformWindow.on_done(window, None)

        window._on_commit.assert_called_once_with(before_transform)
        self.assertTrue(window._confirmed)
        window.Close.assert_called_once_with()

    def test_colour_done_commits_original_shape_once(self):
        original_shape = geom_3d.SimpleShape(
            vs=[[0, 0, 0], [1, 0, 0], [0, 1, 0]],
            fs=[[0, 1, 2]],
        )
        window = Mock()
        window._on_commit = Mock()
        window._original_shape = original_shape
        window._confirmed = False

        main_win.ColourWindow.on_done(window, None)

        window._on_commit.assert_called_once_with(original_shape)
        self.assertTrue(window._confirmed)
