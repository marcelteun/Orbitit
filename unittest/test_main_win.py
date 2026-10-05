"""Unit tests for the main window helpers."""

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

        with (
            patch.object(app_main.GL, "glClear"),
            patch.object(app_main.GL, "glPushMatrix") as push_matrix,
            patch.object(app_main.GL, "glScalef") as scale,
            patch.object(app_main.GL, "glPopMatrix") as pop_matrix,
        ):
            app_main.Canvas3DScene.on_paint(canvas)

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
