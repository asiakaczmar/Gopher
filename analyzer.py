import pickle
import logging

import networkx as nx
import matplotlib.pyplot as plt

from downloader import TweeUser
import settings

logging.basicConfig(level=logging.DEBUG)
logger = logging


def load_user(id):
    with open(settings.BASIC_PATH + 'user' + str(id) + '.txt', 'r') as f:
        return pickle.load(f)

def save_graph(graph):
    with open(settings.BASIC_PATH + 'graph.txt', 'w') as f:
        pickle.dump(graph, f)

def draw_graph():
    with open(settings.BASIC_PATH + 'graph.txt') as f:
        graph = pickle.load(f)
        nx.draw(graph)
        plt.show()


class Analyser(object):

    def __init__(self):
        self.graph = nx.Graph()

    def retweet_measure(self, user):
        if user.tweets:
            retweet_counter = reduce(lambda  x,y: x+y.retweet_count, user.tweets, 0)
            return round(float(retweet_counter)/len(user.tweets), 2)
    
    def add_nodes(self, user):
        logger.debug('processing connections for user %s' % user.name)

        connected_users = []
        node_name = self._get_node_name(user)

        ids = user.friends_ids + user.followers_ids
        ids = list(set(ids))

        for id_ in ids:
            logger.debug('processing connection %s' % id_)
            try:
                new_user = load_user(id_)
                new_node_name = self._get_node_name(new_user)
                #making sure we don't get lost in cycles
                if new_node_name not in self.graph.nodes():
                    connected_users.append(new_user)

                self.graph.add_node(new_node_name)
                self.graph.add_edge(node_name, new_node_name)

            except IOError, e:
                logger.error(e)
        return connected_users

    def _get_node_name(self, user):
        measure = self.retweet_measure(user)
        new_node_name = (user.name, measure)
        return new_node_name
    
    def create_graph(self, start_user_id):
        # crate the first node
        start_user = load_user(start_user_id)
        user_node_name = self._get_node_name(start_user)
        self.graph.add_node(user_node_name)

        # breadth first traversal
        new_connections = [start_user]
        levels_left = settings.DEPTH
        while new_connections or levels_left > 0:
            connections, new_connections = new_connections, []
            for c in connections:
                new_connections += self.add_nodes(c)
                nx.draw(self.graph)
                plt.show()
            levels_left -= 1
        save_graph(self.graph)


if __name__ == '__main__':
    a = Analyser()
    a.create_graph(15009456)
    draw_graph()
