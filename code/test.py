from city import *

GEO_DEFINITIONS = {
    'phi': [{'county': 'Philadelphia', 'state': 'Pennsylvania'}],
    'chi': [{'county': 'Cook', 'state': 'Illinois'}],
    'sf': [{'county': 'San Francisco','state': 'California'}], 
    'sfba': [{'county': 'San Francisco','state': 'California'}, {'county': 'Contra Costa','state': 'California'}, 
            {'county': 'Alameda','state': 'California'}, {'county': 'San Mateo', 'state': 'California'},
            {'county': 'Santa Clara', 'state': 'California'}],
    'eastbay': [{'county': 'Contra Costa','state': 'California'}, {'county': 'Alameda','state': 'California'}],
    'nyc': [{'county': 'King', 'state': 'New York'}, {'county': 'Queens', 'state': 'New York'}, 
            {'county': 'New York', 'state': 'New York'}, {'county': 'Bronx', 'state': 'New York'}]
}

INFRA_TYPES = {
    'bridge': {'bridge':['yes','viaduct']},
    'highway': {'highway': ['motorway','motorway_link','motorway_junctions']},
    'coastline': {'natural':'coastline'},
    'water': {'natural':'water'}
}

# Create City
c_phi = City('Philadelphia',GEO_DEFINITIONS['phi'], '../data/replica_exports/replica-phi_sat_spring_2024-01_14_25-trips_dataset.csv')

# Add Infrastructure
c_phi.load_infrastructure(INFRA_TYPES)

# Split
c_phi.split_infra_pipeline()

# Assign BGs to Zones
c_phi.assign_bg2zones()

# Aand export it
c_phi.export_final_dataset()





# Create City
c_phi = City('Philadelphia',GEO_DEFINITIONS['phi'], '../data/replica_exports/replica-phi_sat_spring_2024-01_14_25-trips_dataset.csv')
# c_sfba = City('SF Bay Area',GEO_DEFINITIONS['sfba'], '../data/replica_exports/replica-sfba_sat_spring_2024-01_14_25-trips_dataset.csv')
# c_nyc = City('New York City',GEO_DEFINITIONS['nyc'], '../data/replica_exports/replica-nyc_sat_spring_2024-01_14_25-trips_dataset.csv')
# c_chi = City('Chicago',GEO_DEFINITIONS['chi'], '../data/replica_exports/replica-chi_sat_spring_2024-01_14_25-trips_dataset.csv')

# Add Infrastructure
c_phi.load_infrastructure(INFRA_TYPES)
# c_sfba.load_infrastructure(INFRA_TYPES)
# c_nyc.load_infrastructure(INFRA_TYPES)
# c_chi.load_infrastructure(INFRA_TYPES)

# Split
c_phi.split_infra_pipeline()

# Assign BGs to Zones
c_phi.assign_bg2zones()