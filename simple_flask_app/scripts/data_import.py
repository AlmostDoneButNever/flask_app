import pandas as pd
import numpy as np

def data_import(path):

    data = {}
    basis = {}
    service = {}
    revenue_change = {}
    bess = {}

    data['basis'] = pd.read_excel(path, sheet_name= 'basis', usecols="C:D", index_col=0, names = ['parameter', 'value'])
    data['basis']  = data['basis'].dropna().drop(['Tag']).replace({'YES': 1, 'NO': 0})

    data['bess'] = pd.read_excel(path, sheet_name= 'bess', usecols="C:D", index_col=0, names = ['parameter', 'value'])
    data['bess']  = data['bess'].dropna().drop(['Tag', np.nan]).replace({'YES': 1, 'NO': 0})

    data['schedule'] = pd.read_excel(path, sheet_name= 'schedule', index_col=0, skiprows=7)
    data['schedule'].columns = ['arb', 'reg', 'pres','cres', 'ec', 'dr', 'il']

    data['activation'] = pd.read_excel(path, sheet_name= 'activation', index_col=0, skiprows=7)
    data['activation'].columns = ['reg', 'pres','cres', 'dr', 'il']
    data['activation']['reg_up'] = data['activation']['reg'].apply(lambda x: x if x > 0 else 0)
    data['activation']['reg_down'] = data['activation']['reg'].apply(lambda x: -x if x < 0 else 0)

    data['reserve'] = pd.read_excel(path, sheet_name= 'reserve', index_col=0, skiprows=7)
    data['reserve'].columns = ['reg', 'pres','cres', 'dr', 'il']

    data['soc_limit'] = pd.read_excel(path, sheet_name= 'soc_limit', index_col=0, skiprows=7)
    data['soc_limit'].columns = ['min', 'max']

    data['load'] = pd.read_excel(path, sheet_name= 'load', index_col=0, skiprows=7)
    data['load'].columns = ['period', 'value']

    data['prices'] = pd.read_excel(path, sheet_name= 'prices', index_col=0, skiprows=7)
    data['prices'].columns = ['period', 'arb_energy_price', 'reg_capacity_price', 'pres_capacity_price', 
                                'cres_capacity_price', 'dr_capacity_price', 'il_capacity_price', 
                                'ec_energy_price', 'reg_down_capacity_price', 'reg_energy_price', 
                                'reg_down_energy_price', 'pres_energy_price', 'cres_energy_price', 
                                'dr_energy_price', 'il_energy_price'
                                ]           

    basis['annual_time_period'] = data['basis'].value.loc['annual_time_period']
    basis['model_time_period'] = data['basis'].value.loc['model_time_period']
    basis['dt'] = data['basis'].value.loc['dt']
    basis['wacc'] = data['basis'].value.loc['wacc']/100

    service['arb'] = data['basis'].value.loc['service_arb']
    service['reg'] = data['basis'].value.loc['service_reg']
    service['pres'] = data['basis'].value.loc['service_pres']
    service['cres'] = data['basis'].value.loc['service_cres']
    service['ec'] = data['basis'].value.loc['service_ec']
    service['dr'] = data['basis'].value.loc['service_dr']
    service['il'] = data['basis'].value.loc['service_il']
    service['reg_symmetric'] = data['basis'].value.loc['reg_symmetric']
    service['reg_activate'] = data['basis'].value.loc['reg_activate']
    service['load'] = data['basis'].value.loc['service_load']

    revenue_change['arb'] = data['basis'].value.loc['dev_rev_arb']
    revenue_change['reg'] = data['basis'].value.loc['dev_rev_reg']
    revenue_change['pres'] = data['basis'].value.loc['dev_rev_pres']
    revenue_change['cres'] = data['basis'].value.loc['dev_rev_cres']
    revenue_change['ec'] = data['basis'].value.loc['dev_rev_ec']
    revenue_change['dr'] = data['basis'].value.loc['dev_rev_dr']
    revenue_change['il'] = data['basis'].value.loc['dev_rev_il']

    bess['cap_power'] = data['bess'].value.loc['cap_power']
    bess['cap_energy'] = data['bess'].value.loc['cap_energy']
    bess['c_eff'] = data['bess'].value.loc['eff_charge']/100
    bess['d_eff'] = data['bess'].value.loc['eff_discharge']/100
    bess['s_eff'] = data['bess'].value.loc['eff_storage']/100
    bess['initial_soc'] = data['bess'].value.loc['initial_charge']/100
    bess['max_soc'] = data['bess'].value.loc['max_soc']/100
    bess['min_soc'] = 1 - data['bess'].value.loc['max_dod']/100
    bess['cycle_life'] = int(data['bess'].value.loc['cycle_life'])
    bess['calendar_life'] = int(data['bess'].value.loc['calendar_life'])
    bess['daily_cycle'] = data['bess'].value.loc['daily_cycle']
    bess['fixed_capex'] = data['bess'].value.loc['bess_fixed_capex']
    bess['energy_capex'] = data['bess'].value.loc['bess_energy_capex']
    bess['power_capex'] = data['bess'].value.loc['bess_power_capex']
    bess['fixed_opex'] = data['bess'].value.loc['bess_fixed_opex']
    bess['energy_opex'] = data['bess'].value.loc['bess_energy_opex']
    bess['power_opex'] = data['bess'].value.loc['bess_power_opex']

    return data, basis, bess, service, revenue_change
