import numpy as np
import pandas as pd

def user_table_prepare(user_table, units):
    
    '''
    Take Nx4 datafame and make it Mx4 where M is the amount of rows completely filled by user. 
    Excel treats empty cells as 0, and we don't expect user to provide whole row filled with 0 at any point.

    Parameters
    ----------
    user_table: pd.DataFrame
        User table []
    units: str
        Either "SI" or "Imperial" []
    
    Returns
    -------
    prep_user_table: pd.DataFrame
        Prepared User Table.
    '''
    
    user_table.columns = [
        'pipe_outer_diameter', 
        'pipe_inner_diameter', 
        'insulation_thickness', 
        'segment_length'
    ]
    prep_user_table = user_table[user_table.notnull().all(1)].copy()

    if units.lower() == 'imperial':
        prep_user_table.loc[:, 'segment_length'] *= 0.3048 # 1 ft = 0.3048 m

    # diameter and insulation thickness is always in inches, convert them to meters
    prep_user_table.loc[:, 
        [
            'pipe_outer_diameter',
            'pipe_inner_diameter',
            'insulation_thickness'
        ]
    ] *= 0.0254 # 1 inch = 0.0254 m
    
    return prep_user_table
    
def prop_table_prepare(properties_table):
    
    '''
    Simple handling of properties table. Take 1x9 dataframe and add names to indicies and convert to series for ease of calling.

    Parameters
    ----------
    properties_table: pd.DataFrame
        Properties table []
    
    Returns
    -------
    prep_properties_table: pd.DataFrame
        Prepared properties table. 
    '''

    # to be updated with heat flux etc
    prep_properties_table = properties_table.copy().iloc[:, 0]
    prep_properties_table.name = 'Values'
    prep_properties_table.index = [
        'inlet_temperature',
		'ambient_temperature',
        'mass_flow_rate',
        'specific_heat_capacity',
        'k_pipe',
        'k_insulation',
        'emissivity'
    ]
    return prep_properties_table

def prop_table_units_handler(properties_table, units):
    
    '''
    Converts all SI units to Impertial if units is SI, otherwise does nothing.

    Parameters
    ----------
    properties_table: pd.DataFrame
        Properties table []
    units: str
        Either "SI" or "Imperial" []
    
    Returns
    -------
    units_handled_prop_table: pd.DataFrame
        Prepared properties table, with handled units.
    '''
    
    _uh_prop_table = prop_table_prepare(properties_table)

    # to be updated with heat flux etc
    if units.lower() == 'imperial':
        _uh_prop_table['inlet_temperature'] = (_uh_prop_table['inlet_temperature'] - 32) / 1.8
        _uh_prop_table['ambient_temperature'] = (_uh_prop_table['ambient_temperature'] - 32) / 1.8
        _uh_prop_table['mass_flow_rate'] *= 0.453592 # 1 lb/h = 0.453592 kg/h
        _uh_prop_table['specific_heat_capacity'] *= 4.1868 # 1 BTU/lb.F = 4.1868 kJ/kg.K
        _uh_prop_table['k_pipe'] *= 1.73073 # 1 BTU/ft.h.F = 1.73073 W/m.K
        _uh_prop_table['k_insulation'] *= 1.73073 # 1 BTU/ft.h.F = 1.73073 W/m.K
    
    return _uh_prop_table

def user_units(units):
    
    '''
    Prints out all necessary units based on choosen metric system.

    Parameters
    ----------
    units: str
        Either "SI" or "Imperial" []
    
    Returns
    -------
    units_list: list
        List of units.
    '''

    # to be updated with heat flux etc
    units_list = [
            'C',
            'C',
            'kg/h',
            'kJ/kg.K',
            'W/m.K',
            'W/m.K'
            ''
        ]
    
    if units.lower() == 'imperial':
        units_list = [
        'F',
        'F',
        'lbm/h',
        'BTU/lbm.F',
        'BTU/ft.h.F',
        'BTU/ft.h.F'
        ''
    ]
    
    return units_list
    
def segment_length_print(units):
    
    '''
    Prints out units of length based on choosen metric system.

    Parameters
    ----------
    units: str
        Either "SI" or "Imperial" []
    
    Returns
    -------
    string: str
        String of length units.
    '''
    length = 'm'
    if units.lower() == 'imperial':
        length = 'ft'
    
    return f'Segment length [{length}]'