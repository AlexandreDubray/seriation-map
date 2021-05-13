import numpy as np

from smap.features import NumericalFeature, CategoricalFeature
from smap.features.utils import haversine

class Distance(NumericalFeature):

    name = 'distance'
    dependencies = []

    def compute(self, data, **kwargs):
        if self.name not in data.columns:
            self.add_dependencies(data, **kwargs)
            lat = kwargs['lat']
            lon = kwargs['lon']
            data[self.name] = haversine(data[lon].shift(-1).fillna(data.loc[len(data)-1, lon]),
                                        data[lat].shift(-1).fillna(data.loc[len(data)-1, lat]),
                                        data[lon],
                                        data[lat])

class Velocity(NumericalFeature):

    name = 'velocity'
    dependencies = [Distance()]

    def compute(self, data, **kwargs):
        if self.name not in data.columns:
            self.add_dependencies(data, **kwargs)
            dist = data[Distance().name]
            durs = data['duration']
            data[self.name] = dist / (durs / 3600)

class TimeUsage(CategoricalFeature):

    name = 'time usage'
    dependencies = [Velocity()]

    values = ['congestion', 'work', 'driving']

    def compute(self, data, **kwargs):
        if self.name not in data.columns:
            self.add_dependencies(data, **kwargs)
            if 'predefined_labels' in kwargs:
                for val in kwargs['predefined_labels']:
                    if val != '' and val not in self.values:
                        self.values.append(val)
            velocity = data[Velocity().name]
            duration = data['duration']
            predefined_labels = kwargs['predefined_labels'] if 'predefined_labels' in kwargs else [np.nan for _ in range(len(data))]

            def type(idx):
                if velocity[idx] <= 15:
                    if duration[idx] < 600:
                        return 'congestion'
                    if predefined_labels[idx] != '':
                        return predefined_labels[idx]
                    return 'work'
                return 'driving'

            data[self.name] = [type(i) for i in range(len(data))]
