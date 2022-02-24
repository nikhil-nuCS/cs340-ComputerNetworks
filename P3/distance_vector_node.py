import json

from simulator.node import Node


class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)

        # Stores distance vector table of the current node
        # Format : {{ STR(NODE) : { route : [ROUTE INFO], cost : COST }}
        self.my_distance_vector_table = self.get_default_routing_table(self.id)

        # Stores the neighbors distance vector table. Uses the information to compute its own DV table.
        # All nodes have complete network information and hence separating self's DV with neighbor's DV
        # Format : {NEIGHBOR ID : { STR(NODE) : { route : [ROUTE INFO], cost : COST }}}
        self.neighbors_distance_vector_table = {}

        # Maintains the list of neighbors of the current node
        self.my_neighbor_list = []

        # Maintains the edge list info of its neighbors and store link cost
        # Format : { STR(NODE) : COST }
        self.my_edge_list = {}

        # Stores current sequence number of the program, increments each time a new message is sent to the neighbors
        self.curr_seq_number = 0

        # Stores timing of the last message received from the neighbor, it is used to determine if the DV message needs to be processed
        # Format : { STR(NODE) : TIME }
        self.neighbors_last_message_time = {}

    # Return a string
    def __str__(self):
        return "Rewrite this function to define your node dump printout"

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        """
        :param neighbor: The neighbor node ID
        :param latency: Cost of the link from self to the neighbor
        :return: None

        The function receives node updates and updates its routing table information
        Handles deletion and change of cost of a link
        It updates the edge list, neighbor list and neighbors routing table accordingly.
        Once the information is stored, the DV table is updated as the link info can introduce changes to DV

        If there is a change, the node's updated DV would be broadcasted in JSON format to all its neighbors
        """

        # latency = -1 if delete a link
        if neighbor in self.my_neighbor_list:
            if latency == -1:
                # remove the entry from all stored information
                self.my_neighbor_list.remove(neighbor)
                del self.neighbors_distance_vector_table[neighbor]
                del self.neighbors_last_message_time[neighbor]
                del self.my_edge_list[neighbor]
            else:
                # update cost for specified neighbor in edge list dictionary
                self.my_edge_list[neighbor] = latency
        else:
            # if neighbor not in list of neighbors already, create new entry in DV table
            # Add its entry into neighbors DV table that will be used to compute self's DV table
            self.my_neighbor_list.append(neighbor)
            self.neighbors_last_message_time[neighbor] = 0
            self.my_edge_list[neighbor] = latency
            self.neighbors_distance_vector_table[neighbor] = self.get_default_routing_table(neighbor)

        self.handle_dv_link_update()

    # Fill in this function
    def process_incoming_routing_message(self, m):
        """
        :param m: Incoming message from other nodes
        :return: None

        The function parses and handles the incoming message.
        If a newer DV version of a neighbor is available, the node would recompute its own DV routing table and inform the neighbors
        If the DV table info is old, it is discarded
        Neighbors default DV is always present with the node, which is created at the time of adding the neighbor
        """
        data = json.loads(m)
        received_dv_message = data["dv"]
        message_sender = received_dv_message["sender_id"]
        message_time = received_dv_message["time_seq"]
        message_dv = received_dv_message["dv_info"]

        if message_sender in self.neighbors_last_message_time:
            if message_time > self.neighbors_last_message_time[message_sender]:
                self.neighbors_last_message_time[message_sender] = message_time
                self.neighbors_distance_vector_table[message_sender] = message_dv
                self.recompute_dv_table()

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        ans = self.my_distance_vector_table[str(destination)]["route"]
        if ans is not None:
            return int(ans[0])
        return -1

    def get_default_routing_table(self, for_node):
        return {str(for_node): {"route": [None], "cost": 0}}

    def handle_dv_link_update(self):
        """
        :return: None

        Updates the node's DV table according to the DV information received from other nodes
        Follows Bellman-Ford's Algorithm. Implemented from : https://www.javatpoint.com/bellman-ford-algorithm
        """

        # TEMP DV table is created which stores the computed DV
        # if there is an update, this table is broadcasted to all neighbors
        my_temp_distance_vector, graph_nodes = self.get_graph_nodes()

        for each_graph_node in graph_nodes:
            if self.id != int(each_graph_node):
                minimum_cost = float("inf")
                minimum_hops = [-1]
            else:
                minimum_cost = 0
                minimum_hops = [None]
            each_graph_node = str(each_graph_node)

            # Each neighbors DV table is iterated over and the cost is calculated.
            # The minimum cost is stored which is then updated in the TEMP DV table
            for neighbor, neighbor_distance_vector in self.neighbors_distance_vector_table.items():
                if each_graph_node in neighbor_distance_vector:
                    neighbor_route = neighbor_distance_vector[each_graph_node]["route"]
                    if self.id not in neighbor_route:
                        # Followed lecture implementation
                        alt = neighbor_distance_vector[each_graph_node]["cost"] + self.my_edge_list[neighbor]
                        if alt <= minimum_cost:
                            minimum_cost = alt
                            minimum_hops = [neighbor] + neighbor_route
            my_temp_distance_vector[str(each_graph_node)] = {"cost": minimum_cost, "route": minimum_hops}

        self.check_dv_and_update_neighbors(my_temp_distance_vector)

    def get_graph_nodes(self):
        """
        :return: TEMP DV TABLE in default format, nodes known from the network
        """
        my_temp_distance_vector = {str(self.id): {"route": [None], "cost": 0}}
        graph_nodes = [str(self.id)]

        for each_neighbor in self.my_neighbor_list:
            for each_node in self.neighbors_distance_vector_table[each_neighbor]:
                if each_node not in graph_nodes:
                    graph_nodes.append(each_node)

        return my_temp_distance_vector, graph_nodes

    def check_dv_and_update_neighbors(self, recomputed_distance_vector_table):
        """
        :param recomputed_distance_vector_table: The recomputed DV table according to Bellman Ford Algo
        :return: None

        If the recomputed version of the DV routing table is not the same as the current version, then inform all neighbors
        The message is sent in JSON format:
            sender_id : Sending node ID
            dv_info : The complete DV table is sent as message, this is then stored as neighbors DV table when received by other nodes
            time_seq : Sequence number to help eliminate outdated versions of DV table
        """
        if self.my_distance_vector_table != recomputed_distance_vector_table:
            # Update the seq number to ensure up-to-date DV table computation by other nodes
            self.curr_seq_number += 1

            # Update self's DV
            self.my_distance_vector_table = recomputed_distance_vector_table

            # The JSON format contains:
            # sender_id : ID of the sender, helps in understanding which node sent the message
            # dv_info   : The complete DV table of the node
            # time_seq  : When did the change occur, to help the node maintain latest information of the network
            message = {
                "sender_id": self.id,
                "dv_info": recomputed_distance_vector_table,
                "time_seq": self.curr_seq_number
            }
            dv_message = json.dumps({"dv": message})
            self.send_to_neighbors(dv_message)

    def recompute_dv_table(self):
        """
        :return: None

        Recomputes the node's DV table according to the DV information received from other nodes
        Follows Bellman-Ford's Algorithm. Implemented from : https://www.javatpoint.com/bellman-ford-algorithm
        """

        # TEMP DV table is created which stores the computed DV
        # if there is an update, this table is broadcasted to all neighbors
        my_temp_distance_vector, graph_nodes = self.get_graph_nodes()

        for each_graph_node in graph_nodes:
            if self.id != int(each_graph_node):
                # Setting the minimum cost to INF, to determine the shortest path possible
                minimum_cost = float("inf")
                minimum_hops = [-1]

                # storing node info in string format, as JSON dumps converts all data into string
                # causes crashes if not done as int to string mapping fails
                each_graph_node = str(each_graph_node)

                # Each neighbors DV table is iterated over and the cost is calculated.
                # The minimum cost is stored which is then updated in the TEMP DV table
                for neighbor, neighbor_distance_vector in self.neighbors_distance_vector_table.items():
                    if each_graph_node in neighbor_distance_vector and neighbor in self.my_edge_list:
                        neighbor_route = neighbor_distance_vector[each_graph_node]["route"]
                        if self.id not in neighbor_route:
                            alt = neighbor_distance_vector[each_graph_node]["cost"] + self.my_edge_list[neighbor]
                            if alt < minimum_cost:
                                minimum_cost = alt
                                minimum_hops = [neighbor] + neighbor_route
            else:
                minimum_cost = 0
                minimum_hops = [None]

            my_temp_distance_vector[str(each_graph_node)] = {"cost": minimum_cost, "route": minimum_hops}

        self.check_dv_and_update_neighbors(my_temp_distance_vector)