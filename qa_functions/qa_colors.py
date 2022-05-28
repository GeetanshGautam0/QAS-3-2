import re
from typing import *
from .qa_std import check_hex_contrast, clamp
from .qa_custom import HexColor


class Convert:
    @staticmethod
    def HexToRGB(color: str):
        return tuple(int("".join(i for i in re.findall(r"\w", color))[j:j + 2], 16) for j in (0, 2, 4))

    @staticmethod
    def RGBToInt(rgb: tuple):
        return rgb[0] << 16 | rgb[1] << 8 | rgb[2]

    @staticmethod
    def IntToRGB(i_rgb: int):
        return i_rgb // 256 // 256 % 256, i_rgb // 256 % 256 // i_rgb // 256

    @staticmethod
    def RGBToHex(rgb: tuple) -> str:
        return "#%02x%02x%02x" % rgb

    @staticmethod
    def HexToInt(color: str):
        return Convert.RGBToInt(Convert.HexToRGB("".join(i for i in re.findall(r"\w", color))))

    @staticmethod
    def IntToHex(val: int):
        return Convert.RGBToHex(Convert.IntToRGB(val))


class Functions:
    @staticmethod
    def fade(start: str, end: str):
        stRGB = Convert.HexToRGB(start)
        edRGB = Convert.HexToRGB(end)

        # Deltas
        deltas_pol = (*[((edRGB[i] - stRGB[i]) / abs(edRGB[i] - stRGB[i])) if (edRGB[i] - stRGB[i]) != 0 else 1 for i in range(3)],)
        deltas = (*[abs(edRGB[i] - stRGB[i]) for i in range(3)],)
        steps = sorted(deltas)[-1]
        o = (start, )

        for step in range(steps):
            o = cast(Tuple[str], (
                *o, Convert.RGBToHex((*[
                    (int(clamp(0, (stRGB[j] + (deltas[j] * deltas_pol[j] / steps * step)), 255)))
                    for j in range(3)],))
            ))

        o = cast(Tuple[str], (*o, end))
        return o

    @staticmethod
    def calculate_more_contrast(one: HexColor, two: HexColor, color: HexColor):
        f, g = one, two

        if not check_hex_contrast(f, color)[0]:
            if check_hex_contrast(g, color)[0]:
                return g
        return f
