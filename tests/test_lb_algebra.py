import numpy as np

from bbx.lb_algebra import expected_rmse, implied_corr, moments_from_constants


def _rmse(p, y):
    return float(np.sqrt(np.mean((p - y) ** 2)))


def test_constants_recover_moments_exactly():
    rng = np.random.default_rng(0)
    y = rng.gamma(0.5, 0.12, size=3000)
    m, s = moments_from_constants(0.0, _rmse(np.zeros_like(y), y), 0.1, _rmse(np.full_like(y, 0.1), y))
    assert np.isclose(m, y.mean()) and np.isclose(s, y.std())


def test_implied_corr_matches_true_corr_when_moments_known():
    rng = np.random.default_rng(1)
    y = rng.gamma(0.5, 0.12, size=3000)
    p = 0.06 + 0.4 * (y - y.mean()) + rng.normal(0, 0.03, size=y.size)
    r = implied_corr(p, _rmse(p, y), y.mean(), y.std())
    assert np.isclose(r, np.corrcoef(p, y)[0, 1])
    assert np.isclose(expected_rmse(p, y.mean(), y.std(), r), _rmse(p, y))
