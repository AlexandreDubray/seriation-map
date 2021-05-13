import numpy as np
from smap.coloring.Colors import Color, color_to_rgb_scale, interpolate, rgb_to_str

def get_colorscale(distances: list[float], colors: list[Color]):
    total_distance = sum(distances)
    props = [0.0 for _ in distances]
    for i in range(1, len(props)):
        props[i] = min(1.0, props[i-1] + (distances[i]/total_distance))

    divs = np.linspace(0, 1, len(colors))
    c1_idx = 0
    c2_idx = 1
    colorscale = list()
    for prop in props:
        if prop >= divs[c2_idx]:
            c1_idx += 1
            c2_idx += 1
        if c1_idx == len(divs)-1:
            colorscale.append((1.0, rgb_to_str(colors[-1])))
        else:
            alpha = (prop - divs[c1_idx])/(divs[c2_idx] - divs[c1_idx])
            c = interpolate(colors[c1_idx], colors[c2_idx], alpha)
            colorscale.append((prop, rgb_to_str(c)))
    print(colorscale[:5])
    rounded = [(round(x,2),y) for x,y in colorscale]
    rounded = [x for i, x in enumerate(rounded) if i == 0 or x != rounded[i-1]]
    return rounded
