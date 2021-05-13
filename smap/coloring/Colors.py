import re

Color = tuple[int, int ,int]

def rgb_to_str(color: Color) -> str:
    return f'rgb({color[0]}, {color[1]}, {color[2]})'

def str_to_rgb(color: str) -> Color:
    return tuple(int(x) for x in re.findall(r'\d+', color))

def color_to_rgb_scale(color: Color) -> tuple[float, float, float]:
    return tuple(color[i] / 255.0 for i in range(3))

def interpolate(c1: Color, c2: Color, alpha: float) -> Color:
    beta = 1 - alpha
    return tuple(int(beta*x+alpha*y) for x,y in zip(c1, c2))
