from enum import Enum
import numpy as np
import pandas as pd
import networkx as nx


class Year(Enum):
    year_2018 = 2018
    year_2019 = 2019
    year_2020 = 2020


def get_ranking_file_path(year):
    switch = {
        Year.year_2018: "../data/atp_rankings_10s_cleaned.csv",
        Year.year_2019: "../data/atp_rankings_10s_cleaned.csv",
        Year.year_2020: "../data/atp_rankings_current_cleaned.csv"
    }
    return switch.get(year)


def year_string_to_enum(year):
    switch = {
        "2018": Year.year_2018,
        "2019": Year.year_2019,
        "2020": Year.year_2020
    }
    return switch.get(year)


def get_ranking_data(year):
    ranking_file_path = get_ranking_file_path(year)
    ranking_data = pd.read_csv(ranking_file_path)

    if year == Year.year_2018:
        mask = (ranking_data['ranking_date'] >= 20180000) & (ranking_data['ranking_date'] < 20190000)
    elif year == Year.year_2019:
        mask = (ranking_data['ranking_date'] >= 20190000) & (ranking_data['ranking_date'] < 20200000)

    if year == Year.year_2018 or year == Year.year_2019:
        return ranking_data[mask]
    else:
        return ranking_data


def get_points_data(year, data_all_players):
    ranking_file_path = get_ranking_file_path(year)
    ranking_data = pd.read_csv(ranking_file_path).drop_duplicates(keep="first")
    ranking_data = ranking_data.drop_duplicates(keep="first")

    if year == Year.year_2018:
        mask = (ranking_data['ranking_date'] == 20181231)
    elif year == Year.year_2019:
        mask = (ranking_data['ranking_date'] == 20191230)
    elif year == Year.year_2020:
        mask = (ranking_data['ranking_date'] == 20201221)

    ranking_data['player'].apply(pd.to_numeric)

    ranking_data = ranking_data[mask]
    return ranking_data.set_index('player').join(data_all_players.set_index('player_id'))


def get_player_rank(player_id, ranking_data):
    ranking_mask = ranking_data['player'] == player_id
    ranking_single_player = ranking_data[ranking_mask]
    ranks = ranking_single_player[['rank']].values
    if ranks.any():
        average_rank = np.round(np.average(ranks), 2)
        std_deviation = np.round(np.std(ranks))
    else:
        average_rank = -1.0
        std_deviation = -1.0

    return average_rank, std_deviation


def add_player_node(graph, player_id, players_data, ranking_data):

    avg_rank, std_dev = get_player_rank(player_id, ranking_data)

    rank_class = int(avg_rank)

    player_mask = players_data['player_id'] == player_id
    player = players_data[player_mask].values[0]
    graph.add_node(player_id,
                   name=player[1] + ' ' + player[2],
                   country_code=player[3],
                   hand=player[4],
                   avg_rank=avg_rank,
                   std_dev=std_dev,
                   rank_class=rank_class)


def calculate_centralities(G):

    DC_dict = nx.degree_centrality(G)
    CC_dict = nx.closeness_centrality(G)
    BC_dict = nx.betweenness_centrality(G)
    EVC_dict = nx.eigenvector_centrality(G)

    names = nx.get_node_attributes(G, "name")
    df0 = pd.DataFrame.from_dict(names, orient='index', columns=['info'])
    df1 = pd.DataFrame.from_dict(DC_dict, orient='index', columns=['DC'])
    df2 = pd.DataFrame.from_dict(CC_dict, orient='index', columns=['CC'])
    df3 = pd.DataFrame.from_dict(BC_dict, orient='index', columns=['BC'])
    df4 = pd.DataFrame.from_dict(EVC_dict, orient='index', columns=['EVC'])
    df = pd.concat([df0, df1, df2, df3, df4], axis=1)
    return df, DC_dict, CC_dict, BC_dict, EVC_dict


def players_nationalities(G):
    names = nx.get_node_attributes(G, "name")
    countries = nx.get_node_attributes(G, "country_code")
    df0 = pd.DataFrame.from_dict(names, orient='index', columns=['info'])
    df1 = pd.DataFrame.from_dict(countries, orient='index', columns=['country_code'])

    df = pd.concat([df0, df1], axis=1)
    return df


def get_all_players():
    all_players_path = "../data/atp_players.csv"
    return pd.read_csv(all_players_path)


def calculate_sum_of_differences(dictionary):
    sum_of_diff = 0
    max_value = max(dictionary.values())
    for value in dictionary.values():
        sum_of_diff += (max_value - value)

    return sum_of_diff


def calculate_graph_centralities(G, DC_dict, CC_dict, BC_dict):
    DC_sum_of_diff = calculate_sum_of_differences(DC_dict)
    CC_sum_of_diff = calculate_sum_of_differences(CC_dict)
    BC_sum_of_diff = calculate_sum_of_differences(BC_dict)
    # EVC_sum_of_diff = calculate_sum_of_differences(EVC_dict)

    star_graph = nx.star_graph(G.number_of_nodes() - 1)

    star_DC_dict = nx.degree_centrality(star_graph)
    star_CC_dict = nx.closeness_centrality(star_graph)
    star_BC_dict = nx.betweenness_centrality(star_graph)
    # star_EVC_dict = nx.eigenvector_centrality(star_graph)

    star_DC_sum_of_diff = calculate_sum_of_differences(star_DC_dict)
    star_CC_sum_of_diff = calculate_sum_of_differences(star_CC_dict)
    star_BC_sum_of_diff = calculate_sum_of_differences(star_BC_dict)
    # star_EVC_sum_of_diff = calculate_sum_of_differences(star_EVC_dict)

    network_DC = DC_sum_of_diff / star_DC_sum_of_diff
    network_CC = CC_sum_of_diff / star_CC_sum_of_diff
    network_BC = BC_sum_of_diff / star_BC_sum_of_diff
    # network_EVC = EVC_sum_of_diff / star_EVC_sum_of_diff

    return network_DC, network_CC, network_BC
