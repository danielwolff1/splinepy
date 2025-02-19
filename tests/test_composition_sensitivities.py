try:
    from . import common as c
except BaseException:
    import common as c


class ComposeSensitivitiesTest(c.SplineBasedTestCase):
    """
    Test composition sensitivity, i.e., the derivative concerning the
    deformation function's control points.
    """

    def test_composition(self):
        # Here we only try 2D compositions (surface-line is tested in bezman)
        # Init Splines to be tested
        surface_polynomial = c.splinepy.Bezier(
            degrees=[1, 2],
            control_points=[[1, 1], [2, 1], [1, 2], [2, 2], [1, 3], [2, 3]],
        )
        surface_rational = c.splinepy.RationalBezier(
            degrees=[2, 1],
            control_points=[[1, 1], [2, 1], [3, 2], [1, 2], [2, 2], [3, 3]],
            weights=[1.0, 0.8, 1.0, 1.0, 0.8, 1.0],
        )
        inner_polynomial = c.splinepy.Bezier(
            degrees=[1, 1],
            control_points=[[0.2, 0.0], [1.0, 0.2], [0.0, 0.8], [0.8, 1.0]],
        )
        inner_rational = c.splinepy.RationalBezier(
            degrees=[2, 1],
            control_points=[
                [0.2, 0.0],
                [0.5, 0.5],
                [1.0, 0.2],
                [0.0, 0.8],
                [0.5, 0.5],
                [0.8, 1.0],
            ],
            weights=[1, 0.5, 1, 1, 0.5, 1],
        )

        dx = 1e-4
        tolerance = 1e-4

        def test_splines(outer, inner):
            # Determine base line
            composed, composed_sensitivities = outer.compose(
                inner, compute_sensitivities=True
            )

            # Check against FD approximation
            for i in range(outer.cps.shape[0]):
                for j in range(outer.cps.shape[1]):
                    outer.cps[i, j] += dx

                    # FD values
                    composed_dx = outer.compose(inner)

                    # FD
                    derivative_fd = (composed_dx.cps - composed.cps) / dx
                    expected = c.np.zeros(composed.cps.shape)
                    expected[:, j] = composed_sensitivities[i].cps.flatten()

                    self.assertTrue(
                        c.np.allclose(derivative_fd, expected, atol=tolerance)
                    )

                    outer.cps[i, j] -= dx

        test_splines(surface_polynomial, inner_polynomial)
        test_splines(surface_polynomial, inner_rational)
        test_splines(surface_rational, inner_polynomial)
        test_splines(surface_rational, inner_rational)

    def test_composition_sensitivities_on_bsplines(self):
        """Combine Composition sensitivities with BSpline extraction"""

        # Initialize outer functions
        bspline = self.bspline_2p2d()
        inner_function = c.splinepy.Bezier(
            degrees=[1, 1],
            control_points=[
                [0.5, 0.0],
                [1.0, 0.5],
                [0.0, 0.5],
                [0.5, 1.0],
            ],
        )

        # Initialize values for finite differences
        bspline_dx = bspline.copy()
        bspline.insert_knots(1, 0.5)
        bspline_dx.insert_knots(1, 0.5)
        dx = 1e-5

        # Perform computations
        extract_beziers = bspline.extract_bezier_patches()
        extraction_matrices = bspline.knot_insertion_matrix(beziers=True)

        composed_der_ctps = []
        beziers = []
        for bez, mat in zip(extract_beziers, extraction_matrices):
            # Composition
            composed, derivatives = bez.compose(
                inner_function, compute_sensitivities=True
            )
            # Form matrix
            deriv_points = c.np.hstack([der.cps for der in derivatives])

            # Compute derivatives
            composed_der_ctps.append(deriv_points @ mat)
            beziers.append(composed)

        for cps in range(bspline.cps.shape[0]):
            for dim in range(bspline.cps.shape[1]):
                # Modify dx spline
                bspline_dx.cps[cps, dim] += dx

                # Extract Beziers
                extract_beziers_dx = bspline_dx.extract_bezier_patches()
                for bez, bez_dx, comps in zip(
                    beziers, extract_beziers_dx, composed_der_ctps
                ):
                    # Compose finite differences spline
                    composed_dx = bez_dx.compose(inner_function)
                    fd_ctps = (composed_dx.cps - bez.cps) / dx

                    self.assertTrue(
                        c.np.allclose(fd_ctps[:, dim], comps[:, cps])
                    )

                # Reset dx spline
                bspline_dx.cps[cps, dim] -= dx


if __name__ == "__main__":
    c.unittest.main()
