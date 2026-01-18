#include "../src/black_scholes.hpp"

#include <cassert>
#include <cmath>
#include <cstdio>

// ---------------------------------------------------------------------------
// Test 1: Call-put parity
// C - P = S - K*exp(-rT)  (must hold to within floating-point noise)
// ---------------------------------------------------------------------------
static void test_call_put_parity() {
    const double S = 100.0, K = 100.0, r = 0.05, sigma = 0.20, T = 1.0;
    const double call    = price_option(S, K, r, sigma, T, OptionType::CALL);
    const double put     = price_option(S, K, r, sigma, T, OptionType::PUT);
    const double forward = S - K * std::exp(-r * T);
    assert(std::abs((call - put) - forward) < 1e-10 &&
           "Call-put parity violated: C - P != S - K*exp(-rT)");
}

// ---------------------------------------------------------------------------
// Test 2: Deep ITM call delta must be near 1
// S=200, K=100: d1 >> 0, so N(d1) -> 1
// ---------------------------------------------------------------------------
static void test_deep_itm_delta() {
    const Greeks g = compute_greeks(200.0, 100.0, 0.05, 0.20, 1.0, OptionType::CALL);
    assert(g.delta > 0.99 && "Deep ITM call delta should be > 0.99 (got less)");
}

// ---------------------------------------------------------------------------
// Test 3: Deep OTM call delta must be near 0
// S=50, K=200: d1 << 0, so N(d1) -> 0
// ---------------------------------------------------------------------------
static void test_deep_otm_delta() {
    const Greeks g = compute_greeks(50.0, 200.0, 0.05, 0.20, 1.0, OptionType::CALL);
    assert(g.delta < 0.01 && "Deep OTM call delta should be < 0.01 (got more)");
}

// ---------------------------------------------------------------------------
// Test 4: Vega symmetry
// Call and put with identical parameters must have identical vega.
// ---------------------------------------------------------------------------
static void test_vega_symmetry() {
    const double S = 100.0, K = 100.0, r = 0.05, sigma = 0.20, T = 1.0;
    const Greeks cg = compute_greeks(S, K, r, sigma, T, OptionType::CALL);
    const Greeks pg = compute_greeks(S, K, r, sigma, T, OptionType::PUT);
    assert(std::abs(cg.vega - pg.vega) < 1e-10 &&
           "Vega must be equal for call and put with identical parameters");
}

int main() {
    test_call_put_parity();
    test_deep_itm_delta();
    test_deep_otm_delta();
    test_vega_symmetry();
    std::puts("All tests passed.");
    return 0;
}
