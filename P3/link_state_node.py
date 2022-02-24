from simulator.node import Node
import json
import heapq


class Heapq_Object:
    """
    The class stores the Heapq object which is used to return the node with minimum cost.
    Stores the Node_ID along with its Cost and route information

    Custom comparator is implemented to return the smallest value
    Followed the implementation at : https://stackoverflow.com/questions/8875706/heapq-with-custom-compare-predicate
    """
    def __init__(self, node_id: int, cost: int, prev: list):
        self.heapq_data = {}
        self.heapq_data["id"] = node_id
        self.heapq_data["cost"] = cost
        self.heapq_data["prev"] = prev

    def __lt__(self, second_value):
        return self.heapq_data["cost"] < second_value.heapq_data["cost"]

class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        # Maintains the list of neighbors of the current node
        self.my_neighbors_list = []

        # Maintains the routing table containing the information of the nodes and recieved messages
        # Format : { Frozenset(Node 1, Node 2) : { cost = COST, time = TIME } }
        self.my_routing_table = {}

    def __str__(self):
        return "Rewrite this function to define your node dump printout"

    def link_has_been_updated(self, neighbor, latency):
        """
        :param neighbor: The neighbor node ID
        :param latency: Cost of the link from self to the neighbor
        :return: None

        The function receives node updates and updates its routing table information
        Handles deletion and change of cost of a link

        If there is a change, the node would broadcast the message in JSON format to all its neighbors
        """
        # if latency = -1 if delete a link
        if neighbor in self.my_neighbors_list:
            if latency == -1:
                self.my_neighbors_list.remove(neighbor)
            # update cost and time for specified neighbor in routing table
            self.my_routing_table[frozenset((self.id, neighbor))]["cost"] = latency
            self.my_routing_table[frozenset((self.id, neighbor))]["time"] = self.get_time()

        else:
            # if neighbor not in list of neighbors already, create new entry in routing table
            self.my_neighbors_list.append(neighbor)
            new_entry = {"cost": latency, "time": self.get_time()}
            self.my_routing_table[frozenset((self.id, neighbor))] = new_entry

        message = []
        for entry, info in self.my_routing_table.items():
            node1, node2 = entry
            # The JSON format contains:
            # sender_id : ID of the sender, helps in understanding which node sent the message
            # link_info : Nodes between which the link status has been updated
            # link_cost : The change cost of the link
            # time_seq  : When did the change occur, to help the node maintain latest information of the network
            message.append({
                "sender_id": self.id,
                "link_info": [node1, node2],
                "link_cost": info["cost"],
                "time_seq": info["time"]
            })
        lsa_message = json.dumps({"lsdb": message})

        # send updated routing table to neighbors in JSON format
        self.send_to_neighbors(lsa_message)

    # Fill in this function
    def process_incoming_routing_message(self, m):
        """
        :param m: Incoming message from other nodes
        :return: None

        The function parses and handles the incoming message.
        If a newer link info is available, the node would update its own routing table and inform the neighbor
        If the link info is old, the node would send its version of the link info to the message sender
        If the link info is not present with the node, add it to its routing table and broadcast the link info to neighbors
        """

        data = json.loads(m)
        received_lsa_message = data["lsdb"]

        # parse through received routing message
        for each_entry in received_lsa_message:
            message_link = each_entry["link_info"]
            message_link_cost = each_entry["link_cost"]
            message_link_time = each_entry["time_seq"]
            message_sender = each_entry["sender_id"]

            link_node1 = message_link[0]
            link_node2 = message_link[1]

            # move onto next entry if either nodes are the same as the current node
            if link_node1 == self.id or link_node2 == self.id or message_sender == self.id:
                continue

            node_pair = frozenset((link_node1, link_node2))

            # if the link exists in routing table, update values to the ones given by routing message
            if node_pair in self.my_routing_table:
                # check that the new time is greater than the time stored previously
                if self.my_routing_table[node_pair]["time"] < message_link_time:
                    self.my_routing_table[node_pair]["cost"] = message_link_cost
                    self.my_routing_table[node_pair]["time"] = message_link_time
                    node1, node2 = node_pair
                    message = [{
                        "sender_id": self.id,
                        "link_info": [node1, node2],
                        "link_cost": message_link_cost,
                        "time_seq": message_link_time
                    }]
                    lsa_message = json.dumps({"lsdb": message})
                    for each_neighbor in self.my_neighbors_list:
                        if each_neighbor != message_sender:
                            self.send_to_neighbor(each_neighbor, lsa_message)

            # if the link does not exist in routing table, create new entry
            else:
                new_entry = {"cost": message_link_cost, "time": message_link_time}
                self.my_routing_table[node_pair] = new_entry
                node1, node2 = node_pair
                message = [{
                    "sender_id": self.id,
                    "link_info": [node1, node2],
                    "link_cost": message_link_cost,
                    "time_seq": message_link_time
                }]
                lsa_message = json.dumps({"lsdb": message})
                self.send_to_neighbors(lsa_message)

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        ans, _ = self.run_dijkstra(destination)
        if ans is not None:
            return ans[0]
        return -1

    def run_dijkstra(self, destination: int):
        # follows implementation shown in lecture 10
        Q = []
        dist = {}

        # Creating a heapq object, planned to use array but was not able to handle INF cases
        default_q = Heapq_Object(node_id=self.id, cost=0, prev=[])
        heapq.heappush(Q, default_q)

        dist[self.id] = 0

        while len(Q) > 0:

            # popping the node with minimum cost
            vertices_info = heapq.heappop(Q)

            node_id = vertices_info.heapq_data["id"]
            link_cost = vertices_info.heapq_data["cost"]
            prev = vertices_info.heapq_data["prev"]

            # if node found, return the node and the associated link cost
            if node_id == destination:
                return prev, link_cost

            for node_pair, entry in self.my_routing_table.items():
                if entry["cost"] >= 0:
                    d_node1, d_node2 = node_pair
                    if node_id == d_node1:
                        n_key = d_node2
                    elif node_id == d_node2:
                        n_key = d_node1
                    else:
                        n_key = None

                    if n_key is not None:
                        alt = entry["cost"] + link_cost
                        if n_key not in dist or dist[n_key] > alt:
                            new_object = Heapq_Object(node_id=n_key, cost=alt, prev=prev + [n_key])
                            heapq.heappush(Q, new_object)
                            dist[n_key] = alt
        return None
