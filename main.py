import cv2
import numpy as np
import re

class SVGPath:

    def __init__(self, pathStr: str):
        assert isinstance(pathStr, str)

        self.path = self.strToPath(pathStr)

    @staticmethod
    def strToPath(pathStr: str) -> list:
        assert isinstance(pathStr, str)
        # assert re.match(r"(([Mm] \d+ \d+|[cC] \d+ \d+, \d+ \d+, \d+ \d+) ?)+$", pathStr)

        path = []
        for i in re.findall(r"(?a)(\w) ((?:[-0-9.]+ [-0-9.]+(?:, )?)+)", pathStr):
            points = [ np.array([float(k) for k in j.split(" ")], "f") for j in re.split(", ?", i[1]) ]

            if i[0].upper() == "C":
                assert len(points) == 3
            elif i[0].upper() == "M":
                assert len(points) == 1

            path.append( (i[0], *points) )

        return path

    def standardize(self, maxX, maxY) -> None:
        for prefix, *points in self.path:
            for point in points:
                point /= [maxX, maxY]


def generateMask(size: tuple, svgPath: SVGPath, step: float = 0.0001) -> np.ndarray:
    assert isinstance(size, tuple)
    assert isinstance(svgPath, SVGPath)

    mask = np.zeros(size, "bool")
    cursorPos = np.array([0, 0], "float")
    for prefix, *points in svgPath.path:

        if prefix == "M":
            cursorPos = points

        elif prefix == "m":
            cursorPos += points[0]

        elif prefix == "C":
            def matchSize(point):
                point[0] = point[0]*(size[1]-1)
                point[1] = point[1]*(size[0]-1)
                return point

            oriPoint = matchSize(points[0])
            endPoint = matchSize(points[1])
            ctrlPoint = matchSize(points[2])

            mask |= _calculateCurveMask(mask, oriPoint, endPoint, ctrlPoint, step)
            cursorPos = endPoint

        elif prefix == "c":
            def matchSize(point):
                point[0] = point[0]*(size[1]-1)
                point[1] = point[1]*(size[0]-1)
                return point

            oriPoint = matchSize(points[0]) + cursorPos
            endPoint = matchSize(points[1]) + cursorPos
            ctrlPoint = matchSize(points[2]) + cursorPos

            mask |= _calculateCurveMask(mask, oriPoint, endPoint, ctrlPoint, step)
            cursorPos = endPoint

    return mask


def _calculateCurveMask(
        mask: np.ndarray,
        oriPoint: np.ndarray,
        endPoint: np.ndarray,
        ctrlPoint: np.ndarray,
        step: float
    ) -> np.ndarray:
        visited = np.zeros(mask.shape, "bool")
        i = 0
        cursorPos = np.array([0., 0.])
        prevPos = np.array([1., 1.])

        def slope(x1,y1,x2,y2):
            return (y1 - y2) / (x1 - x2)

        print(abs(slope(*cursorPos, *prevPos)))
        while i < 1:
            cursorPos = (1-i)**2*oriPoint + 2*i*(1-i)*ctrlPoint + i**2*endPoint
            if abs(slope(*cursorPos, *prevPos)) >= 99:
                print(abs(slope(*cursorPos, *prevPos)))
                break
            if 0 <= int(mask.shape[0]-1-cursorPos[1]) <= mask.shape[0]-1 and 0 <= int(cursorPos[0]) <= mask.shape[1]-1:
                continue
            if not visited[int(mask.shape[0]-1-cursorPos[1]), int(cursorPos[0])]:
                mask1 = np.array(mask, "uint8") * 255
                cv2.imshow("test", mask1)
                cv2.waitKey(1)
                # mask[int(mask.shape[0]-1-cursorPos[1]):, int(cursorPos[0])] ^= True
                mask[int(mask.shape[0]-1-cursorPos[1]):, int(cursorPos[0])] = True
            visited[int(mask.shape[0]-1-cursorPos[1]), int(cursorPos[0])] = 1
            prevPos = cursorPos
            i += step

        mask2 = np.zeros(mask.shape, "bool")
        while i < 1:
            cursorPos = (1-i)**2*oriPoint + 2*i*(1-i)*ctrlPoint + i**2*endPoint
            if not visited[int(mask.shape[0]-1-cursorPos[1]), int(cursorPos[0])]:
                mask1 = np.array(mask2 ^ mask, "uint8") * 255
                cv2.imshow("test", mask1)
                cv2.waitKey(1)
                # mask[int(mask.shape[0]-1-cursorPos[1]):, int(cursorPos[0])] ^= True
                mask2[int(mask.shape[0]-1-cursorPos[1]):, int(cursorPos[0])] = True
            visited[int(mask.shape[0]-1-cursorPos[1]), int(cursorPos[0])] = 1
            i += step

        return mask ^ mask2


def main():
    # imgPath = "/Users/intong/Desktop/00062-2443895948-strybk, Labrador Walking Through City, Fantasy Artwork Style, Cute Big Reflective Eyes, Pixar Render, Complex Detail, Oil On Can.png"
    # img = cv2.imread(imgPath)
    s = SVGPath("C 0 0, 0.2 0.4, 1 1 C 0 0, 0.2 0.5, 1 1")
    s = SVGPath("m 113.60057 118.31007 c 0 0, 22.57108 -37.697446, 48.73247 0")
    s.standardize(118, 118)
    print(s.path)
    # s.standardize(10, 10)
    print(s.path)

    mask = generateMask((500, 500), s)
    # mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
    mask = np.array(mask, "uint8") * 255
    cv2.imshow("test", mask)
    cv2.waitKey(0)


if __name__ == "__main__":
    main()
