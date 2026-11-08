# Heat Loss on Piping with Heat Flux

A Python-based tool implemented in Excel for easily calculating heat loss (or gain) of fluid flowing through insulated piping systems. This tool allows users to model various thermal scenarios, including convection, radiation, and external/internal heat flux applications.

The main idea behind this project is to provide results as accurate as possible with the least user input required. There is no external database to be connected and no additional calculations needed. There is a possibility for user to provide density and viscosity to correct values like volumetric flow rate and Raynold's number. If no value is provided the values are provided for water with denisty at $20^{o}$ C and viscosity at mean temperature between inlet and outlet for given segment. For more information, refer to User Guide.

## How It Works (Brief Overview)

The tool calculates heat transfer by integrating the effects of convection, radiation, and applied fluxes across the piping insulation system. Users can select the appropriate mode to match their physical scenario: Standard for passive loss/gain, External Flux for environmental loading, or Heat Tracing for active heating requirements.

## Features

*   **Versatile Calculation Modes:**
    *   **(1) Standard:** Calculates total heat loss considering **convection** and **radiation**.
    *   **(2) External Heat Flux:** Applies an external heat flux (e.g., solar radiation) directly onto the insulation surface.
    *   **(3) Heat Tracing:** Applies a specific heat flux at the piping-insulation interface to model active heating/tracing.
*   **Emissivity Control:** Easily select and input the emissivity ($\epsilon$) of the insulation surface for accurate radiation calculations.
*   **Dual Implementation:** Available as a user-friendly **Excel IDE** or runnable Python scripts.

## Installation

You have two simple options to get started:

1.  **Excel IDE (Recommended):** Download and open the provided Excel file directly.
2.  **Python Files:** Clone the repository and run the necessary Python scripts.

## Usage Examples

Detailed examples demonstrating how to use each calculation mode are provided in separate files within this repository:

*   [Standard calculations](https://github.com/jack-sparrowh/Heat-Loss-on-Piping/blob/main/Examples/Standard.ipynb)
*   [External Heat Flux](https://github.com/jack-sparrowh/Heat-Loss-on-Piping/blob/main/Examples/External%20Heat%20Flux.ipynb)
*   [Heat Tracing](https://github.com/jack-sparrowh/Heat-Loss-on-Piping/blob/main/Examples/Heat%20Tracing.ipynb)
