from pyomo.environ import *

def optimize_revenue(initial_soc, data_input, prices, loads, final_soc_target, cap_settings):

    data, basis, bess, service = data_input

    if cap_settings: 
        cap_power = cap_settings[0]
        cap_energy = cap_settings[1]
    else:
        cap_power = bess['cap_power']
        cap_energy = bess['cap_energy']

    price_df = prices

    if service['load'] == 1:
        load_profile = loads.value

    # Parameters
    lamda_min = data['soc_limit']['min']
    lamda_max = data['soc_limit']['max']
    theta = data['schedule']
    beta = data['activation']
    gamma = data['reserve']

    dt = basis['dt']


    Seff = bess['s_eff']
    Ceff = bess['c_eff']
    Deff = bess['d_eff']
    lamda_max_tech = bess['max_soc']
    lamda_min_tech = bess['min_soc']
    eta = bess['daily_cycle']

    # Price Data for the day
    total_time_period = len(price_df)

    T = range(1, total_time_period + 1)
    SOC_T = range(0, total_time_period + 1)

    p_arb = price_df['arb_energy_price']
    p_reg_up_c = price_df['reg_capacity_price']
    p_reg_up_e = price_df['reg_energy_price']
    p_reg_down_c = price_df['reg_down_capacity_price']
    p_reg_down_e = price_df['reg_down_energy_price']
    p_pres_c = price_df['pres_capacity_price']
    p_pres_e = price_df['pres_energy_price']
    p_cres_c = price_df['cres_capacity_price']
    p_cres_e = price_df['cres_energy_price']
    p_ec = price_df['ec_energy_price']
    p_dr_c = price_df['dr_capacity_price']
    p_dr_e = price_df['dr_energy_price']
    p_il_c = price_df['il_capacity_price']
    p_il_e = price_df['il_energy_price']

    # Define the model
    model = ConcreteModel()

    # Variables
    model.SOC = Var(SOC_T, within=NonNegativeReals, bounds = (0, cap_energy))
    model.E_c = Var(T, within=NonNegativeReals, bounds = (0, cap_energy))
    model.E_cr = Var(T, within=NonNegativeReals, bounds = (0, cap_energy))
    model.E_d = Var(T, within=NonNegativeReals, bounds = (0, cap_energy))
    model.E_dr = Var(T, within=NonNegativeReals, bounds = (0, cap_energy))
 
    model.PC_arb = Var(T, within=NonNegativeReals, bounds = (0, cap_power * 2))
    model.PD_arb = Var(T, within=NonNegativeReals, bounds = (0, cap_power * 2))
    model.P_reg = Var(T, within=NonNegativeReals, bounds = (0, cap_power * 2))
    model.PC_reg = Var(T, within=NonNegativeReals, bounds = (0, cap_power * 2))
    model.PD_reg = Var(T, within=NonNegativeReals, bounds = (0, cap_power * 2))
    model.P_pres = Var(T, within=NonNegativeReals, bounds = (0, cap_power * 2))
    model.P_cres = Var(T, within=NonNegativeReals, bounds = (0, cap_power * 2))

    model.P_ec = Var(T, within=NonNegativeReals)
    model.PL_ec = Var(T, within=NonNegativeReals)
    model.PC_ec = Var(T, within=NonNegativeReals, bounds = (0, cap_power * 2))
    model.PD_L = Var(T, within=NonNegativeReals, bounds = (0, cap_power * 2))
    model.P_dr = Var(T, within=NonNegativeReals, bounds = (0, cap_power * 2))
    model.P_il = Var(T, within=NonNegativeReals, bounds = (0, cap_power * 2))

    # model.y_ch = Var(T, within=Binary)
    model.y_minus = Var(T, within=Binary)

    model.R_arb = Var(T, within=Reals)
    model.R_reg = Var(T, within=Reals)
    model.R_pres = Var(T, within=Reals)
    model.R_cres = Var(T, within=Reals)
    model.R_ec = Var(T, within=Reals)
    model.R_dr = Var(T, within=Reals)
    model.R_il = Var(T, within=Reals)

    # Objective function
    model.obj = Objective(
        expr= sum(model.R_arb[t] + model.R_reg[t] + model.R_pres[t] + model.R_cres[t] 
                  + model.R_ec[t] + model.R_dr[t] + model.R_il[t] 
                  for t in T),        
        sense=maximize
    )

    def revenue_arbitrage_rule(model, t):
        return model.R_arb[t] == p_arb[t]  * (model.PD_arb[t] - model.PC_arb[t]) * dt
    model.revenue_arbitrage = Constraint(T, rule=revenue_arbitrage_rule)

    def revenue_primary_reserve_rule(model, t):
        return model.R_pres[t] == (p_pres_c[t]  * model.P_pres[t]
                                        + p_pres_e[t] * beta['pres'][t] * model.P_pres[t]) * dt
    model.revenue_preserve = Constraint(T, rule=revenue_primary_reserve_rule)

    def revenue_contingency_reserve_rule(model, t):
        return model.R_cres[t] == (p_cres_c[t]  * model.P_cres[t]
                                        + p_cres_e[t] * beta['cres'][t] * model.P_cres[t]) * dt
    model.revenue_creserve = Constraint(T, rule=revenue_contingency_reserve_rule)

    if service['reg_symmetric'] == 1:
        def reg_constraint_rule(model, t):
            return model.P_reg[t] == model.PC_reg[t]  + model.PD_reg[t] 
        model.reg_up_down = Constraint(T, rule=reg_constraint_rule)

        def revenue_regulation_rule(model, t):
            return model.R_reg[t] == (p_reg_up_c[t]  * model.P_reg[t]
                                            + p_reg_up_e[t] * beta['reg'][t] * model.P_reg[t]) * dt
        model.revenue_regulation = Constraint(T, rule=revenue_regulation_rule)

    else:

        def revenue_regulation_rule(model, t):
            return model.R_reg[t] == (p_reg_up_c[t]  * model.PD_reg[t] * beta['reg_up_activated'][t] 
                                            + p_reg_down_c[t]  * model.PC_reg[t] * beta['reg_down_activated'][t]
                                            + p_reg_up_e[t] * beta['reg_up'][t] * model.PD_reg[t]
                                            - p_reg_down_e[t] * beta['reg_down'][t] * model.PC_reg[t]
                                            ) * dt
        model.revenue_regulation = Constraint(T, rule=revenue_regulation_rule)


    def revenue_energy_charge_rule(model, t):
        if service['load'] == 1:
            return model.R_ec[t] == p_ec[t]  * (load_profile[t] - model.P_ec[t] * dt) 
        else:
            return model.R_ec[t] == 0
    model.revenue_energy_charge = Constraint(T, rule=revenue_energy_charge_rule)

    def revenue_demand_response_rule(model, t):
        return model.R_dr[t] == (p_dr_c[t]  * model.P_dr[t]
                                        + p_dr_e[t] * beta['dr'][t] * model.P_dr[t]) * dt
    model.revenue_demand_response = Constraint(T, rule=revenue_demand_response_rule)

    def revenue_interruptible_load_rule(model, t):
        return model.R_il[t] == (p_il_c[t]  * model.P_il[t]
                                        + p_il_e[t] * beta['il'][t] * model.P_il[t]) * dt
    model.revenue_interruptible_load = Constraint(T, rule=revenue_interruptible_load_rule)


    # Power balance
    def total_charge_rule(model, t):
        return model.PC_arb[t] + model.PC_reg[t] + model.PC_ec[t]  <= cap_power * model.y_minus[t]
    model.total_charge = Constraint(T, rule=total_charge_rule)

    def total_discharge_rule(model, t):
        return model.PD_arb[t] +  model.PD_reg[t] + model.P_pres[t] +  model.P_cres[t] \
                    + model.PD_L[t] + model.P_dr[t] +  model.P_il[t] <= cap_power * (1 - model.y_minus[t])
    model.total_discharge = Constraint(T, rule=total_discharge_rule)

    # Power balance for BTM services
    def total_grid_power_rule(model, t):
        return model.P_ec[t] == model.PL_ec[t] + model.PC_ec[t]
    model.total_grid_power = Constraint(T, rule=total_grid_power_rule)

    if service['load'] == 1:
        def total_load_balance_rule(model, t):
            return (model.PL_ec[t] +  model.PD_L[t] + beta['dr'][t] * model.P_dr[t] + beta['il'][t] * model.P_il[t]) * dt == load_profile[t]
        model.total_load_balance = Constraint(T, rule=total_load_balance_rule)

    # Energy balance
    
    def energy_discharge_rule(model, t):
        return model.E_d[t] == (model.PD_arb[t] + model.PD_L[t]
                                + beta['reg_up'][t] * model.PD_reg[t]
                                + beta['pres'][t] * model.P_pres[t]
                                + beta['cres'][t] * model.P_cres[t]
                                + beta['dr'][t] * model.P_dr[t]
                                + beta['il'][t] * model.P_il[t]
                                ) * dt
    model.energy_discharge = Constraint(T, rule=energy_discharge_rule)

    def energy_discharge_reserve_rule(model, t):
        return model.E_dr[t] == (
                                   (gamma['reg'][t] - beta['reg_up'][t]) * model.PD_reg[t]
                                +  (gamma['pres'][t] - beta['pres'][t]) * model.P_pres[t]
                                +  (gamma['cres'][t] - beta['cres'][t]) * model.P_cres[t]
                                +  (gamma['dr'][t] - beta['dr'][t]) * model.P_dr[t]
                                +  (gamma['il'][t] - beta['il'][t]) * model.P_il[t]
                                ) * dt
    model.energy_discharge_reserve = Constraint(T, rule=energy_discharge_reserve_rule)

    def energy_charge_rule(model, t):
        return model.E_c[t] == (model.PC_arb[t]  
                                + beta['reg_down'][t] * model.PC_reg[t]
                                + model.PC_ec[t]  
                                ) * dt
    model.energy_charge = Constraint(T, rule=energy_charge_rule)

    def energy_charge_reserve_rule(model, t):
        return model.E_cr[t] == ((gamma['reg'][t] - beta['reg_down'][t]) * model.PC_reg[t]) * dt
    model.energy_charge_reserve = Constraint(T, rule=energy_charge_reserve_rule)


    def soc_constraints(model, t):
        if t == 0:
            return model.SOC[t] == initial_soc
        else:
            return model.SOC[t] == model.SOC[t-1] * Seff + model.E_c[t] * Ceff - model.E_d[t]/Deff
    model.SOC_constraints = Constraint(SOC_T, rule=soc_constraints)

    def soc_lower_limit_constraint(model, t):
        return model.SOC[t] - model.E_dr[t]/Deff >= cap_energy * lamda_min[t]
    model.SOC_lower_limit = Constraint(T, rule=soc_lower_limit_constraint)

    def soc_upper_limit_constraint(model, t):
        return model.SOC[t] + model.E_cr[t] * Ceff <= cap_energy * lamda_max[t]
    model.SOC_upper_limit = Constraint(T, rule=soc_upper_limit_constraint)

    if final_soc_target:
        def soc_final_state_constraint(model):
            end_t = SOC_T[-1]
            return model.SOC[end_t] == bess['initial_soc'] * cap_energy
        model.SOC_final = Constraint(rule=soc_final_state_constraint)


    # Cycle limits

    if service['reg_activate'] != 1:

        def cycle_charge_constraint(model):
            return sum(model.PC_arb[t] + model.PC_ec[t] +  model.PC_reg[t] * gamma['reg'][t] for t in T)*dt <= eta * cap_energy * (lamda_max_tech - lamda_min_tech)
        model.cycle_charge = Constraint(rule=cycle_charge_constraint)

        def cycle_discharge_constraint(model):
            return sum(model.PD_arb[t] + model.PD_L[t] + model.PD_reg[t] * gamma['reg'][t] for t in T)*dt <= eta * cap_energy * (lamda_max_tech - lamda_min_tech)
        model.cycle_discharge = Constraint(rule=cycle_discharge_constraint)

    else:

        def cycle_charge_constraint(model):
            return sum(model.PC_arb[t] + model.PC_ec[t] +  model.PC_reg[t] * beta['reg_down'][t] for t in T)*dt <= eta * cap_energy * (lamda_max_tech - lamda_min_tech)
        model.cycle_charge = Constraint(rule=cycle_charge_constraint)

        def cycle_discharge_constraint(model):
            return sum(model.PD_arb[t] + model.PD_L[t] + model.PD_reg[t] * beta['reg_up'][t] for t in T)*dt <= eta * cap_energy * (lamda_max_tech - lamda_min_tech)
        model.cycle_discharge = Constraint(rule=cycle_discharge_constraint)


    # Service availability

    def arbitrage_availability_rule(model, t):
        return model.PC_arb[t] + model.PD_arb[t] <= cap_power * service['arb'] * theta['arb'].loc[t] * 999999
    model.arbitrage_availability = Constraint(T, rule=arbitrage_availability_rule)

    def regulation_availability_rule(model, t):
        return model.PC_reg[t] + model.PD_reg[t] <= cap_power * service['reg'] * theta['reg'].loc[t] * 999999
    model.regulation_availability = Constraint(T, rule=regulation_availability_rule)

    def preserve_availability_rule(model, t):
        return model.P_pres[t] <= cap_power * service['pres'] * theta['pres'].loc[t] * 999999
    model.preserve_availability = Constraint(T, rule=preserve_availability_rule)

    def creserve_availability_rule(model, t):
        return model.P_cres[t] <= cap_power * service['cres'] * theta['cres'].loc[t] * 999999
    model.creserve_availability = Constraint(T, rule=creserve_availability_rule)

    def energy_charge_availability_rule(model, t):
        return model.P_ec[t] <= cap_power * service['ec'] * theta['ec'].loc[t] * 999999
    model.energy_charge_availability = Constraint(T, rule=energy_charge_availability_rule)

    def demand_response_availability_rule(model, t):
        return model.P_dr[t] <= cap_power * service['dr'] * theta['dr'].loc[t] * 999999
    model.demand_response_availability = Constraint(T, rule=demand_response_availability_rule)

    def interruptible_load_availability_rule(model, t):
        return model.P_il[t] <= cap_power * service['il'] * theta['il'].loc[t] * 999999
    model.interruptible_load_availability = Constraint(T, rule=interruptible_load_availability_rule)

    #glpk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'solver', 'glpsol.exe')
    solver = SolverFactory('glpk')
    # solver.options['mipgap'] = 0.005  
    # solver.options['tmlim'] = 10

    solver.solve(model, tee=False)

    schedule_dict = {}
    revenue_dict = {}

    # Extract results for charging, discharging, and SOC
    schedule_dict['arb_charge'] = [model.PC_arb[t].value for t in T]  
    schedule_dict['arb_discharge'] = [model.PD_arb[t].value for t in T]
    schedule_dict['reg_down'] = [model.PC_reg[t].value for t in T] 
    schedule_dict['reg_up'] = [model.PD_reg[t].value for t in T]  
    schedule_dict['pres'] = [model.P_pres[t].value for t in T]  
    schedule_dict['cres'] = [model.P_cres[t].value for t in T]  
    schedule_dict['dr'] = [model.P_dr[t].value for t in T] 
    schedule_dict['il'] = [model.P_il[t].value for t in T] 
    schedule_dict['grid_purchase'] = [model.P_ec[t].value for t in T]  
    schedule_dict['grid_to_storage'] = [model.PC_ec[t].value for t in T]  
    schedule_dict['grid_to_load'] = [model.PL_ec[t].value for t in T] 
    schedule_dict['storage_to_load'] = [model.PD_L[t].value for t in T]  
    schedule_dict['soc'] = [model.SOC[t].value for t in SOC_T]  

    revenue_dict['arb'] =  [model.R_arb[t]() for t in T] 
    revenue_dict['reg'] = [model.R_reg[t]() for t in T ]
    revenue_dict['pres'] = [model.R_pres[t]() for t in T ]
    revenue_dict['cres'] = [model.R_cres[t]() for t in T] 
    revenue_dict['dr'] = [model.R_dr[t]() for t in T ]
    revenue_dict['il'] = [model.R_il[t]() for t in T ]
    revenue_dict['ec'] = [model.R_ec[t]() for t in T]

    # Return the results and final SOC
    return model, model.obj(), schedule_dict, revenue_dict