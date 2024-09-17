import pandas as pd

def generate_html(filename, bess, service, price_data, result_data, revenue_data, discount_rate, btm_service):
    # Convert data to JSON format
    revenue_data_json = revenue_data.to_json(orient='records', date_format='iso')
    price_data_json = price_data.reset_index().to_json(orient='records', date_format='iso')
    result_data_json = result_data.to_json(orient='records', date_format='iso')

    # Calculate the annual revenue by summing all items in the revenue_data series
    annual_revenue = bess['revenue']

    # Extract dates from result_data and format them as strings
    dates_list = result_data['time'].dt.strftime('%Y-%m-%d').tolist()

    # Create JavaScript array from the dates list
    js_dates_array = ", ".join([f"'{date}'" for date in dates_list])

    # Generate the HTML content with embedded JavaScript
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Financial Calculations with Plotly</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
                color: #333;
            }}
            .menu {{
                overflow: hidden;
                background-color: #333;
                padding: 0 10px;
            }}
            .menu a {{
                float: left;
                display: block;
                color: white;
                text-align: center;
                padding: 14px 16px;
                text-decoration: none;
            }}
            .menu a:hover {{
                background-color: #ddd;
                color: black;
            }}
            .content {{
                display: none;
                padding: 20px;
                background-color: white;
                margin: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            .content.active {{
                display: block;
            }}
            .chart-container {{
                width: 100%;
                height: 500px;
                margin-top: 20px;
            }}
            .input-group {{
                margin: 10px 0;
                display: flex;
                flex-direction: column;
                font-size: 14px;
            }}
            .input-group label {{
                margin-bottom: 5px;
            }}
            .input-group input {{
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }}
            .input-group span {{
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f9f9f9;
                text-align: left;
            }}
            .input-group button {{
                padding: 6px 12px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }}
            .input-group button:hover {{
                background-color: #0056b3;
            }}
            .metrics {{
                margin-top: 20px;
                display: flex;
                flex-wrap: wrap;
            }}
            .metrics div {{
                flex: 1 1 200px;
                padding: 10px;
                margin: 5px;
                background-color: #f9f9f9;
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
            }}
            .input-container {{
                display: flex;
                flex-wrap: wrap;
            }}
            .input-container .input-group {{
                flex: 1 1 calc(50% - 10px);
                box-sizing: border-box;
                margin-bottom: 10px;
            }}
            .input-container .input-group:nth-child(odd) {{
                margin-right: 20px;
            }}
            .container {{
                display: flex;
                align-items: center;
                margin-bottom: 20px;
            }}
            .datepicker {{
                height: 40px;
                margin-right: 10px;
            }}
            .duration-button {{
                height: 40px;
                margin-right: 10px;
                padding: 0 20px;
                cursor: pointer;
            }}
            .duration-button:hover {{
                background-color: #ddd;
            }}

            .duration-button.active {{
                background-color: #0056b3; /* Darker blue for active state */
                color: white;
            }}
    
            .label {{
                margin-right: 20px;
            }}
        </style>
        <script>
            function setInitialStep(input) {{
                const value = input.defaultValue;
                if (input.id === 'discountRate' || input.id === 'revenueChange' || input.id === 'costChange') {{
                    input.step = 1;
                }} else if (value) {{
                    const [integerPart, decimalPart] = value.split('.');
                    if (decimalPart) {{
                        // If there's a decimal part, the step should be 10^(number of integer digits - 1)
                        const step = Math.pow(10, integerPart.length - 1);
                        input.step = step;
                    }} else {{
                        // If there's no decimal part, calculate step based on the length of the integer part
                        const step = Math.pow(10, value.length - 1);
                        input.step = step;
                    }}
                }} else {{
                    input.step = 1; // default step if input is empty
                }}
            }}

            function initializeStepValues() {{
                const inputs = document.querySelectorAll('.input-group input[type="number"]');
                inputs.forEach(input => {{
                    setInitialStep(input);
                }});
            }}

            document.addEventListener('DOMContentLoaded', initializeStepValues);
        </script>
    </head>
    <body>
        <div class="menu">
            <a href="#bessOptimizationResult" onclick="showSection('bessOptimizationResult'); return false;">Optimization Result for BESS Operation</a>
            <a href="#economicAnalysis" onclick="showSection('economicAnalysis'); return false;">Economic Analysis</a>
        </div>

        <div id="bessOptimizationResult" class="content">
            <div class="container" style="display: none;">
                <h4 class="label">Select a Start Date</h4>
                <input type="date" id="startDatePicker" class="datepicker">
                <button class="duration-button" data-duration="1day">1 Day</button>
                <button class="duration-button" data-duration="1week">1 Week</button>
                <button class="duration-button" data-duration="1month">1 Month</button>
                <button class="duration-button" data-duration="allafter">All After</button>
                <button id="clearAllButton" class="duration-button" style="background-color: #007bff; color: white; width: 100px;">Clear All</button>
            </div>
            <h2 id="endDateText" style="display: none;">End Date: </h2>
            
            <div class="chart-container" id="prices_chart"></div>
            <div class="chart-container" id="revenue_breakdown_chart" style="display: none;"></div>
            <div class="chart-container" id="soc_chart"></div>
            <div class="chart-container" id="charge_discharge_chart" style="display: none;"></div>
            <div class="chart-container" id="operation_schedule_chart"></div>
            <div class="chart-container" id="btm_services_chart" style="display: none;"></div>
        </div>

        <div id="economicAnalysis" class="content active">
            <h2 style="display: none;">Capacity Settings</h2>
            <div class="input-container" style="display: none;">
                <div class="input-group">
                    <label>Power capacity (MW):</label>
                    <span id="cap_power">{bess['cap_power']}</span>
                </div>
                <div class="input-group">
                    <label>Energy capacity (MWh):</label>
                    <span id="cap_energy">{bess['cap_energy']}</span>
                </div>
            </div>

            <h2 style="display: none;">Costing</h2>
            <div class="input-container" style="display: none;">
                <div class="input-group">
                    <label for="fixed_capex">Fixed capital cost ($):</label>
                    <input type="number" id="fixed_capex" name="fixed_capex" value="{bess['fixed_capex']:.2f}" min="0" oninput="updateInitialCost()">
                </div>
                <div class="input-group">
                    <label for="fixedOpex">Fixed O&M cost ($):</label>
                    <input type="number" id="fixedOpex" name="fixedOpex" value="{bess['fixed_opex']:.2f}" min="0" oninput="updateAnnualCost()">
                </div>
                <div class="input-group">
                    <label for="energy_capex">Energy-related capital cost ($/kWh):</label>
                    <input type="number" id="energy_capex" name="energy_capex" value="{bess['energy_capex']:.2f}" min="0" oninput="updateInitialCost()">
                </div>
                <div class="input-group">
                    <label for="energyOpex">Energy-related O&M cost ($/kWh):</label>
                    <input type="number" id="energyOpex" name="energyOpex" value="{bess['energy_opex']:.2f}" min="0" oninput="updateAnnualCost()">
                </div>
                <div class="input-group">
                    <label for="power_capex">Power-related capital cost ($/kW):</label>
                    <input type="number" id="power_capex" name="power_capex" value="{bess['power_capex']:.2f}" min="0" oninput="updateInitialCost()">
                </div>
                <div class="input-group">
                    <label for="powerOpex">Power-related O&M cost ($/kW):</label>
                    <input type="number" id="powerOpex" name="powerOpex" value="{bess['power_opex']:.2f}" min="0" oninput="updateAnnualCost()">
                </div>
            </div>

            <h2>Financial Analysis</h2>
            <div class="input-container">
                <div class="input-group">
                    <label>Initial cost ($):</label>
                    <span id="initialCost">0.00</span>
                </div>
                <div class="input-group">
                    <label for="discountRate">Discount rate (%):</label>
                    <input type="number" id="discountRate" name="discountRate" value="{discount_rate * 100:.2f}" step="1" min="0" max="100" oninput="updateChart()">
                </div>
                <div class="input-group">
                    <label>Annual cost ($):</label>
                    <span id="annualCost">0.00</span>
                </div>
                <div class="input-group">
                    <label for="costChange">Annual cost change (%):</label>
                    <input type="number" id="costChange" name="costChange" value="0" step="1" min="-100" max="100" oninput="updateChart()">
                </div>
                <div class="input-group">
                    <label>Annual revenue ($):</label>
                    <span id="annualRevenue">{annual_revenue:,.2f}</span>
                </div>
                <div class="input-group">
                    <label for="revenueChange">Annual revenue change (%):</label>
                    <input type="number" id="revenueChange" name="revenueChange" value="0" step="1" min="-100" max="100" oninput="updateChart()">
                </div>

                <div class="input-group">
                    <button onclick="resetEconomicAnalysisDefaults()">Reset to Default Values</button>
                </div>
            </div>

            <div class="metrics">
                <div>NPV: $<span id="npvValue"></span></div>
                <div>BCR: <span id="bcrValue"></span></div>
                <div>ROI: <span id="roiValue"></span>%</div>
                <div>IRR: <span id="irrValue"></span>%</div>
                <div>Payback Period: <span id="paybackPeriod"></span> years</div>
            </div>

            <div class="chart-container" id="netCashFlowChart"></div>
            <div class="chart-container" id="cumulativeCashFlowChart"></div>
        </div>

        <script>
            // List of allowed dates
            const allowedDates = [{js_dates_array}];

            // Function to check if a date is allowed
            function isDateAllowed(date) {{
                return allowedDates.includes(date);
            }}

            // Function to add days to a date
            function addDays(date, days) {{
                const result = new Date(date);
                result.setDate(result.getDate() + days);
                return result;
            }}

            // Function to add weeks to a date
            function addWeeks(date, weeks) {{
                return addDays(date, weeks * 7);
            }}

            // Function to add months to a date
            function addMonths(date, months) {{
                const result = new Date(date);
                result.setMonth(result.getMonth() + months);
                return result;
            }}

            // Function to get the nearest allowed date within the allowed range
            function getNearestAllowedDate(date) {{
                for (let i = 0; i < allowedDates.length; i++) {{
                    if (new Date(allowedDates[i]) >= date) {{
                        return new Date(allowedDates[i]);
                    }}
                }}
                return new Date(allowedDates[allowedDates.length - 1]);
            }}

            // Function to filter data based on selected date range
            function filterDataByDate(startDate, endDate, data) {{
                const start = new Date(startDate + 'T00:00:00');
                const end = new Date(endDate + 'T23:59:59');
                end.setDate(end.getDate() - 1); // Subtract one day from the end date
                return data.filter(d => new Date(d.time) >= start && new Date(d.time) <= end);
            }}

            // Event listener to handle date and duration selection
            document.querySelectorAll('.duration-button').forEach(button => {{
                button.addEventListener('click', function() {{
                    const startDateInput = document.getElementById('startDatePicker');
                    if (startDateInput.value) {{
                        const startDate = new Date(startDateInput.value);
                        if (!isDateAllowed(startDateInput.value)) {{
                            alert('Selected date is not allowed. Please choose a valid date.');
                            startDateInput.value = '';
                            document.getElementById('endDateText').innerText = 'End Date: ';
                        }} else {{
                            let endDate;
                            switch (this.dataset.duration) {{
                                case '1day':
                                    endDate = addDays(startDate, 1);
                                    break;
                                case '1week':
                                    endDate = addWeeks(startDate, 1);
                                    break;
                                case '1month':
                                    endDate = addMonths(startDate, 1);
                                    break;
                                case 'allafter':
                                    endDate = new Date(allowedDates[allowedDates.length - 1]);
                                    break;
                            }}
                            endDate = getNearestAllowedDate(endDate);
                            document.getElementById('endDateText').innerText = 'End Date: ' + endDate.toISOString().split('T')[0];

                            // Filter data based on selected date range
                            const filteredPriceData = filterDataByDate(startDateInput.value, endDate.toISOString().split('T')[0], priceData);
                            const filteredResultData = filterDataByDate(startDateInput.value, endDate.toISOString().split('T')[0], resultData);
                            const filteredRevenueData = filterDataByDate(startDateInput.value, endDate.toISOString().split('T')[0], revenueData);

                            // Update charts with filtered data
                            renderCharts(filteredPriceData, filteredResultData);
                            updateRevenueBreakdownChart(filteredRevenueData);
                        }}
                    }}
                }});
            }});

            // Clear All Button Event Listener
            document.getElementById('clearAllButton').addEventListener('click', function() {{
                document.getElementById('startDatePicker').value = '';
                document.getElementById('endDateText').innerText = 'End Date: ';
                renderCharts(priceData, resultData);
                updateRevenueBreakdownChart(revenueData);
            }});

            // Set min and max date for the start date picker
            document.getElementById('startDatePicker').setAttribute('min', allowedDates[0]);
            document.getElementById('startDatePicker').setAttribute('max', allowedDates[allowedDates.length - 1]);

            // Set initial date to the earliest date in the list
            document.getElementById('startDatePicker').value = allowedDates[0];

            var resultData = {result_data_json};
            var priceData = {price_data_json};
            var revenueData = {revenue_data_json};

            $(document).ready(function() {{
                renderCharts(priceData, resultData);
                updateRevenueBreakdownChart(revenueData);
                updateInitialCost();
                updateAnnualCost();
                updateChart();
            }});

            function updateRevenueBreakdownChart(revenueData) {{
                var revenueSums = {{
                    "Arbitrage": 0,
                    "Frequency Regulation": 0,
                    "Primary Reserve": 0,
                    "Contingency Reserve": 0,
                    "Demand Response": 0,
                    "Interruptible Load": 0,
                    "Demand-side Energy Savings": 0
                }};

                revenueData.forEach(function(d) {{
                    revenueSums["Arbitrage"] += d["Arbitrage"];
                    revenueSums["Frequency Regulation"] += d["Frequency Regulation"];
                    revenueSums["Primary Reserve"] += d["Primary Reserve"];
                    revenueSums["Contingency Reserve"] += d["Contingency Reserve"];
                    revenueSums["Demand Response"] += d["Demand Response"];
                    revenueSums["Interruptible Load"] += d["Interruptible Load"];
                    revenueSums["Demand-side Energy Savings"] += d["Demand-side Energy Savings"];
                }});

                Plotly.newPlot('revenue_breakdown_chart', [
                    {{
                        x: Object.values(revenueSums),
                        y: Object.keys(revenueSums),
                        type: 'bar',
                        orientation: 'h',
                        marker: {{
                            color: '#ff7f0e'
                        }}
                    }}
                ], {{
                    title: 'Breakdown of Revenues',
                    xaxis: {{title: 'Revenue ($)'}},
                    yaxis: {{title: 'Revenue Sources', automargin: true}},
                    margin: {{ t: 50, l: 200, r: 0, b: 50 }},
                    height: 450

                }}, 
                {{responsive: true}});
            }}

            function updateInitialCost() {{
                let fixed_capex = parseFloat(document.getElementById('fixed_capex').value);
                let energy_capex = parseFloat(document.getElementById('energy_capex').value) * 1000;
                let power_capex = parseFloat(document.getElementById('power_capex').value) * 1000;
                let cap_energy = parseFloat(document.getElementById('cap_energy').innerText);
                let cap_power = parseFloat(document.getElementById('cap_power').innerText);
                let initialCost = fixed_capex + (energy_capex * cap_energy) + (power_capex * cap_power);
                document.getElementById('initialCost').innerText = formatCurrency(initialCost);
                updateAnnualCost();
            }}

            function updateAnnualCost() {{
                let fixedOpex = parseFloat(document.getElementById('fixedOpex').value);
                let energyOpex = parseFloat(document.getElementById('energyOpex').value) * 1000;
                let powerOpex = parseFloat(document.getElementById('powerOpex').value) * 1000;
                let cap_energy = parseFloat(document.getElementById('cap_energy').innerText);
                let cap_power = parseFloat(document.getElementById('cap_power').innerText);
                let annualCost = fixedOpex + (energyOpex * cap_energy) + (powerOpex * cap_power);
                document.getElementById('annualCost').innerText = formatCurrency(annualCost);
                updateChart();
            }}

            function formatCurrency(value) {{
                return value.toLocaleString(undefined, {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
            }}

            function calculatePaybackPeriod(cumulativeDiscountedCashFlow) {{
                for (let i = 0; i < cumulativeDiscountedCashFlow.length; i++) {{
                    if (cumulativeDiscountedCashFlow[i] >= 0) {{
                        return i;
                    }}
                }}
                return 'N/A';
            }}

            function calculateIRR(values) {{
                const guess = 0.1;
                const tol = 1e-6;
                const maxIter = 100;
                let rate = guess;
                for (let i = 0; i < maxIter; i++) {{
                    let npv = values.reduce((acc, val, j) => acc + val / Math.pow(1 + rate, j), 0);
                    let npvPrime = values.reduce((acc, val, j) => acc - (j * val) / Math.pow(1 + rate, j + 1), 0);
                    let newRate = rate - npv / npvPrime;
                    if (Math.abs(newRate - rate) < tol) return newRate;
                    rate = newRate;
                }}
                return rate;
            }}

            function calculateFinancialMetrics(discountRate, initialCost, annualCost, annualRevenue, revenueChange, costChange) {{
                let periods = Array.from({{ length: {bess['calendar_life']} + 1 }}, (_, i) => i);
                let cashInflows = [0].concat(Array({bess['calendar_life']}).fill(annualRevenue).map((rev, i) => rev * Math.pow(1 + revenueChange / 100, i)));
                let cashOutflows = [initialCost].concat(Array({bess['calendar_life']}).fill(annualCost).map((cost, i) => cost * Math.pow(1 + costChange / 100, i)));

                let netCashFlow = cashInflows.map((inflow, i) => inflow - cashOutflows[i]);
                let discountedNetCashFlow = netCashFlow.map((flow, i) => flow / Math.pow(1 + discountRate, periods[i]));
                let cumulativeNetCashFlow = netCashFlow.reduce((acc, val, i) => [...acc, (acc[i - 1] || 0) + val], []);
                let cumulativeDiscountedCashFlow = discountedNetCashFlow.reduce((acc, val, i) => [...acc, (acc[i - 1] || 0) + val], []);

                let totalPvInflows = cashInflows.reduce((acc, val, i) => acc + val / Math.pow(1 + discountRate, i), 0);
                let totalPvOutflows = cashOutflows.reduce((acc, val, i) => acc + val / Math.pow(1 + discountRate, i), 0);

                let npv = cumulativeDiscountedCashFlow[cumulativeDiscountedCashFlow.length - 1];
                let bcr = totalPvInflows / totalPvOutflows;
                let roi = ((totalPvInflows - totalPvOutflows) / totalPvOutflows) * 100;
                let irr = calculateIRR(netCashFlow) * 100;
                let paybackPeriod = calculatePaybackPeriod(cumulativeDiscountedCashFlow);

                return {{
                    periods,
                    cashInflows,
                    cashOutflows,
                    netCashFlow,
                    cumulativeNetCashFlow,
                    cumulativeDiscountedCashFlow,
                    npv,
                    bcr,
                    roi,
                    irr,
                    paybackPeriod
                }};
            }}

            function updateChart() {{
                let discountRate = parseFloat(document.getElementById('discountRate').value) / 100;
                let initialCost = parseFloat(document.getElementById('initialCost').innerText.replace(/,/g, ''));
                let annualCost = parseFloat(document.getElementById('annualCost').innerText.replace(/,/g, ''));
                let annualRevenue = parseFloat(document.getElementById('annualRevenue').innerText.replace(/,/g, ''));
                let revenueChange = parseFloat(document.getElementById('revenueChange').value);
                let costChange = parseFloat(document.getElementById('costChange').value);

                let metrics = calculateFinancialMetrics(discountRate, initialCost, annualCost, annualRevenue, revenueChange, costChange);

                let cashInflowsTrace = {{
                    x: metrics.periods,
                    y: metrics.cashInflows,
                    name: 'Annual Revenue',
                    type: 'bar',
                    marker: {{
                        color: '#1f77b4'
                    }}
                }};

                let cashOutflowsTrace = {{
                    x: metrics.periods,
                    y: metrics.cashOutflows,
                    name: 'Annual Cost',
                    type: 'bar',
                    marker: {{
                        color: '#ff7f0e'
                    }}
                }};

                let netCashFlowTrace = {{
                    x: metrics.periods,
                    y: metrics.netCashFlow,
                    name: 'Net Cash Flow',
                    type: 'scatter',
                    mode: 'lines+markers',
                    marker: {{
                        color: '#2ca02c'
                    }},
                    line: {{
                        color: '#2ca02c'
                    }}
                }};

                let cumulativeNetCashFlowTrace = {{
                    x: metrics.periods,
                    y: metrics.cumulativeNetCashFlow,
                    name: 'Undiscounted Cumulative Cash Flow',
                    type: 'scatter',
                    mode: 'lines+markers',
                    marker: {{
                        color: '#d62728'
                    }},
                    line: {{
                        color: '#d62728'
                    }}
                }};

                let cumulativeDiscountedCashFlowTrace = {{
                    x: metrics.periods,
                    y: metrics.cumulativeDiscountedCashFlow,
                    name: 'Discounted Cumulative Cash Flow',
                    type: 'scatter',
                    mode: 'lines+markers',
                    marker: {{
                        color: '#9467bd'
                    }},
                    line: {{
                        color: '#9467bd'
                    }}
                }};

                let netCashFlowData = [cashInflowsTrace, cashOutflowsTrace, netCashFlowTrace];
                let cumulativeCashFlowData = [cumulativeNetCashFlowTrace, cumulativeDiscountedCashFlowTrace];

                let netCashFlowLayout = {{
                    title: 'Net Cash Flow with Annual Costs and Revenues',
                    xaxis: {{ title: 'Period' }},
                    yaxis: {{ title: 'Amount ($)' }},
                    barmode: 'group',
                    legend: {{ orientation: "h", y: 1.1 }}
                }};

                let cumulativeCashFlowLayout = {{
                    title: 'Cumulative Cash Flows',
                    xaxis: {{ title: 'Period' }},
                    yaxis: {{ title: 'Amount ($)' }},
                    legend: {{ orientation: "h", y: 1.1 }}
                }};

                Plotly.newPlot('netCashFlowChart', netCashFlowData, netCashFlowLayout, {{responsive: true}});
                Plotly.newPlot('cumulativeCashFlowChart', cumulativeCashFlowData, cumulativeCashFlowLayout, {{responsive: true}});

                document.getElementById('npvValue').innerText = formatCurrency(metrics.npv);
                document.getElementById('bcrValue').innerText = metrics.bcr.toFixed(2);
                document.getElementById('roiValue').innerText = metrics.roi.toFixed(2);
                document.getElementById('irrValue').innerText = metrics.irr.toFixed(2);
                document.getElementById('paybackPeriod').innerText = metrics.paybackPeriod;
            }}

            function resetEconomicAnalysisDefaults() {{
                document.getElementById('fixed_capex').value = '{bess['fixed_capex']:.2f}';
                document.getElementById('energy_capex').value = '{bess['energy_capex']:.2f}';
                document.getElementById('power_capex').value = '{bess['power_capex']:.2f}';
                document.getElementById('fixedOpex').value = '{bess['fixed_opex']:.2f}';
                document.getElementById('energyOpex').value = '{bess['energy_opex']:.2f}';
                document.getElementById('powerOpex').value = '{bess['power_opex']:.2f}';
                document.getElementById('discountRate').value = '{discount_rate * 100:.2f}';
                document.getElementById('revenueChange').value = 0;
                document.getElementById('costChange').value = 0;
                updateInitialCost();
                updateAnnualCost();
                updateChart();
            }}

            function showSection(sectionId) {{
                var sections = document.querySelectorAll('.content');
                sections.forEach(function(section) {{
                    section.classList.remove('active');
                }});
                document.getElementById(sectionId).classList.add('active');
                window.dispatchEvent(new Event('resize')); // Trigger resize to adjust Plotly charts
            }}

            function renderCharts(priceData, resultData) {{
                // Prices Chart
                const plotData = [
                    {{
                        x: priceData.map(item => item.time),
                        y: priceData.map(item => item.arb_energy_price),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Energy (Wholesale)',
                        line: {{color: '#1f77b4'}}
                    }},
                ];

                /*
                if ({service['reg_symmetric']} != 1) {{
                    plotData.push(
                    {{
                        x: priceData.map(item => item.time),
                        y: priceData.map(item => item.reg_capacity_price),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Regulation Up',
                        line: {{color: '#CC5500'}}
                    }},
                    {{
                        x: priceData.map(item => item.time),
                        y: priceData.map(item => item.reg_down_capacity_price),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Regulation Down',
                        line: {{color: '#ff7f0e'}}
                    }}
                    );
                }};

                if ({service['reg_symmetric']} == 1) {{
                    plotData.push(
                    {{
                        x: priceData.map(item => item.time),
                        y: priceData.map(item => item.reg_capacity_price),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Regulation',
                        line: {{color: '#CC5500'}}
                    }}
                    );
                }};

                plotData.push(
                    {{
                        x: priceData.map(item => item.time),
                        y: priceData.map(item => item.pres_capacity_price),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Primary Reserve',
                        line: {{color: '#006400'}}
                    }},
                    {{
                        x: priceData.map(item => item.time),
                        y: priceData.map(item => item.cres_capacity_price),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Contingency Reserve',
                        line: {{color: '#808000'}}
                    }},
                    {{
                        x: priceData.map(item => item.time),
                        y: priceData.map(item => item.dr_capacity_price),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Demand Response',
                        line: {{color: '#4B0082'}}
                    }},
                    {{
                        x: priceData.map(item => item.time),
                        y: priceData.map(item => item.il_capacity_price),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Interruptible Load',
                        line: {{color: '#e377c2'}}
                    }},
                    {{
                        x: priceData.map(item => item.time),
                        y: priceData.map(item => item.ec_energy_price),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Consumer-side Energy',
                        line: {{color: '#7f7f7f'}} 
                    }}, 
                )
                */
                
                plotData.push(
                    {{
                        x: priceData.map(item => item.time),
                        y: priceData.map(item => item.ec_energy_price),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Consumer-side Energy',
                        line: {{color: '#7f7f7f'}} 
                    }}, 
                )

                Plotly.newPlot('prices_chart', plotData, {{
                    title: 'Energy Prices Over Time',
                    xaxis: {{title: 'Time'}},
                    yaxis: {{title: 'Price ($/MWh)'}},
                    legend: {{ orientation: "h", y: 1.1 }}
                }}, {{responsive: true}});


                // Charge Discharge Chart
                Plotly.newPlot('charge_discharge_chart', [
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.arb_discharge),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Arbitrage Discharge',
                        line: {{color: '#1f77b4'}}
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => -item.arb_charge),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Arbitrage Charge',
                        line: {{color: '#17becf'}}
                    }},

                    /*
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.reg_up),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Regulation Up',
                        line: {{color: '#CC5500'}}
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => -item.reg_down),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Regulation Down',
                        line: {{color: '#ff7f0e'}}
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.pres),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Primary Reserve',
                        line: {{color: '#006400'}}
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.cres),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Contingency Reserve',
                        line: {{color: '#808000'}}
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.dr),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Demand Response',
                        line: {{color: '#4B0082'}}
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.il),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Interruptible Load',
                        line: {{color: '#e377c2'}}
                    }},
                    */
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.storage_to_load),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Storage to Load',
                        line: {{color: '#7f7f7f'}}
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => -item.grid_to_storage),
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Grid to Storage',
                        line: {{color: '#654321'}}
                    }},
                ], {{
                    title: 'Operation Schedule',
                    xaxis: {{title: 'Time'}},
                    yaxis: {{title: 'Power (MW)'}},
                    legend: {{ orientation: "h", y: 1.1 }}
                }}, 
                {{responsive: true}});

                // SOC Chart
                Plotly.newPlot('soc_chart', [
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.soc_percent * 100),
                        type: 'scatter',
                        mode: 'lines',
                        fill: 'tozeroy',
                        name: 'State of Charge',
                        line: {{color: '#1f77b4'}}
                    }}
                ], {{
                    title: 'State of Charge Over Time',
                    xaxis: {{title: 'Time'}},
                    yaxis: {{title: 'SOC (%)'}},
                    legend: {{ orientation: "h", y: 1.2 }}
                }}, 
                {{responsive: true}});

                // Operation Schedule Stacked Bar Chart
                Plotly.newPlot('operation_schedule_chart', [
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.arb_discharge),
                        name: 'Storage discharge (grid-side)',
                        type: 'bar',
                        marker: {{color: '#1f77b4'}}
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => -item.arb_charge),
                        name: 'Storage charge (grid-side)',
                        type: 'bar',
                        marker: {{color: '#17becf'}},
                        offsetgroup: 'negative'
                    }},

                    /*
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.reg_up),
                        name: 'Regulation Up',
                        type: 'bar',
                        marker: {{color: '#CC5500'}}
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => -item.reg_down),
                        name: 'Regulation Down',
                        type: 'bar',
                        marker: {{color: '#ff7f0e'}},
                        offsetgroup: 'negative'
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.pres),
                        name: 'Primary Reserve',
                        type: 'bar',
                        marker: {{color: '#006400'}}
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.cres),
                        name: 'Contingency Reserve',
                        type: 'bar',
                        marker: {{color: '#808000'}}
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.dr),
                        name: 'Demand Response',
                        type: 'bar',
                        marker: {{color: '#4B0082'}}
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.il),
                        name: 'Interruptible Load',
                        type: 'bar',
                        marker: {{color: '#e377c2'}}
                    }},
                    */

                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => item.storage_to_load),
                        name: 'Storage discharge (consumer-side)',
                        type: 'bar',
                        marker: {{color: '#7f7f7f'}}
                    }},
                    {{
                        x: resultData.map(item => item.time),
                        y: resultData.map(item => -item.grid_to_storage),
                        name: 'Storage charge (consumer-side)',
                        type: 'bar',
                        marker: {{color: '#bcbd22'}},
                        offsetgroup: 'negative'
                    }}
                ], {{
                    title: 'Operation Schedule',
                    barmode: 'relative',
                    xaxis: {{title: 'Time'}},
                    yaxis: {{title: 'Power (MW)'}},
                    legend: {{ orientation: "h", y: 1.1 }}
                }}, 
                {{responsive: true}});

                // BTM Services Chart
                if ({btm_service}) {{
                    document.getElementById('btm_services_chart').style.display = 'block';
                    Plotly.newPlot('btm_services_chart', [
                        {{
                            x: resultData.map(item => item.time),
                            y: resultData.map(item => item.grid_purchase),
                            type: 'scatter',
                            mode: 'lines',
                            name: 'Grid Purchase',
                            line: {{color: '#1f77b4'}}
                        }},
                        {{
                            x: resultData.map(item => item.time),
                            y: resultData.map(item => item.load),
                            type: 'scatter',
                            mode: 'lines',
                            name: 'Load',
                            line: {{color: '#ff7f0e'}}
                        }},
                        {{
                            x: resultData.map(item => item.time),
                            y: resultData.map(item => item.grid_to_load),
                            name: 'Grid to Load',
                            type: 'bar',
                            marker: {{color: '#d62728'}}
                        }},
                        {{
                            x: resultData.map(item => item.time),
                            y: resultData.map(item => item.storage_to_load),
                            name: 'Storage to Load',
                            type: 'bar',
                            marker: {{color: '#9467bd'}}
                        }},
                        {{
                            x: resultData.map(item => item.time),
                            y: resultData.map(item => item.grid_to_storage),
                            name: 'Grid to Storage',
                            type: 'bar',
                            marker: {{color: '#2ca02c'}}
                        }},

                    ], {{
                        title: 'BTM Services',
                        barmode: 'stack',
                        xaxis: {{title: 'Time'}},
                        yaxis: {{title: 'Power (MW)'}},
                        legend: {{ orientation: "h", y: 1.1 }}
                    }}, 
                    {{responsive: true}});
                }}
            }}

            
        </script>
    </body>
    </html>
    """

    # Write the HTML content to a file
    with open(filename + ".html", 'w') as file:
        file.write(html_content)

    print("HTML file generated:" + filename + ".html")
