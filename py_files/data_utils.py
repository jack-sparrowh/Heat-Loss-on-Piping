import numpy as np
import pandas as pd

def find_heat_rates(piping_segment, n):

    '''
    Finds total heat lost by fluid as well as average net heat lost.
    Here, total heat lost by fluid is Q_lost_fluid = -m_rate*C*dT_f
    From energy balance A_t*q_s - Q_avg = m_rate*C*dT_f we find Q_avg as
    Q_avg = A_t*q_s - m_rate*C*dT_f = Q_s + Q_lost_fluid
    Then we find average surface temperature that yields
    (Q_avg - pi*D_t*h_vec*dT_sa)**2 = 0
    
    Parameters
    ----------
    piping_segment: class object
    	Filled Piping_Segment class []
    n: int
    	Number of parts to split the given segment to []
    
    Returns
    -------
    total_heat_rate_out: float
    	Total heat lost by the fluid.
    total_heat_from_h_vec(w_minim): float
    	Average net heat lost.
    '''
    
    ps = piping_segment
    
    # calculate heat lost by fluid
    total_heat_rate_out = -ps.mass_flow_rate * ps.specific_heat_capacity * (ps.temp_prof["temp"][n-1] - ps.inlet_temperature) / ps.segment_length
    # calculate heat absorbed by solar radiation
    total_heat_rate_solar = np.pi * ps.total_diameter / 12 * ps.solar_flux
    # find average net heat lost
    total_heat_rate_lost_avg = total_heat_rate_solar + total_heat_rate_out
    
    #find surface temperature that provides the average net heat lost
    surf_w_temp = lambda w: np.array(w * ps.temp_prof["surf_temp"][n-1] + (1 - w) * ps.temp_prof["surf_temp"][0])
    total_heat_from_h_vec = lambda w: np.pi * ps.total_diameter / 12 * ps.h_comb_vec(surf_w_temp(w)) * (surf_w_temp(w) - ps.ambient_temperature)
    _loss = lambda w: (total_heat_rate_lost_avg - total_heat_from_h_vec(w).sum()) ** 2
    w_minim = minimize_scalar(_loss, bounds=[0, 1]).x
    return total_heat_rate_out, total_heat_from_h_vec(w_minim)

def LMTD(T_i, T_e, T_a):

    '''
    Find Log-mean temperature difference.

    Parameters
    ----------
    T_i: float, array-like
    	Inlet temperature [F]
    T_e: float, array-like
    	Exit temperature [F]
    T_a: float, array-like
    	Ambient temperature [F]
    
    Returns
    -------
    _lmtd: float, array-like
    	Log-mean temperature difference.
    '''
    
    # use np.abs for cases when fluid temperature is less than ambient temperature
    _lmtd = ( T_i - T_e ) / ( np.log(np.abs(T_i - T_a)) - np.log(np.abs(T_e - T_a)) )
    return _lmtd

def calculate_total_piping(piping_class, air_surface_class, user_table, properties_table, n=2):

    '''
    Calculate all pipng segments provided by user.
    
    Parameters
    ----------
    piping_class: class object
    	Piping_Segment []
    air_surface_class: class object
    	Air []
    user_table: pd.DataFrame
    	Table specified by user, defining all piping segments []
    properties_table: pd.DataFrame
    	Table specified by user, defining all required properties []
    n: int
    	Number of parts to split the given segment to. Default n=2 []
    
    Returns
    -------
    class_list: list
    	List containing solved Piping_Segment classes for each segment specified by user.
    '''
 
    class_list = []

    for i in range(0, user_table.shape[0]):

        # load air class
        a = air_surface_class(*user_table.loc[i, ['pipe_outer_diameter', 'insulation_thickness']], *properties_table[['ambient_temperature', 'emissivity']])
        
        # load piping class
        if i == 0:
            ps = piping_class(*user_table.loc[0, :], 0, *properties_table[:-1], a.h_combined)
        else:
            ps = piping_class(*user_table.loc[i, :], ps.end_length, ps.temp_prof.loc[n-1, 'temp'], *properties_table[1:-1], a.h_combined)

        # find temperature profile
        ps.temperature_profile(n=n)

        # load heat rates
        ps.heat_rate_psl_total, ps.heat_rate_psl_surface = find_heat_rates(ps, n)

        # append the list
        class_list.append(ps)
    
    return class_list

def final_table(piping_segment_class_list):

    '''
    Takes output from calculate_total_piping and converts it to easy to read pandas DataFrame.
    
    Parameters
    ----------
    piping_segment_class_list: list
    	List containing solved Piping_Segment classes for each segment specified by user []
    
    Returns
    -------
    _final_table: pd.DataFrame
    	Table containing all solved piping segments.
    '''

    # make sure n=2
    assert(piping_segment_class_list[0].temp_prof.shape[0] == 2), print('Number of points must be n=2')
    
    _final_table = pd.DataFrame(
        index=np.arange(0, len(piping_segment_class_list)),
        columns=[
            'segment_length',
            'temperature_inlet',
            'temperature_outlet',
            'surface_temperature_inlet',
            'surface_temperature_outlet',
            'heat_sum',
            'heat_by_radiation',
            'heat_by_convection'
        ],
        dtype=float
    )       
    
    for i in range(len(piping_segment_class_list)):

        _final_table.loc[i, 'segment_length'] = piping_segment_class_list[i].segment_length
        _final_table.loc[i, ['temperature_inlet', 'temperature_outlet']] = piping_segment_class_list[i].temp_prof['temp'].values
        _final_table.loc[i, ['surface_temperature_inlet', 'surface_temperature_outlet']] = piping_segment_class_list[i].temp_prof['surf_temp'].values
        _final_table.loc[i, 'heat_sum'] = piping_segment_class_list[i].heat_rate_psl_total
        _final_table.loc[i, ['heat_by_radiation', 'heat_by_convection']] = piping_segment_class_list[i].heat_rate_psl_surface

    return _final_table

def final_table_units_handler(piping_segment_class_list, units):

    '''
    Converts final table to correct units.

    Parameters
    ----------
    piping_segment_class_list: list
    	List containing solved Piping_Segment classes for each segment specified by user []
    units: str
        Either "SI" or "Imperial" []

    Returns
    -------
    _uh_final_table: pd.DataFrame
        Final table.
    '''

    _uh_final_table = final_table(piping_segment_class_list)

    rename_columns = lambda length, temp, heat: [
        f'Segment Length [{length}]',
        f'Temperature Inlet [{temp}]',
        f'Temperature Outlet [{temp}]',
        f'Surface Temperature Inlet [{temp}]',
        f'Surface Temperature Outlet [{temp}]',
        f'Heat Transfer Total [{heat}]',
        f'Heat Transfer by Radiation [{heat}]',
        f'Heat Transfer by Convection [{heat}]'
    ]

    length, temp, heat = ['ft', 'F', 'BTU/h.ft']

    if units.lower() == 'si':
        length, temp, heat = ['m', 'C', 'W/m']
        _uh_final_table['segment_length'] = _uh_final_table['segment_length'] * 0.3048 # 1 ft = 0.3048 m
        _uh_final_table['temperature_inlet'] = (_uh_final_table['temperature_inlet'] - 32) / 1.8
        _uh_final_table['temperature_outlet'] = (_uh_final_table['temperature_outlet'] - 32) / 1.8
        _uh_final_table['surface_temperature_inlet'] = (_uh_final_table['surface_temperature_inlet'] - 32) / 1.8
        _uh_final_table['surface_temperature_outlet'] = (_uh_final_table['surface_temperature_outlet'] - 32) / 1.8
        _uh_final_table['heat_sum'] = _uh_final_table['heat_sum'] * 0.293071 / 0.3048 # 1 BTU/h.ft = 0.293071 / 0.3048 W/m
        _uh_final_table['heat_by_radiation'] = _uh_final_table['heat_by_radiation'] * 0.293071 / 0.3048 # 1 BTU/h.ft = 0.293071 / 0.3048 W/m
        _uh_final_table['heat_by_convection'] = _uh_final_table['heat_by_convection'] * 0.293071 / 0.3048 # 1 BTU/h.ft = 0.293071 / 0.3048 W/m

    _uh_final_table.columns = rename_columns(length, temp, heat)

    return _uh_final_table.round(2)