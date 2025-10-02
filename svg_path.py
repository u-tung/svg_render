import numpy as np
import re
from typing import Any
from copy import deepcopy


class InvalidSVGPath(Exception):
    ...


class SVGPath:

    def __init__(self, pathStr: str):
        assert isinstance(pathStr, str)
        self._data = self._parsePathStr(pathStr)

    def _parsePathStr(
        self, pathStr: str
    ) -> list[str | np.ndarray[Any, np.dtype[np.float32]] | float]:

        PREFIX = r"[A-Za-z]"
        SEP = r"(?: +|, *)"
        NUMBER = r"(?:-?\d+(?:\.\d*)?|-?\.\d+)"
        POSITION_AREA = rf"(?:(?:{NUMBER}{SEP}??)*)"
        COMMAND = rf"({PREFIX}){SEP}?({POSITION_AREA}){SEP}?(?={PREFIX}|$)"

        commands = []
        while pathStr:
            match_ = re.match(COMMAND, pathStr)
            if match_ is None:
                raise InvalidSVGPath(f"Invalid svg path '{pathStr}'")

            prefix, positions = match_.groups()

            positions = re.findall(NUMBER, positions)
            if prefix.upper() == "M" and len(positions) % 2:
                raise InvalidSVGPath(f"Invalid svg path '{pathStr}'")
            elif prefix.upper() == "C" and len(positions) % 6:
                raise InvalidSVGPath(f"Invalid svg path '{pathStr}'")
            elif prefix.upper() == "L" and len(positions) %2:
                raise InvalidSVGPath(f"Invalid svg path '{pathStr}'")
            elif prefix.upper() == "Z" and len(positions) != 0:
                raise InvalidSVGPath(f"Invalid svg path '{pathStr}'")

            if len(positions) >= 2:
                positions = [np.array(pos, "f") for pos in zip(positions[::2], positions[1::2])]
            elif len(positions) == 1:
                positions[0] = float(positions[0])

            commands.append((prefix, *positions))
            pathStr = pathStr[match_.end():]

        return commands

    def scale(self, ratio: float) -> None:
        for i, (prefix, *positions) in enumerate(self): # type: ignore
            if len(positions) == 1 and isinstance(positions[0], float):
                self._data[i] = (prefix, self[i][1] * ratio) # type: ignore
            for pos in positions:
                pos *= ratio

    def __getitem__(self, index) -> tuple[str | np.ndarray[Any, np.dtype[np.float32]] | float]:
        return self._data[index]

    def __repr__(self, ) -> str:
        return f"{self.__class__.__name__}('{str(self)}')"

    def _reprCommand(self, command) -> str:
        if len(command) == 2 and isinstance(command[1], float):
            return f"{command[0]} {command[1]}"
        return f"{command[0]} {', '.join(' '.join(str(j) for j in i) for i in command[1:])}"

    def __str__(self, ):
        return " ".join(self._reprCommand(cmd) for cmd in self)

    def __len__(self, ):
        return len(self._data)

    def copy(self, ):
        result = self.__class__("")
        result._data = deepcopy(self._data)
        return result


def test():
    s = SVGPath("m 65.143231,131.19969 c 0,0 7.914598,-25.87465 23.439387,-2.43526 15.524792,23.43938 -23.439387,2.43526 -23.439387,2.43526 z")
    s = SVGPath("M5.053,15.158c0,1.395-1.131,2.526-2.526,2.526C1.131,17.684,0,16.553,0,15.158c0-1.395,1.131-2.526,2.526-2.526h2.526    V15.158z")
    s = SVGPath("m277.983 203.645c-14.03 0-22.35-7.18-22.987-17.52h13.414c0 3.447 1.91 8.035 10.21 8.32 5.752 0 8.935-3.446 8.935-6.037-.637-4.018-5.752-4.303-10.846-5.181-5.752-.834-10.209-1.998-13.414-3.425-4.457-2.305-7.026-7.201-7.026-12.36 0-9.2 7.684-16.38 21.077-16.38 12.778 0 21.077 6.61 21.691 16.665h-12.755c0-2.57-.637-6.894-8.3-6.894-5.115 0-8.298.856-8.935 4.588 0 5.182 10.846 4.896 19.145 6.894 7.662 2.02 12.777 6.894 12.777 13.81 0 12.646-10.209 17.52-22.986 17.52m-244.446-84.845 44.042-25.578 23.623 40.53h-59.366")
    print(s)


if __name__ == "__main__":
    test()
