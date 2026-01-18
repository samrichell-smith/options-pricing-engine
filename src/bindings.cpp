#include "batch_pricer.hpp"
#include "black_scholes.hpp"

#include <pybind11/pybind11.h>
#include <pybind11/stl.h> // required for automatic std::vector <-> list conversion
#include <sstream>

namespace py = pybind11;

PYBIND11_MODULE(options_pricer, m) {
    m.doc() = "Black-Scholes options pricing engine with analytical Greeks.";

    // --- OptionType enum ---
    py::enum_<OptionType>(m, "OptionType")
        .value("CALL", OptionType::CALL)
        .value("PUT", OptionType::PUT)
        .export_values(); // also exposes op.CALL / op.PUT as module-level names

    // --- Greeks struct ---
    py::class_<Greeks>(m, "Greeks")
        .def_readonly("delta", &Greeks::delta,
                      "dV/dS; positive [0,1] for calls, negative [-1,0] for puts.")
        .def_readonly("gamma", &Greeks::gamma,
                      "d²V/dS²; always positive, largest near ATM.")
        .def_readonly("vega", &Greeks::vega,
                      "dV/dσ per 1% vol move; always positive for long options.")
        .def_readonly("theta", &Greeks::theta,
                      "dV/dT per calendar day; typically negative (time decay).")
        .def("__repr__", [](const Greeks& g) {
            std::ostringstream ss;
            ss << "Greeks(delta=" << g.delta << ", gamma=" << g.gamma << ", vega=" << g.vega
               << ", theta=" << g.theta << ")";
            return ss.str();
        });

    // --- Contract struct ---
    py::class_<Contract>(m, "Contract")
        .def(py::init([](double S, double K, double r, double sigma, double T,
                         OptionType option_type) {
                 return Contract{S, K, r, sigma, T, option_type};
             }),
             py::arg("S"), py::arg("K"), py::arg("r"), py::arg("sigma"), py::arg("T"),
             py::arg("option_type"),
             "Construct a contract from its pricing parameters.")
        .def_readwrite("S", &Contract::S, "Spot price.")
        .def_readwrite("K", &Contract::K, "Strike price.")
        .def_readwrite("r", &Contract::r, "Risk-free rate.")
        .def_readwrite("sigma", &Contract::sigma, "Volatility.")
        .def_readwrite("T", &Contract::T, "Time to expiry in years.")
        .def_readwrite("option_type", &Contract::option_type, "CALL or PUT.");

    // --- Free functions ---
    m.def("price_option", &price_option,
          py::arg("S"), py::arg("K"), py::arg("r"), py::arg("sigma"),
          py::arg("T"), py::arg("option_type"),
          "Compute the Black-Scholes price of a European option.");

    m.def("compute_greeks", &compute_greeks,
          py::arg("S"), py::arg("K"), py::arg("r"), py::arg("sigma"),
          py::arg("T"), py::arg("option_type"),
          "Compute analytical Black-Scholes Greeks for a European option.");

    m.def("price_batch", &price_batch,
          py::arg("contracts"),
          "Price a list of Contract objects. Returns a list of prices in the same order.");
}
