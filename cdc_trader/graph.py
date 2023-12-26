import matplotlib.pyplot as plt
import networkx as nx


class CryptoGraph:
    def __init__(self):
        self.graph = {}

    def add_edge(self, crypto1, crypto2):
        if crypto1 not in self.graph:
            self.graph[crypto1] = []
        self.graph[crypto1].append(crypto2)

    def find_conversion_sequence(self, start_crypto, target_crypto, path=[]):
        path = path + [start_crypto]
        if start_crypto == target_crypto:
            return path
        if start_crypto not in self.graph:
            return None
        for crypto in self.graph[start_crypto]:
            if crypto not in path:
                new_path = self.find_conversion_sequence(
                    crypto, target_crypto, path)
                if new_path:
                    return new_path
        return None


# Create a graph and add edges
def find_sequences(CryptoGraph, instrument_names, currency_names):
    crypto_graph = CryptoGraph()
    for instrument in instrument_names:
        base, quote = instrument.split('_')
        crypto_graph.add_edge(base, quote)

# Find conversion sequences
    conversion_sequences = []
# Cross currencies
    for currency1 in currency_names:
        for currency2 in currency_names:
            if currency1 != currency2:
                conversion_sequence = crypto_graph.find_conversion_sequence(
                    currency1, currency2)
                if conversion_sequence:
                    # print(f"Conversion Sequence from {currency1} to {currency2}: {conversion_sequence}")
                    conversion_sequences.append(conversion_sequence)
                # input()
                else:
                    pass
    return conversion_sequences

# conversion_sequences = find_sequences(CryptoGraph, instrument_names, currency_names)
# print(conversion_sequences)


# Create a directed graph
def directed_graph(conversion_sequences):
    G = nx.DiGraph()

# Add edges based on cryptocurrency pairs
    for pair in conversion_sequences:
        for i in range(len(pair) - 1):
            source, target = pair[i], pair[i + 1]
            if G.has_edge(source, target):
                G[source][target]['weight'] += 1
            else:
                G.add_edge(source, target, weight=1)

# Draw the graph
    pos = nx.spring_layout(G)  # You can choose different layout algorithms
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw(G, pos, with_labels=True, node_size=700,
            node_color='skyblue', font_size=8)
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=edge_labels, font_color='red')

    plt.show()

# directed_graph(conversion_sequences)
