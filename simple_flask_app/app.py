from flask import Flask, render_template, request
import pandas as pd
import webbrowser
import threading


# Import the Pyomo function from the scripts folder
from scripts.data_import import data_import
from scripts.run_optimization_model import run_model
from scripts.result_export_v2 import generate_html 

app = Flask(__name__, template_folder='templates', static_folder='flask/static')
app.secret_key = 'supersecretkey'

other_services = [
    "Frequency Regulation", "Primary Reserve", 
    "Contingency Reserve", "Demand Response (BTM)", "Interruptible Load (BTM)"
]

all_services = ['Grid-side', 'Consumer-side']

all_services_dict = {
                        "Grid-side": 'arb', 
                        "Consumer-side": 'ec', 
                        "Frequency Regulation": 'reg', 
                        "Primary Reserve": 'pres', 
                        "Contingency Reserve": 'cres', 
                        "Demand Response (BTM)": 'dr', 
                        "Interruptible Load (BTM)": 'il'
}

all_price_options = ['Nominal', "Nominal x 150%", 'Nominal x 200%']
all_profile_options = ['Commercial', 'Residential']
all_tariffplan_options = ['Time of use', 'Fixed']

@app.route('/', methods=['GET', 'POST'])

def index():

    if request.method == 'POST':
        # Get the power and energy capacity from the form
        power_capacity = request.form.get('power_capacity')
        energy_capacity = request.form.get('energy_capacity')
        fixed_cost = request.form.get('fixed_cost')
        energy_cost = request.form.get('energy_cost')
        power_cost = request.form.get('power_cost')
        om_cost = request.form.get('om_cost')
        selected_services = request.form.getlist('bess_service')  # Get selected checkboxes
        selected_price_options = request.form.getlist('electricity_tariff')  # Get selected checkboxes
        selected_profile_options = request.form.getlist('load_profile')  # Get selected checkboxes
        selected_tariffplan_options = request.form.getlist('tariff_plan')  # Get selected checkboxes

        # Print the values to the terminal
        # print(f"Selected service: {selected_services}")

        # Select excel file path based on type of load
        for option in selected_profile_options:
            if option == "Commercial":
                excel_name = 'data_commercial'
            # elif option == "Industrial":
            #     excel_name = 'data_industrial'
            elif option == "Residential":
                excel_name = 'data_residential'

        # Load the Excel file from the templates folder
        file_path = 'templates/' + excel_name + '.xlsx'
        data, basis, bess, service, revenue_change = data_import(file_path)

        # print(data['load'])

        bess['cap_power'] = float(power_capacity)/1000
        bess['cap_energy'] = float(energy_capacity) * bess['cap_power']
        bess['fixed_capex'] = float(fixed_cost)
        bess['energy_capex'] = float(energy_cost)
        bess['power_capex'] = float(power_cost)
        bess['fixed_opex'] = float(om_cost)/100 * bess['fixed_capex']
        bess['energy_opex'] = float(om_cost)/100 * bess['energy_capex']
        bess['power_opex'] = float(om_cost)/100 * bess['power_capex']

        # Modify service based on selection
        data['soc_limit']['min'] = 0.1
        
        for key in all_services + other_services:
            option = all_services_dict[key]
            if option in service and key in selected_services:
                service[option] = 1
                data['schedule'][option] = 1
            else: 
                service[option] = 0
        service['reg_symmetric'] = 1

        if service['ec'] == 1:
            service['load'] = 1

        # Modify electricity tariff based on selection
        for option in selected_tariffplan_options:
            if option == "Fixed":
                data['prices']['ec_energy_price'] = 325.7

        for option in selected_price_options:
            if option == "Nominal x 150%":
                data['prices']['arb_energy_price'] *= 1.5
                data['prices']['ec_energy_price'] *= 1.5

            elif option == "Nominal x 200%":
                data['prices']['arb_energy_price'] *= 2
                data['prices']['ec_energy_price'] *= 2



        packaged_data = [data, basis, bess, service] 
        html_file_name = 'results/result'
        html_file_path = html_file_name + ".html"

        annual_revenue, result_df, revenue_df, financial_metrics = run_model(packaged_data, result_html_name = html_file_name)      

        # Read the generated HTML file content
        with open(html_file_path, "r") as f:
            generated_html_content = f.read()

        return render_template('output.html', 
                            power_capacity=power_capacity, 
                            energy_capacity=energy_capacity, 
                            fixed_cost = fixed_cost,
                            energy_cost = energy_cost, 
                            power_cost = power_cost,
                            om_cost = om_cost,
                            all_services = all_services,
                            selected_services = selected_services,
                            all_price_options = all_price_options,
                            selected_price_options = selected_price_options,
                            all_profile_options = all_profile_options,
                            selected_profile_options = selected_profile_options,
                            all_tariffplan_options = all_tariffplan_options,
                            selected_tariffplan_options = selected_tariffplan_options,
                            generated_html=generated_html_content)
    
    # If it's a GET request, render the form without any results
    # selected_services = all_services  # Select all by default

    selected_services = ['Grid-side']
    selected_price_options = ['Nominal']
    selected_profile_options = ['Commercial']
    selected_tariffplan_options = ['Time of use']

    return render_template('output.html', 
                            all_services = all_services,
                            selected_services = selected_services,
                            all_price_options = all_price_options,
                            selected_price_options = selected_price_options,
                            all_profile_options = all_profile_options,
                            selected_profile_options = selected_profile_options,
                            all_tariffplan_options = all_tariffplan_options,
                            selected_tariffplan_options = selected_tariffplan_options,
                           generated_html=None)


def open_browser():
    webbrowser.open('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # threading.Timer(1.25, open_browser).start()
    app.run(debug=True, use_reloader=True) 
