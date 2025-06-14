state_sales_tax_dict =  {
    0.08: [['Alabama', 'AL']],
    0.0: [['Alaska', 'AK'], ['Delaware', 'DE'], ['Florida', 'FL'], ['Montana', 'MT'], ['New Hampshire', 'NH'], ['Oregon', 'OR']],
    0.056: [['Arizona', 'AZ']],
    0.09: [['Arkansas', 'AR']],
    0.095: [['California', 'CA']],
    0.0781: [['Colorado', 'CO']],
    0.0635: [['Connecticut', 'CT']],
    0.06: [['District Of Columbia', 'DC'], ['Iowa', 'IA'], ['Kentucky', 'KY'], ['Maryland', 'MD'], ['Michigan', 'MI'], ['Pennsylvania', 'PA'], ['South Carolina', 'SC'], ['Vermont', 'VT'], ['West Virginia', 'WV']],
    0.07: [['Georgia', 'GA'], ['Indiana', 'IN'], ['Mississippi', 'MS'], ['Rhode Island', 'RI'], ['Tennessee', 'TN']],
    0.04: [['Hawaii', 'HI'], ['Wyoming', 'WY']],
    0.0603: [['Idaho', 'ID']],
    0.0886: [['Illinois', 'IL']],
    0.065: [['Kansas', 'KS'], ['Washington', 'WA']],
    0.0445: [['Louisiana', 'LA']],
    0.055: [['Maine', 'ME'], ['Nebraska', 'NE']],
    0.0625: [['Massachusetts', 'MA'], ['Texas', 'TX']],
    0.06875: [['Minnesota', 'MN']],
    0.04225: [['Missouri', 'MO']],
    0.0685: [['Nevada', 'NV']],
    0.06625: [['New Jersey', 'NJ']],
    0.05125: [['New Mexico', 'NM']],
    0.08375: [['New York', 'NY']],
    0.0475: [['North Carolina', 'NC']],
    0.05: [['North Dakota', 'ND'], ['Wisconsin', 'WI']],
    0.0575: [['Ohio', 'OH']],
    0.0899: [['Oklahoma', 'OK']],
    0.045: [['South Dakota', 'SD']],
    0.0485: [['Utah', 'UT']],
    0.053: [['Virginia', 'VA']]}


def get_state_tax_rate(state):
    state_to_tax_rate = {}
    for tax_rate, states in state_sales_tax_dict.items():
        for state_name, abbr in states:
            state_to_tax_rate[state_name] = tax_rate
            state_to_tax_rate[abbr] = tax_rate
    return state_to_tax_rate.get(state)

# state_sales_tax_dict = {
#     "Alabama": .08, "Alaska": .00, "Arizona": .056, "Arkansas": .09, "California": .095, "Colorado": .0781, 
#     "Connecticut": .0635, "Delaware": .00, "District Of Columbia": .06, "Florida": .00, "Georgia": .07, "Hawaii": .04, 
#     "Idaho": .0603, "Illinois": .0886, "Indiana": .07, "Iowa": .06, "Kansas": .065, "Kentucky": .06, "Louisiana": .0445, 
#     "Maine": .055, "Maryland": .06, "Massachusetts": .0625, "Michigan": .06, "Minnesota": .06875, "Mississippi": .07, 
#     "Missouri": .04225, "Montana": .00, "Nebraska": .055, "Nevada": .0685, "New Hampshire": .00, "New Jersey": .06625, 
#     "New Mexico": .05125, "New York": .08375, "North Carolina": .0475, "North Dakota": .05, "Ohio": .0575, 
#     "Oklahoma": .0899, "Oregon": .00, "Pennsylvania": .06, "Rhode Island": .07, "South Carolina": .06, "South Dakota": .045, 
#     "Tennessee": .07, "Texas": .0625, "Utah": .0485, "Vermont": .06,  "Virginia": .053, "Washington": .065, 
#     "West Virginia": .06, "Wisconsin": .05, "Wyoming": .04, 
# }

# Calculate tax for an order
# tax = ({
#   'from_country': 'US',
#   'from_zip': '90002',
#   'from_state': 'CA',
#   'to_country': 'US',
#   'to_zip': '94111',
#   'to_state': 'CA',
#   'amount': 15,
#   'shipping': 1.5,
# })