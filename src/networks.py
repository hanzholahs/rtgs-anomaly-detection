import numpy as np
import pandas as pd
import networkx as nx
from abc import ABC


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



class AbstractPaymentNetwork(ABC):
    def __init__(self) -> None:
        self.G = None


    def extract_link_matrix(self) -> np.ndarray:
        """
        Extracts and returns the adjacency matrix of the network graph where each element (i, j) in the matrix represents the number of transactions from bank i to bank j.

        :return: A numpy ndarray representing the adjacency matrix of the network graph.
        """
        return nx.to_numpy_array(self.G, weight='s')


    def _random_bank(self, prob) -> int:
        """
        Selects a bank for initiating a transaction based on a weighted probability distribution.

        :return: The selected bank's identifier.
        """
        return np.random.choice(self.G.nodes(), p=prob)
    

    def _payment_link(self, sender: int, receiver: int) -> None:
        """
        Creates or updates a payment link between two banks in the simulation graph.

        :param sender: The identifier of the bank initiating the payment.
        :param receiver: The identifier of the bank receiving the payment.
        """
        if self.G.has_edge(sender, receiver):
            self.G[sender][receiver]['s'] += 1
        else:
            self.G.add_edge(sender, receiver, s=1)



class SimplePaymentNetwork(AbstractPaymentNetwork):
    def __init__(self,
                 total_banks: int,
                 avg_payments: int,
                 alpha: float = 1.0,
                 allow_self_loop: bool = False) -> None:
        """
        Initializes the RTGS Simulator with specified parameters.

        :param total_banks: Total number of banks participating in the RTGS simulation.
        :param avg_payments: Average number of payments each bank is expected to process during the simulation.
        :param alpha: A learning rate parameter that influences the strength of preferential attachment in the simulation.
        :param allow_self_loop: Boolean indicating whether transactions within the same bank (self-loops) are allowed.
        """
        super().__init__()

        # set simulation parameters
        self.alpha = alpha
        self.total_banks = total_banks
        self.avg_payments = avg_payments
        self.allow_self_loop = allow_self_loop


    def simulate_payments(self, init_banks: int = None) -> None:
        """
        Simulate the payment processing between banks for a given date, starting with an initial set of banks.

        :param date: The date on which the payments are to be simulated.
        :param init_banks: Initial number of banks to start the simulation with.
        """
        if init_banks is None:
            init_banks = int(1 + np.ceil(self.total_banks / 2))
        
        # Initialize the graph with some nodes
        self.G = nx.DiGraph() # graph network
        self.G.add_nodes_from(list(range(init_banks)))

        # Initialize preference vector
        self.h = np.ones(init_banks, dtype=float)
        
        # Simulate payment network
        for k in range(init_banks, self.total_banks):
            for l in range(self.avg_payments):
                # select sender and receiver
                prob = self.h / self.h.sum()
                sender = self._random_bank(prob)
                receiver = self._random_bank(prob)

                # prevent self-loop transactions unless explicitly allowed
                while sender == receiver and not self.allow_self_loop:
                    receiver = self._random_bank(prob)

                # update payment link between banks
                self._payment_link(sender, receiver)

                # update preferential attachment strength
                self.h[sender] += self.alpha
                self.h[receiver] += self.alpha

            # Initialize the next bank/node
            self.G.add_node(k) 
            self.h = np.append(self.h, 1.)



if __name__ == "__main__":
    network = SimplePaymentNetwork(total_banks=10,
                                   avg_payments=1000,
                                   alpha=0.1,
                                   allow_self_loop=False)
    network.simulate_payments()

    print("Bank strengths:")
    print(network.h)

    print("Network params:")
    print(pd.Series(calculate_network_params(network.G)))

    print("Network links:")
    print(network.extract_link_matrix())