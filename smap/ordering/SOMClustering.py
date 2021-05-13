from minisom import MiniSom

from smap.ordering import OrderingMethod

class SOMClustering(OrderingMethod):

    name = "Self-Organizing Maps"
    clustering = True

    def get_order(self, data):
        l = data.values.tolist()
        som = MiniSom(20, 1, len(data[0]), sigma=0.6)
        som.train(data, 1000)
        return [som.winner(x)[0] for x in l]
