import subprocess

from scipy.spatial.distance import pdist, squareform
from sklearn.preprocessing import normalize

from smap.ordering import OrderingMethod


class TSPSeriation(OrderingMethod):

    name = "TSP based Seriation"
    clustering = False

    def get_order(self, data):
        norm_data = normalize(data, norm='l2')
        dist = squareform(pdist(norm_data))
        self._write_tsp_file(dist)
        subprocess.call('concorde problem.tsp', shell=True)
        return self._get_tsp_sol()

    def _write_tsp_file(self, distance_matrix):
        with open('problem.tsp', 'w') as f:
            f.write('NAME : seriation\n')
            f.write('TYPE: TSP\n')
            f.write(f'DIMENSION: {len(distance_matrix) + 1}\n')
            f.write('EDGE_WEIGHT_TYPE: EXPLICIT\n')
            f.write('EDGE_WEIGHT_FORMAT: FULL_MATRIX\n')
            f.write('EDGE_WEIGHT_SECTION\n')
            f.write(' ' + ' '.join(['0' for _ in range(len(distance_matrix) + 1)]))
            f.write('\n')
            for row in distance_matrix:
                f.write(' 0 ' + ' '.join([str(int(x*1000)) for x in row]))
                f.write('\n')
            f.write('EOF\n')

    def _get_tsp_sol(self):
        order = list()
        with open('problem.sol', 'r') as f:
            first = True
            for line in f:
                if first:
                    first = False
                    continue
                order += [int(x) - 1 for x in line.rstrip().split(' ') if int(x) != 0]
        return order
