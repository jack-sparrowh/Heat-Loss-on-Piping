import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.integrate import quad

class Air:

    '''
    Describes air properties around piping. 
    Provides all necessary functions for heat transfer coefficient determination.
    
    Parameters
    ----------
    outer_diameter: float, array-like
    	Piping outer diameter [inch]
    insulation_thickness: float, array-like
    	Insulation thickness [inch]
    ambient_temperature: float, array-like
    	Ambient temperature [K]
    emissivity: float
    	Piping surface emissivity []
    
    Returns
    -------
    Air_class: 
    	Air class.
    '''
    
    def __init__(
        self,
        outer_diameter,
        insulation_thickness,
        ambient_temperature,
        emissivity
    ):

        self.total_diameter = outer_diameter + 2 * insulation_thickness
        self.ambient_temperature = ambient_temperature
        self.emissivity = emissivity
        
    
    def cp(
        self,
        ref_temperature
    ):

        '''
        Calculate specific heat capacity of air at reference temperature, which is film temperature of air around piping.
        Model is taken from Cengel, and is fitted to a range 273K - 1800K. Below 273K cp is equal to cp at 273K and above 
        1800K cp is equal to cp at 1800K.
    
        Parameters
        ----------
        ref_temperature: float, array_like
            Reference temperature at insulation-air interface [K]
    
        Returns
        -------
        _cp: float, array_like
            Specific heat capacity [kJ/kg.K]
        '''        
        
        # all constants here come from "Thermodynamics: An Engineering Approach" by Y. Cengel
        _cp_f = lambda ref_temperature: (28.11 + 0.1967e-2 * ref_temperature + 0.4802e-5 * ref_temperature ** 2 - 1.966e-9 * ref_temperature ** 3) / 28.96
        
        # going with np.array below assures that even when ref_temp is int all calculations carry on
        _cp = np.array(_cp_f(ref_temperature))
        _cp[ref_temperature < 273] = _cp_f(273)
        _cp[ref_temperature > 1800] = _cp_f(1800)
        return _cp

    def u(
        self,
        ref_temperature
    ):
    
        '''
        Calculate kinematic viscosity of air at reference temperature, which is film temperature of air around piping.
    
        Parameters
        ----------
        ref_temperature: float, array_like
            Reference temperature at insulation-air interface [K]
    
        Returns
        -------
        _u: float, array_like
            Kinematic viscosity [Pa*s]
        '''
    
        # Sutherland's Law
        _u = 1.458e-6 * ref_temperature ** 1.5 / (ref_temperature + 110.4)
        return _u
    
    def Ra(
        self,
        ambient_temperature,
        surface_temperature,
    ):
    
        '''
        Calculate Rayleigh number of air at film temperature for horizontal cylindrical body. 
        It is assummed that Pr=0.72 for air in all temperature range.
    
        Parameters
        ----------
        surface_temperature: float, array_like
            Insulation surface temperature [K]
        ambient_temperature: float
            Ambient temperature around piping [K]
    
        Returns
        -------
        _Ra: float, array_like
            Rayleigh number.
        '''

        film_temperature = (surface_temperature + ambient_temperature) / 2
    
        # Pr = 0.72 -> mean value for air on range from 220K to 2200K
        # g = 9.81 -> gravitational acceleration
        # P / R = 101.325 / 0.287 -> atmospheric pressure over gas constant for air
        # 0.0254 -> conversion from inch to meter
        _Ra = 0.72 * 9.81 * (101.325 / 0.287) ** 2 *\
            np.abs(surface_temperature - ambient_temperature) / (film_temperature ** 3 * self.u(film_temperature) ** 2) *\
            (self.total_diameter * 0.0254) ** 3
        
        return _Ra
    
    def h_combined(
        self,
        T_surface
    ):
    
        '''
        Calculate combined heat transfer coefficient at insulation-air interface.
        Radiation heat transfer coeff. is in its typical form.
        Convective heat transfer is based on Churchill and Chu correlation formula.
    
        Parameters
        ----------
        surface_temperature: float, array_like
            Insulation surface temperature [C]
    
        Returns
        -------
        _h_comb_vec: array_like
            Array with heat transfer coefficients of radiative and convective effects [W/m2.K]
        '''

        # change to K
        surface_temperature_K = T_surface + 273.15
        ambient_temperature_K = self.ambient_temperature + 273.15
    
        # 5.67E-8 -> Stefan-Boltzmann constant in W/m2.K4
        h_rad = self.emissivity * 5.67E-8 *\
                (surface_temperature_K ** 2 + ambient_temperature_K ** 2) *\
                (surface_temperature_K + ambient_temperature_K)
        
        film_temperature_K = (surface_temperature_K + ambient_temperature_K) / 2
    
        # 1000 -> conversion from kW to W
        # Pr = 0.72 -> mean value for air on range from 220K to 2200K
        # 0.6 + 0.387 / 1.20326 -> constants from Churchill and Chu correlation assuming Pr=0.72
        # 0.0254 -> conversion from inch to meters
        h_conv = 1000 / 0.72 *\
                 (0.6 + 0.387 / 1.20326 * self.Ra(surface_temperature_K, ambient_temperature_K) ** (1/6)) ** 2 *\
                 self.u(film_temperature_K) * self.cp(film_temperature_K) / (self.total_diameter * 0.0254)
    
        _h_comb_vec = np.c_[h_rad, h_conv]
    
        return _h_comb_vec

class Piping_Segment:

    '''
    Describes one piping section defined by user.

    Parameters
    ----------
    outer_diameter: float
        Outer diameter [m]
    inner_diameter: float
        Inner diameter [m]
    insulation_thickness: float
        Insulation thickness [m]
    segment_length: float
        Length of pipng segment [m]
    start_length: float
        Initial cumulative length. If there is more than one segment, then start_length_i = end_segment_(i-1) [m]
    inlet_temperature: float
        Temperature at start length. If there is more than one segment, then inlet_temperature_i = final_temperature_(i-1) [C]
    ambient_temperature: float
        Ambient temperature [C]
    mass_flow_rate: float
        Mass flow rate [kg/h]
    specific_heat_capacity: float
        Specific heat capacity of liquid [kJ/kg.K]
    k_pipe: float
        Thermal conductivity of piping material [W/m.K]
    k_insulation: float
        Thermal conductivity of insulation material [W/m.K]
    heat_flux: float
        Value of heat flux [W/m2]
    h_combined_func: function
        Function for calculating combined heat transfer coeff. Must take one argument only []
    mode: str
        Mode of calculation, either standard, heat flux or heat tracing []
    absorptivity: float
        Absorptivity of piping surface. By default, equal to 0.25 []
    
    Returns
    -------
    Piping_Segment_class: 
        Piping segment class.
    '''
    
    def __init__(
        self,
        outer_diameter,
        inner_diameter,
        insulation_thickness,
        segment_length,
        start_length,
        inlet_temperature,
        ambient_temperature,
        mass_flow_rate,
        specific_heat_capacity,
        k_pipe, 
        k_insulation,
        heat_flux,
        h_combined_func,
        mode,
        absorptivity=1
    ):

        # piping geometry
        # 0.0254 multiplication added for testing
        # in full code it shouldnt be there
        self.outer_diameter = outer_diameter * 0.0254
        self.inner_diameter = inner_diameter * 0.0254
        self.insulation_thickness = insulation_thickness * 0.0254
        self.segment_length = segment_length
        self.start_length = start_length
        self.total_diameter = self.outer_diameter + 2 * self.insulation_thickness
        self.end_length = self.start_length + self.segment_length

        # define variable diameter
        self.D_y = self.total_diameter
        if mode.lower() == "heat tracing":
            self.D_y = self.outer_diameter
        
        # piping thermal properties
        self.k_pipe = k_pipe
        self.k_insulation = k_insulation

        # fluid properties
        self.inlet_temperature = inlet_temperature
        self.ambient_temperature = ambient_temperature
        self.mass_flow_rate = mass_flow_rate
        self.specific_heat_capacity = specific_heat_capacity

        # add heat rate per segment length, that will be populated during solution for total piping
        self.heat_rate_psl_total = 0
        self.heat_rate_psl_surface = 0 

        # heat transfer coefficient functoin
        self.h_comb_vec = lambda T_surface: h_combined_func(T_surface)
        self.h_comb_func = lambda T_surface: h_combined_func(T_surface).sum(1)

        # define derivative function
        self.derivative = lambda f, x: ( f(x+0.00001) - f(x-0.00001) ) / 0.00002

        # heat flux
        # we always want to use flux helper as it sets proper bounds for all cases
        self.heat_flux_abs = heat_flux * absorptivity
        if mode.lower() == 'standard':
            self.heat_flux_abs = 0
        self.heat_flux_abs_helper()

    def U_x(self, kind):

        '''
        Calculates heat transfer coeff. for different layers.
        fx - from fluid to x in insulation
        xs - from x in insulation to surface

        Parameters
        ----------
    
        Returns
        -------
        _U_fs: float, array_like
            heat transfer coeff. [W/m2.K]
        '''
        
        pseudo_R_fx = np.log( self.outer_diameter / self.inner_diameter ) / self.k_pipe +\
            np.log( self.D_y / self.outer_diameter ) / self.k_insulation
        
        pseudo_R_xs = np.log( self.total_diameter / self.D_y ) / self.k_insulation

        _U_fx = 2 / (self.total_diameter * pseudo_R_fx)
        
        if self.D_y == self.total_diameter:
            _U_xs = np.inf
        else:
            _U_xs = 2 / (self.total_diameter * pseudo_R_xs)

        if kind == "fx":
            _U_x = _U_fx

        elif kind == "rx":
            _u_rx = 1 + _U_fx / _U_xs
            _U_x = _u_rx

        return _U_x
    
    def find_fluid_temperature(
        self, 
        T_surface
    ):
    
        '''
        Calculate fluid temperature at provided surface temperature.
    
        Parameters
        ----------
        T_surface: float, array_like
            Insulation surface temperature [C]
    
        Returns
        -------
        _T_fluid: float, array_like
            Temperature calculated at provided surface temperature [C]
        '''

        _T_fluid = T_surface + ( self.U_x('rx') * self.h_comb_func(T_surface) *\
            (T_surface - self.ambient_temperature) - self.D_y / self.total_diameter * self.heat_flux_abs ) /\
            self.U_x('fx')
    
        self.fluid_temperature = _T_fluid

        return self.fluid_temperature

    def find_inlet_surface_temperature(
        self
    ):
        '''
        Calculate inlet surface temperature.

        Function minimizes squared difference of:
        U_fx*(T_f-T_s) + D_y/D_t*q - u_rx*h(T_s)*(T_s-T_a)

        Parameters
        ----------
        
        Returns
        -------
        self.inlet_surface_temperature: float
        	Inlet surface temperature.
        '''

        _T_surf_loss_func = lambda T_surface: (
            self.U_x('fx') * (self.inlet_temperature - T_surface) +\
            self.D_y / self.total_diameter * self.heat_flux_abs -\
            self.U_x('rx') * self.h_comb_func(T_surface) * (T_surface - self.ambient_temperature)
        ) ** 2

        # we use sorted() for when inlet temperature is lower than ambient temperature
        # it is important to use bracket here as starting interval
        # it is important to use bounds with 0R as lower bound,
        # this is because for very large heat_flux values minimize_scalar might try values of negative K
        self.minim_inlet_surface_temperature = minimize_scalar(
            _T_surf_loss_func,
            bracket=sorted([self.ambient_temperature, self.inlet_temperature]),
            bounds=[-273.15, 1E9]
        )

        # make sure to extract float, so scipy can accept it
        self.inlet_surface_temperature = self.minim_inlet_surface_temperature.x[0]

    def heat_flux_abs_helper(
        self,
        threshold=0.001
    ):

        '''
        Function setting bounds for all cases and updating heat flux if
        it is close within threshold value of critical point of integrand.

        Parameters
        ----------
        threshold: float
            Determines how close heat flux must be to trigger update. Default 1 []
        
        Returns
        -------
        '''
        
        # initiate by finding inlet surface temperature
        self.find_inlet_surface_temperature()
        
        # calculate constant temperature heat flux
        self.const_temp_heat_flux_abs = self.total_diameter / self.D_y *\
            self.h_comb_func(self.inlet_surface_temperature) * (self.inlet_surface_temperature - self.ambient_temperature)

        # find how close provided heat flux is to constant temp heat flux
        _closeness = self.heat_flux_abs / self.const_temp_heat_flux_abs - 1

        _loss = lambda T_s: (
            self.h_comb_func(T_s) *\
            (T_s - self.ambient_temperature) -\
            self.D_y / self.total_diameter * self.heat_flux_abs
        ) ** 2

        if _closeness >= 0:

            # update bounds for heating
            upper_bound = minimize_scalar(_loss).x[0]
            self.bounds = sorted([self.inlet_surface_temperature, upper_bound])

            if _closeness <= threshold:
                # update heat flux value to escape critical point of integrand
                self.heat_flux_abs = (1 + threshold) * self.const_temp_heat_flux_abs

        else:

            # update bounds for cooling
            lower_bound = minimize_scalar(_loss).x[0]
            self.bounds = sorted([lower_bound, self.inlet_surface_temperature])

            if _closeness >= -threshold:
                # update heat flux value to escape critical point of integrand
                self.heat_flux_abs = (1 - threshold) * self.const_temp_heat_flux_abs
    
    def integrand(
        self,
        T_surface
    ):
        '''
        Find value of integrand, given surface temperature.

        Parameters
        ----------
        T_surface: float
        	Insulation surface temperature [C]
        
        Returns
        -------
        _integrand: float
        	Calculated integrand.
        '''

        _integrand_p1 = self.h_comb_func(T_surface) * (T_surface - self.ambient_temperature) -\
            self.D_y / self.total_diameter * self.heat_flux_abs
        _integrand_p2 = 1 + self.U_x('rx') * self.h_comb_func(T_surface) / self.U_x('fx') +\
            self.U_x('rx') * (T_surface - self.ambient_temperature) / self.U_x('fx') *\
            self.derivative(self.h_comb_func, T_surface)
        _integrand = 1 / _integrand_p1 * _integrand_p2

        # make sure to extract float, so scipy can accept it
        return _integrand[0]

    def integral_loss_function(
        self,
        T_surface,
        length
    ):

        '''
        Calculates squared sum of integral over surface temperature and integral over distance.

        Parameters
        ----------
        T_surface: float
        	Insulation surface temperature [C]
        length: float
        	Distance at which to find surface temperature [m]
        
        Returns
        -------
        loss_function: float
        	Calculated loss.
        '''
        
        _lambda = self.mass_flow_rate * self.specific_heat_capacity / (np.pi * self.total_diameter)
        integral = quad(self.integrand, self.inlet_surface_temperature, T_surface, limit=500)
        loss = (integral[0] + length / _lambda) ** 2

        return loss

    def find_surface_temperature(
        self,
        length
    ):

        '''
        Finds surface temperature, at specified length by minimizing integral_loss_funciton.

        Parameters
        ----------
        length: float
        	Distance at which to find surface temperature [m]
        
        Returns
        -------
        self.surface_temperature: float
        	Surface temperature.
        '''

        self.minim_surface_temperature = minimize_scalar(
            self.integral_loss_function,
            bounds=self.bounds,
            args=(length)
        )

        self.surface_temperature = self.minim_surface_temperature.x
        
        return self.surface_temperature
        
    def temperature_profile(self, n=2):

        '''
        Find fluid temperature over a whole segment.
        Parameter n controls to how many parts a given segment is to be split to.
        Calculations are carried out by filling separate lists, and then they are combined
        to one pandas dataframe. At the end, this dataframe is saved into class as "temp_prof".
        
        Parameters
        ----------
        n: int
        	Number of parts to split the given segment to. Default n=2 []
        
        Returns
        -------
        self.temp_prof: pd.DataFrame
        	Temperature profile.
        '''

        # initialize at x=0
        temp_profile = [self.inlet_temperature]
        surf_temp_profile = [self.inlet_surface_temperature]
        segment_length = [0]

        # run through rest n-1 segments
        for _l in np.linspace(self.segment_length / (n - 1), self.segment_length, n - 1):
 
            _T_surf_l = self.find_surface_temperature(_l)
            _T_l = self.find_fluid_temperature(_T_surf_l)

            temp_profile.append(_T_l[0])
            surf_temp_profile.append(_T_surf_l)
            segment_length.append(_l)

        _result_df = pd.DataFrame(
            np.c_[segment_length, temp_profile, surf_temp_profile],
            columns=["length", "temp", "surf_temp"]
        )

        self.temp_prof = _result_df

        return self.temp_prof