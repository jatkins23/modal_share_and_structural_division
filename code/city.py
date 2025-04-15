COLS_DICT = {
    'origin_bgrp_fips_2020': 'O_bg_fips',
    'destination_bgrp_fips_2020': 'D_bg_fips',
    'primary_mode': 'primary_mode', 
    'origin_bgrp_lng_2020': 'O_bg_lng',
    'origin_bgrp_lat_2020': 'O_bg_lat',
    'destination_bgrp_lat_2020': 'D_bg_lat',
    'destination_bgrp_lng_2020': 'D_bg_lng',
    'trip_distance_meters': 'dist_m'
}

import pandas as pd
import osmnx as ox
import geopandas as gpd
from keplergl import KeplerGl


# BASIC_COLS = ['origin_bgrp_fips_2020', 'destination_bgrp_fips_2020', 'trip_distance_meters', 'primary_mode', 'origin_bgrp_lng_2020', 
#               'origin_bgrp_lat_2020','destination_bgrp_lat_2020','destination_bgrp_lng_2020']
INFRA_TYPES = {
    'bridge': {'bridge':['yes','viaduct']},
    'highway': {'highway': ['motorway','motorway_link','motorway_junctions']},
    'coastline': {'natural':'coastline'},
    'water': {'natural':'water'}
}

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

class City:
    def __init__(self, name: str, geo_definition: list[dict],  file_path: str = None, proj: str = 'EPSG:3857'):
        self.name = name
        self.geo_definition = geo_definition
        self.geo_bounds = self._get_geo_bounds(geo_definition)
        self.proj = proj
        self.trip_data = self._read_trip_data(file_path) if file_path is not None else None
        
        self.infra_data = {}
        self.G = None
        self.Gp = None
        self.Gps = None

        self.blockgroup_centroids = self.get_blockgroups(self.trip_data)
        self.zones = None

    def __repr__(self):
        trips_len = 0 if self.trip_data is None else self.trip_data.shape[0]
        bgs_len = 0 if self.blockgroup_centroids is None else self.blockgroup_centroids.shape[0]
        infra_len = 0 if self.infra_data == {} else pd.concat(self.infra_data, axis=0).shape[0]
        graph_len = 0
        zones_len = 0 if self.zones is None else self.zones.shape[0]
        graph_nodes_len = 0 if self.Gps is None else len(self.Gps.nodes)
        graph_edges_len = 0 if self.Gps is None else len(self.Gps.edges)
        
        return (
            f'{self.name}\n'
            f'\tTrips: {trips_len}\n'
            f'\tBGs  : {bgs_len}\n'
            f'\tInfra: {infra_len}\n'
            f'\tZones: {zones_len}\n'
            f'\tGraph: {graph_nodes_len} nodes, {graph_edges_len} edges\n'
        )

    # Geo-bounds
    def _get_geo_bounds(self, geo_definition: list[dict]) -> gpd.GeoDataFrame:
        return ox.geocoder.geocode_to_gdf(geo_definition).dissolve()

    # Load the trip data from a replica file-path
    def _read_trip_data(self, file_path: str) -> pd.DataFrame:
        """_summary_

        Args:
            file_path (_type_): _description_
        """
        try:
            df = pd.read_csv(file_path).set_index('activity_id')
            return df[list(COLS_DICT.keys())].rename(columns=COLS_DICT)
        except Exception as e:
            print(f'{e}')
    
    # Load all infrastructure
    def _load_infra_type(self, type: dict, name: str) -> gpd.GeoDataFrame:
        try:
            feats =  ox.features_from_place(self.geo_definition, tags=type)
            return feats
        except Exception as e:
            print(f'Warning! {name}: {e}')
            return None

    def load_infrastructure(self, types: dict, append: bool = True) -> None:
        for i in types.keys():
            self.infra_data[i] = self._load_infra_type(types[i], i)

    def load_road_network(self, type: str = 'walk', simplify: bool = True) -> None:
        try:
            self.G = ox.graph.graph_from_place(self.geo_definition, network_type=type, simplify=True, retain_all=False)
            self.Gp = ox.projection.project_graph(self.G, to_crs=self.proj)
            self.Gps = ox.simplification.consolidate_intersections(self.Gp)
        except Exception as e:
            print(f'{e}')


    # Split infrastructure pipeline
    def split_infra_pipeline(self, buffer_width: int = 10) -> None:
        """_summary_

        Args:
            buffer_width (int, optional): _description_. Defaults to 10.
        """
        # Collapse all the infrastructure together
        temp = pd.concat(self.infra_data, axis=0)

        # PROJECT to meter-coordinate system 
        # Create 10m BUFFER
        temp['buffer'] = temp.to_crs(self.proj).buffer(10)
        temp = temp.set_geometry('buffer')
        # DISSOLVE into a singular geospatial object
        temp = temp.dissolve()
        # DIFFERENCE between extents
        # MULTIPART_TO_SINGLEPARTS (explode)
        temp2 = self.geo_bounds.to_crs(self.proj).difference(temp).explode()
        # CLIP by water and other boundaries (necessary?)
        self.zones = temp2
    
    def get_blockgroups(self, trip_data) -> None:    
        if trip_data is not None:
            try:
                temp = trip_data[['O_bg_fips', 'O_bg_lng', 'O_bg_lat']]
                temp = temp.drop_duplicates().rename(columns={'O_bg_fips': 'fips12','O_bg_lng':'lng','O_bg_lat':'lat'})
                gdf_temp = gpd.GeoDataFrame(temp[['fips12']], geometry=gpd.points_from_xy(temp['lng'], temp['lat']), crs='EPSG:4326')
                return gdf_temp
            except Exception as e:
                print(f'Error: {e}')
                return None
        else:
            return None

    def calc_grped_stats(self, ) -> None:
        # temp = pd.read_csv('path').rename(columns=COLS_RENAME_DICT).groupby(list(COLS_RENAME_DICT.values())).agg({'trip_distance_meters' : ['count','sum'], 'trip_duration_minutes' : ['sum','mean']})
        # temp.columns = ['n_trips','trip_dist_m', 'trip_duration_min_total', 'trip_duration_min_mean']
        # temp['metro'] = metro
        # temp = temp.reset_index()
        # temp['O_bg_fips'] = temp['O_bg_fips'].astype('str').str.pad(12, 'left','0')
        # temp['D_bg_fips'] = temp['D_bg_fips'].astype('str').str.pad(12, 'left','0')
        # temp = temp.set_index(['O_bg_fips', 'D_bg_fips','primary_mode'])
        print('stub')
        
    def _calc_nearest_nodes(self, ) -> None:
        print('stub')
    
    # Assigning BGs to Zones
    def assign_bg2zones(self) -> None:
        print(self.blockgroup_centroids)
        self.bg2zones = (
            self.blockgroup_centroids
            .to_crs(self.proj)
            .sjoin(
                self.zones
                .reset_index()
                .drop('index',axis=1)
            )
            .rename(columns={'index_right':'zoneID'})
        )

    def export_final_dataset(self) -> None:
        self.final_dataset = (
            self.trip_data
            .reset_index()
            .rename(columns={'value':'dist'})
            .merge(
                self.bg2zones[['fips12','zoneID']],
                left_on = 'O_bg_fips',
                right_on = 'fips12',
                suffixes = ('','_o')
            )
            .drop('fips12', axis=1)
            .merge(
                self.bg2zones[['fips12','zoneID']],
                left_on = 'D_bg_fips',
                right_on = 'fips12',
                suffixes = ('_o','_d')
            )
            .drop('fips12', axis=1)
            .assign(zone_same = lambda x: x.zoneID_o == x.zoneID_d)
        )
    
    # Plotting
    def plot_infrastructure(self) -> None: 
        map_1 = KeplerGl()
        for i in self.infra_data.keys():
            map_1.add_data(self.infra_data[i], name = i)

        map_1

    # Saving
    def save_to_postgres(self, name, pg_connstring, ) -> None: 
        print('stub')
        

    #def load_from_postgres(self, name, )
