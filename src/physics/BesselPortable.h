#pragma once
#include <cmath>
#include <limits>

/**
 * Portable ascending-series Bessel J_m / modified Bessel I_m for small
 * integer order and moderate argument (TODO.md X2, 2026-08-20).
 *
 * WHY THIS EXISTS: std::cyl_bessel_j / std::cyl_bessel_i are C++17
 * mathematical special functions implemented by libstdc++ (GCC/Linux) and
 * MSVC (macro __cpp_lib_math_special_functions = 201603 verified on this
 * repo's MSVC toolchain, 2026-08-20) but NOT by libc++ (Apple) -- LLVM never
 * shipped them, which is why the macos-14 CI leg failed to build
 * (HANDOVER.md 1.3). PlateModel.h switches on the standard feature-test
 * macro: platforms with the std implementation keep using it (their rendered
 * bytes are untouched -- Rule 10 deliberately NOT triggered by this fix),
 * and only libc++ falls back to this implementation.
 *
 * SOURCE (Rule 4): Abramowitz & Stegun, "Handbook of Mathematical
 * Functions", NBS Applied Mathematics Series 55 (1964), ascending series
 * eq. 9.1.10 (J) and eq. 9.6.10 (I):
 *
 *     J_m(x) = (x/2)^m * sum_{k>=0} (-x^2/4)^k / (k! * (m+k)!)
 *     I_m(x) = (x/2)^m * sum_{k>=0} ( x^2/4)^k / (k! * (m+k)!)
 *
 * These are the defining power series -- mathematics, not tunable constants.
 *
 * VALIDATED DOMAIN: integer order 0 <= m <= 8, 0 <= x <= 16. Chosen to
 * cover PlateModel's entire actual usage with margin: the largest clamped
 * eigenvalue is Omega = 120.08 (mode (1,2)) so lambda = sqrt(120.08) =
 * 10.958 bounds every argument (z = lambda * radius, radius <= 1), and the
 * largest order is m + 1 = 6 (free-edge moment coefficient). Outside the
 * validated domain both functions return quiet NaN (fail-closed -- the
 * pipeline's existing NaN gates catch it) instead of silently extrapolating.
 *
 * ACCURACY inside the domain: the J series alternates, so cancellation
 * bounds the absolute error by ~(largest term) * eps; the largest term is
 * bounded by I_0(16) ~ 8.9e5, so |error| <~ 2e-10 absolute at the extreme
 * domain corner and far smaller (<1e-12) over the actual plate range
 * x <= 10.958. The I series has all-positive terms (no cancellation).
 * Verified two independent ways in tests/physics_models_repro.cpp:
 * (1) grid comparison against std::cyl_bessel_j/_i on platforms that have
 * them, (2) literature/scipy anchor values that run on EVERY platform,
 * including the libc++ one where std:: is absent.
 */
namespace tsuki
{

inline double besselSeriesPortable (int order, double x, bool modified)
{
    if (order < 0 || order > 8 || ! (x >= 0.0 && x <= 16.0))
        return std::numeric_limits<double>::quiet_NaN();

    // term_0 = (x/2)^m / m!
    double term = 1.0;
    for (int i = 1; i <= order; ++i)
        term *= 0.5 * x / (double) i;

    const double q = 0.25 * x * x * (modified ? 1.0 : -1.0);
    double sum = term;

    // Deterministic termination: fixed recurrence, stop once the term is
    // below 1e-17 relative to the running sum. Hard cap 64 terms: at the
    // domain edge x=16 the term ratio |q|/(k(k+m)) drops below 1 by k=8 and
    // the k=40 term is already ~3e-24 of the peak, so 64 is unreachable in
    // practice and exists only as a loop bound.
    for (int k = 1; k <= 64; ++k)
    {
        term *= q / ((double) k * (double) (k + order));
        sum += term;
        if (std::abs (term) < 1e-17 * (1.0 + std::abs (sum)))
            break;
    }
    return sum;
}

inline double besselJPortable (int order, double x) { return besselSeriesPortable (order, x, false); }
inline double besselIPortable (int order, double x) { return besselSeriesPortable (order, x, true);  }

} // namespace tsuki
