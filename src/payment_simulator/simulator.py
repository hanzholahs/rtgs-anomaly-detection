import datetime
from abc import ABC
from typing import Any, Callable

import pandas as pd

from .anomaly import AbstractAnomalyGenerator
from .networks import AbstractPaymentNetwork


class AbstractTransactionSim(ABC):
    """
    Abstract base class for simulating transaction scenarios in a financial network.

    This class is intended to be subclassed to create specific transaction simulation scenarios
    by providing concrete implementations for transaction value calculations and timing.

    Parameters
    ----------
    network : AbstractPaymentNetwork
        An instance of a payment network which handles the simulation of payments.
    value_fn : Callable
        A function to calculate the value of each transaction.
    timing_fn : Callable
        A function to determine the timing of each transaction within the operational hours.
    open_time : str, optional
        The opening time of the transaction window each day, formatted as "HH:MM:SS".
    close_time : str, optional
        The closing time of the transaction window each day, formatted as "HH:MM:SS".

    Attributes
    ----------
    payments : List[tuple]
        A list to store all payment transactions. Each transaction is stored as a tuple containing
        period, timing, sender, receiver, count, and value of the transaction.
    network : AbstractPaymentNetwork
        The payment network instance used for simulating transactions.
    value_fn : Callable
        Function used to calculate the transaction value.
    timing_fn : Callable
        Function used to determine the transaction timing.
    open_time : datetime.time
        Parsed opening time for transactions.
    close_time : datetime.time
        Parsed closing time for transactions.

    Methods
    -------
    get_payments_df() -> pd.DataFrame
        Returns a DataFrame containing all simulated transactions with detailed columns.
    simulate_day(init_banks: int | None = None)
        Simulates a day's transactions using the network's payment simulation function.
    """

    def __init__(
        self,
        network: AbstractPaymentNetwork,
        value_fn: Callable,
        timing_fn: Callable,
        open_time: str = "08:00:00",
        close_time: str = "17:00:00",
    ) -> None:
        """
        Initialize an AbstractTransactionSim with a payment network, transaction value and timing functions,
        and operational hours.
        """
        self.payments: list[tuple] = []
        self.network = network
        self.value_fn = value_fn
        self.timing_fn = timing_fn
        self.open_time = datetime.datetime.strptime(open_time, "%H:%M:%S").time()
        self.close_time = datetime.datetime.strptime(close_time, "%H:%M:%S").time()

    def get_payments_df(self) -> pd.DataFrame:
        """
        Constructs and returns a DataFrame from the accumulated payment transactions.

        Returns
        -------
        pd.DataFrame
            DataFrame containing transaction data with columns for period, time, sender, receiver,
            count, and value.
        """
        col_names = ["Period", "Time", "Sender", "Receiver", "Count", "Value"]
        return pd.DataFrame(self.payments, columns=col_names)

    def simulate_day(self, init_banks: int | None = None):
        """
        Simulates transaction activities for a single day, optionally initializing a specific number of banks.

        Parameters
        ----------
        init_banks : int, optional
            Number of banks to initialize at the start of the day's simulation. If None, the default
            setup of the network is used.
        """
        self.network.simulate_payments(init_banks)


class TransactionSim(AbstractTransactionSim):
    """
    Simulation class for generating transaction patterns in a financial network.

    This class extends `AbstractTransactionSim` and simulates transactions across
    various periods, without introducing anomalies.

    Parameters
    ----------
    sim_id : Any
        An identifier for the simulation, which can be of any type.
    **kwargs : dict
        Additional keyword arguments that are passed to the base class `AbstractTransactionSim`.

    Attributes
    ----------
    sim_id : Any
        Stores the identifier for the simulation.
    payments : list
        Accumulates all the payments made during the simulation.

    Methods
    -------
    run(sim_periods: list[int]) -> None
        Executes the simulation over specified time periods, generating standard payments.
    """

    def __init__(self, sim_id: Any, **kwargs) -> None:
        """
        Initializes the TransactionSim with a simulation identifier and other parameters.
        """
        super().__init__(**kwargs)
        self.sim_id = sim_id

    def run(self, sim_periods: list[int]) -> None:
        """
        Run the simulation for a list of time periods, each representing a discrete simulation interval.

        Parameters
        ----------
        sim_periods : list[int]
            List of periods during which the simulation runs. Each period typically represents a day.

        Notes
        -----
        During each period, the simulation:
        1. Generates a payment network for the day.
        2. Iterates over all links (i.e., bank pairs) in the network.
        3. For each link, generates transactions based on the link weight (number of transactions).
        4. Calculates the timing and value of each transaction without anomalies.
        5. Collects all transactions in a list, storing details including period, timing, sender, receiver, transaction type, and value.
        """
        all_payments: list[tuple] = []

        # Process transactions for each simulation period
        for period in sim_periods:
            self.simulate_day()  # Simulate network dynamics for the day

            # Process each link in the simulated payment network
            for (i, j), data in self.network.G.edges.items():

                # Simulate transactions based on the weight of each link
                for _ in range(data["weight"]):
                    # Calculate transaction timing
                    timing = self.timing_fn(self.open_time, self.close_time)

                    # Calculate transaction value
                    value = self.value_fn()
                    
                    # Store transaction details
                    all_payments.append((period, timing, i, j, 1, value))

        self.payments = all_payments


class AnomalyTransactionSim(AbstractTransactionSim):
    """
    Simulation class for generating anomalous transaction patterns in a financial network.

    Parameters
    ----------
    sim_id : Any
        An identifier for the simulation, which can be of any type.
    anomaly : AbstractAnomalyGenerator
        An anomaly generator instance that modifies payment values to simulate anomalies.
    **kwargs : dict
        Additional keyword arguments that are passed to the base class `AbstractTransactionSim`.

    Attributes
    ----------
    sim_id : Any
        Stores the identifier for the simulation.
    anomaly : AbstractAnomalyGenerator
        Holds the anomaly generator used in the simulation.
    payments : list
        Accumulates all the payments made during the simulation, including anomalies.

    Methods
    -------
    run(sim_periods: list[int]) -> None
        Executes the simulation over specified time periods, generating payments and incorporating anomalies.
    """

    def __init__(
        self, sim_id: Any, anomaly: AbstractAnomalyGenerator, **kwargs
    ) -> None:
        """
        Initializes the AnomalyTransactionSim with a simulation identifier, an anomaly generator, and other parameters.
        """
        super().__init__(**kwargs)
        self.sim_id = sim_id
        self.anomaly = anomaly

    def run(self, sim_periods: list[int]) -> None:
        """
        Run the simulation for a list of time periods, each representing a discrete simulation interval.

        Parameters
        ----------
        sim_periods : list[int]
            List of periods during which the simulation runs. Each period should typically represent a day.

        Notes
        -----
        During each period, the simulation:
        1. Generates a payment network for the day.
        2. Iterates over all links (i.e., bank pairs) in the network.
        3. For each link, generates transactions based on the link weight (number of transactions).
        4. Applies an anomaly to the value of each transaction.
        5. Collects all transactions in a list, storing details including period, timing, sender, receiver, transaction type, and value.
        """
        all_payments: list[tuple] = []

        # Process transactions for each simulation period
        for period in sim_periods:
            self.simulate_day()  # Simulate network dynamics for the day

            # Process each link in the simulated payment network
            for (i, j), data in self.network.G.edges.items():

                # Simulate transactions based on the weight of each link
                for _ in range(data["weight"]):
                    # Calculate transaction timing
                    timing = self.timing_fn(self.open_time, self.close_time)

                    # Calculate transaction value with anomaly
                    value = self.value_fn() + self.anomaly(period)

                    # Store transaction details
                    all_payments.append((period, timing, i, j, 1, value))

        self.payments = all_payments
