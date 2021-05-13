from scipy.cluster import hierarchy
from scipy.cluster.hierarchy import optimal_leaf_ordering
from sklearn.preprocessing import normalize

from smap.ordering import OrderingMethod

class OLOSeriation(OrderingMethod):

    name = "Optimal Leaf Ordering"
    clustering = False

    def get_order(self, data):
        norm_data = normalize(data, norm='l2')
        z = hierarchy.ward(norm_data)
        return hierarchy.leaves_list(optimal_leaf_ordering(z, norm_data))
