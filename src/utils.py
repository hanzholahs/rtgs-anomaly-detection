import datetime
import numpy as np
import networkx as nx


def random_payment_value(**args) -> float:
    """
    Computes a random value based on a log-normal distribution.

    :param args: Parameters for the lognormal distribution, typically mean and standard deviation.
    :return: A random value sampled from a log-normal distribution.
    """
    return np.exp(np.random.lognormal(**args))


def random_payment_period(open_time: datetime.datetime,
                          close_time: datetime.datetime,
                          **args) -> datetime.datetime:
    """
    Generates a random datetime within the operation period defined by the open and close times.

    :param open_time: Opening time of the operation period.
    :param close_time: Closing time of the operation, must be after the open time.
    :param args: Additional arguments to be passed to the uniform distribution, typically the bounds for the random period.
    :return: A random datetime within the specified operation period.
    """
    operation_duration = (close_time - open_time).seconds
    random_period = int(np.random.uniform(**args) * operation_duration)
    random_period = datetime.timedelta(seconds = random_period)
    return open_time + random_period


def calc_num_payments(G: nx.DiGraph) -> int:
    return np.sum([data['s'] for _, data in G.edges.items()])


def calculate_network_params(G: nx.DiGraph) -> dict:
    """
    Calculates and returns various parameters of the simulation such as connectivity, reciprocity, and degrees.

    :return: Dictionary containing calculated simulation parameters.
    """        
    num_nodes = G.number_of_nodes()
    num_links = G.number_of_edges()
    connectivity = num_links / (num_nodes * (num_nodes - 1))
    reciprocity = nx.reciprocity(G)
    
    avg_degree = np.mean([val for _, val in G.degree])
    max_k_in = np.max([val for _, val in G.in_degree])
    max_k_out = np.max([val for _, val in G.out_degree])

    num_payments = np.sum([data['s'] for _, data in G.edges.items()])
    
    return {
        "Number of nodes": num_nodes,
        "Number of links": num_links,
        "Connectivity": connectivity,
        "Reciprocity": reciprocity,
        "Average Degree (k)": avg_degree,
        "Max (k-in)": max_k_in,
        "Max (k-out)": max_k_out,
        "Number of payments": num_payments
    }
