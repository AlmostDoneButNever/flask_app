import numpy_financial as npf
import pandas as pd

def econs_calc(basis, bess, annual_revenue):

    discount_rate = basis['wacc']
    initial_cost = bess['fixed_capex'] + bess['energy_capex'] * bess['cap_energy'] * 1000 \
                                        + bess['power_capex'] * bess['cap_power'] * 1000
    annual_cost = bess['fixed_opex'] + bess['energy_opex'] * bess['cap_energy'] * 1000 \
                                        + bess['power_opex'] * bess['cap_power'] * 1000
                                        
    lifespan = bess['calendar_life']

    # Set initial discount rate and annual cost
    data = {
        'Period': list(range(0, lifespan + 1)),
        'Cash Inflows': [0] + [annual_revenue]*lifespan,
        'Cash Outflows': [initial_cost] + [annual_cost]*lifespan,
    }

    # Create DataFrame
    cash_flows = pd.DataFrame(data)


    # Calculate Present Value of Cash Inflows and Outflows
    cash_flows['PV Cash Inflows'] = cash_flows['Cash Inflows'] / (1 + discount_rate) ** cash_flows['Period']
    cash_flows['PV Cash Outflows'] = cash_flows['Cash Outflows'] / (1 + discount_rate) ** cash_flows['Period']

    # Calculate Net Cash Flow
    cash_flows['Net Cash Flow'] = cash_flows['Cash Inflows'] - cash_flows['Cash Outflows']

    # Calculate Discounted Cash Flow (DCF)
    cash_flows['Discounted Cash Flow'] = cash_flows['Net Cash Flow'] / (1 + discount_rate) ** cash_flows['Period']

    # Calculate Cumulative Discounted Cash Flow
    cash_flows['Cumulative Discounted Cash Flow'] = cash_flows['Discounted Cash Flow'].cumsum()

    # Calculate NPV
    NPV = cash_flows['Discounted Cash Flow'].sum()

    # Calculate ROI considering the discount rate
    total_pv_inflows = cash_flows['PV Cash Inflows'].sum()
    total_pv_outflows = cash_flows['PV Cash Outflows'].sum()
    ROI = (total_pv_inflows - total_pv_outflows) / total_pv_outflows

    # Calculate BCR
    BCR = total_pv_inflows / total_pv_outflows

    # Calculate IRR
    cash_flows_list = cash_flows['Net Cash Flow'].tolist()
    IRR = npf.irr(cash_flows_list)


    # Calculate Payback Period
    payback_period = None
    for i in range(1, len(cash_flows)):
        if cash_flows.loc[i, 'Cumulative Discounted Cash Flow'] >= 0:
            payback_period = cash_flows.loc[i, 'Period']
            break

    return [NPV, ROI, IRR, BCR, payback_period]