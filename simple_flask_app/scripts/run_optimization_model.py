import pandas as pd
from scripts.optimization_model import optimize_revenue
from scripts.result_export_v2 import generate_html 
from scripts.econs import econs_calc 


def run_model(packaged_data, result_html_name):
    [data, basis, bess, service] = packaged_data

    price_df = data['prices']
    initial_soc = bess['initial_soc'] * bess['cap_energy']

    model_time_period = int(basis['model_time_period'])    # periods
    total_time_period = len(data['prices'])
    num_slices = int(total_time_period // model_time_period)     # number of time slices to model

    # Lists to store results
    total_revenue = 0
    skipped_p = []

    all_schedule_dict = {}
    all_schedule_dict['arb_charge'] = []
    all_schedule_dict['arb_discharge'] = []
    all_schedule_dict['reg_down'] = []
    all_schedule_dict['reg_up'] = []
    all_schedule_dict['pres'] = []
    all_schedule_dict['cres'] = []
    all_schedule_dict['dr'] = []
    all_schedule_dict['il'] = []
    all_schedule_dict['grid_purchase'] = []
    all_schedule_dict['grid_to_storage'] = []
    all_schedule_dict['grid_to_load'] = []
    all_schedule_dict['storage_to_load'] = []
    all_schedule_dict['soc'] = []

    all_revenue_dict = {}
    all_revenue_dict['Arbitrage'] =  []
    all_revenue_dict['Frequency Regulation'] = []
    all_revenue_dict['Primary Reserve'] = []
    all_revenue_dict['Contingency Reserve'] = []
    all_revenue_dict['Demand Response'] = []
    all_revenue_dict['Interruptible Load'] = []
    all_revenue_dict['Demand-side Energy Savings'] = []

    # num_slices = 3

    first_p = 0
    last_p = num_slices - 1

    # Run the optimization for each time period
    for p in range(num_slices):

        # if p % 50 == 0:
        #     print('Watch: ', p)
        if p == last_p:
            final_soc_target = 1
        else:
            final_soc_target = 0

        periodic_price = price_df[p*model_time_period:(p+1)*model_time_period]
        periodic_price = periodic_price.set_index('period')

        if service['load'] == 1:
            periodic_load = data['load'][p*model_time_period:(p+1)*model_time_period]
            periodic_load = periodic_load.set_index('period')

            # print('periodic load', periodic_load)
        else:
            periodic_load = []

        # try:
        model, revenue, schedule_dict, revenue_dict = optimize_revenue(initial_soc, packaged_data, periodic_price, periodic_load, final_soc_target, cap_settings = [])
        
        # Store the results
        total_revenue += model.obj()
        
        all_revenue_dict['Arbitrage'].extend(revenue_dict['arb'])
        all_revenue_dict['Frequency Regulation'].extend(revenue_dict['reg'])
        all_revenue_dict['Primary Reserve'].extend(revenue_dict['pres'])
        all_revenue_dict['Contingency Reserve'].extend(revenue_dict['cres'])
        all_revenue_dict['Demand-side Energy Savings'].extend(revenue_dict['ec'])
        all_revenue_dict['Demand Response'].extend(revenue_dict['dr'])
        all_revenue_dict['Interruptible Load'].extend(revenue_dict['il'])
        
        all_schedule_dict['arb_charge'].extend(schedule_dict['arb_charge'])
        all_schedule_dict['arb_discharge'].extend(schedule_dict['arb_discharge'])
        all_schedule_dict['reg_up'].extend(schedule_dict['reg_up'])
        all_schedule_dict['reg_down'].extend(schedule_dict['reg_down'])
        all_schedule_dict['pres'].extend(schedule_dict['pres'])
        all_schedule_dict['cres'].extend(schedule_dict['cres'])
        all_schedule_dict['dr'].extend(schedule_dict['dr'])
        all_schedule_dict['il'].extend(schedule_dict['il'])
        all_schedule_dict['grid_purchase'].extend(schedule_dict['grid_purchase'])
        all_schedule_dict['grid_to_storage'].extend(schedule_dict['grid_to_storage'])
        all_schedule_dict['grid_to_load'].extend(schedule_dict['grid_to_load'])
        all_schedule_dict['storage_to_load'].extend(schedule_dict['storage_to_load'])
        all_schedule_dict['soc'].extend(schedule_dict['soc'][:-1])

        # Update the initial SOC for the next day
        final_soc = schedule_dict['soc'][-1]
        initial_soc = final_soc



    # Create a DataFrame for the results
    all_revenue_dict['time'] = price_df.index[:len(all_schedule_dict['arb_charge'])]
    revenue_data = pd.DataFrame(all_revenue_dict)

    all_schedule_dict['time'] = price_df.index[:len(all_schedule_dict['arb_charge'])]
    result_df = pd.DataFrame(all_schedule_dict)
    result_df['net_power'] = result_df['arb_discharge'] - result_df['arb_charge'] - result_df['grid_purchase']
    result_df['soc_percent'] = result_df['soc'] /bess['cap_energy']

    if service['load'] == 1:
        result_df = result_df.set_index(['time'])
        result_df['load'] = data['load'].value[:len(all_schedule_dict['arb_charge'])]/basis['dt']
        result_df = result_df.reset_index()

    price_df.index.names = ['time']
    # bess['revenue'] = total_revenue * basis['annual_time_period']/len(price_df)
    bess['revenue'] = total_revenue * 365/num_slices

    financial_metrics = econs_calc(basis, bess, bess['revenue'])

    if result_html_name:
        generate_html(result_html_name, bess, service, price_df[:num_slices*48], result_df, revenue_data, basis['wacc'], service['load'])

    return bess['revenue'], result_df, revenue_data, financial_metrics