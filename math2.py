import math


class Vector2:
    __slots__ = ("x", "y")

    def __init__(self, x_component: float, y_component: float):
        self.x = x_component
        self.y = y_component

    def clamp(self, maxLength: float):
        length = self.magnitude()

        if length > maxLength:
            factor = maxLength / length
            self.x *= factor
            self.y *= factor

    def normalise(self):
        length = self.magnitude()
        self.x /= length
        self.y /= length

        return self

    def magnitude(self):
        return math.hypot(self.x, self.y)

    def rotated(self, degrees):
        sinComp = math.sin(math.radians(degrees))
        cosComp = math.cos(math.radians(degrees))
        return Vector2(
            self.x * cosComp - self.y * sinComp, self.x * sinComp + self.y * cosComp
        )

    def tuple(self) -> tuple[float, float]:
        return (self.x, self.y)

    def dot(self, other: "Vector2") -> float:
        """Compute the dot product between this and another vector"""
        return self.x * other.x + self.y * other.y

    def __add__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x + other.x, self.y + other.y)

        else:
            raise NotImplementedError

    def __sub__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x - other.x, self.y - other.y)

        else:
            raise NotImplementedError

    def __mul__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return Vector2(self.x * float(other), self.y * float(other))

        else:
            raise NotImplementedError

    def __str__(self):
        return f"({self.x}, {self.y})"


class Vector2Std:
    """Defines common vectors for convenience"""

    UP = Vector2(0, 1)
    DOWN = Vector2(0, -1)
    LEFT = BACKWARD = Vector2(-1, 0)
    RIGHT = FORWARD = Vector2(1, 0)
    ONE = Vector2(1, 1)


class Matrix:
    """Defines a matrix (grid of numbers). Normally you would use Numpy or similar, but that defeats the point of the exercise. Rows, then columns"""

    __slots__ = ("matrix", "rows", "cols")

    def __init__(self, matrix: list[list[float]]):
        self.matrix = matrix
        self.rows = len(matrix)
        self.cols = len(matrix[0])

        # Check the matrix is valid!
        self.verify()

    def verify(self):
        """Verify this matrix is correct, throw an exception if it broke"""
        for row in self.matrix:
            if len(row) != self.cols:
                raise Exception("Uneven row lengths. Fix your code.")

    def transformVector2(self, vector: Vector2) -> Vector2:
        """Use this matrix to transform a Vector2"""

        # To actually multiply the point, we need to make it a 1x3
        transformed = self * Matrix([[vector.x], [vector.y], [1]])
        # And then back to 1x2 (a vector 2) because its helpful
        return Vector2(transformed[0][0], transformed[1][0])

    def __add__(self, other):
        if not isinstance(other, Matrix):
            raise Exception("Can only add matrices with matrices")

        # Set the type of other to Matrix so we get type hinting
        other: Matrix = other

        # Matrices can only be added if they are the same size
        if self.rows != other.rows or self.cols != other.cols:
            raise Exception("Matrices are not the same size, cannot add")

        # Add the numbers together with a nasty looking list comprehension
        return Matrix(
            [
                [colPair[0] + colPair[1] for colPair in zip(rowPair[0], rowPair[1])]
                for rowPair in zip(self.matrix, other.matrix)
            ]
        )

    def __mul__(self, other):
        if not isinstance(other, Matrix):
            raise Exception("Can only multiply matrices with matrices")

        # Set the type of other to Matrix so we get type hinting
        other: Matrix = other

        # Because Matrix multiplication, these sizing rules must be followed
        if self.cols != other.rows:
            raise Exception("Matrices cannot be multiplied, dimension mismatch")

        matrixData: list[list[float]] = []

        # If you want to know how this works, consult Google on matrix multiplication
        for row in range(self.rows):
            newRow: list[float] = []
            for col in range(other.cols):
                value = 0
                for i in range(self.cols):
                    value += self[row][i] * other[i][col]
                newRow.append(value)
            matrixData.append(newRow)

        return Matrix(matrixData)

    def __getitem__(self, item):
        """Allows list like access to this class, simply return the actual matrix"""
        return self.matrix[item]

    def __str__(self):
        return str(self.matrix)


type Vector2Like = Vector2 | tuple[float | int, float | int] | list[
    float | int
] | Matrix | float | int


def asVector2(vectorLike: Vector2Like) -> Vector2:
    """Convert a Vector2 like object to an actual Vector2"""

    if isinstance(vectorLike, Vector2):
        # Just return itself, already in the correct format
        return vectorLike

    elif (isinstance(vectorLike, tuple) or isinstance(vectorLike, list)) and len(
        vectorLike
    ) >= 2:
        # For ordered collections, first value is x, second is y
        return Vector2(vectorLike[0], vectorLike[1])

    elif (
        isinstance(vectorLike, Matrix) and vectorLike.cols >= 1 and vectorLike.rows >= 2
    ):
        # A matrix by default will just be the top two values in the first column
        return Vector2(vectorLike[0][0], vectorLike[1][0])

    elif isinstance(vectorLike, int) or isinstance(vectorLike, float):
        # For single values, multiple that out by the unit vector
        return Vector2(vectorLike, vectorLike)

    else:
        raise Exception("Input is not like a Vector2 and cannot be converted")


def getTransformationMatrix(
    translation: Vector2, degrees: float = 0, scale: Vector2 = Vector2Std.ONE
) -> Matrix:
    """Return a matrix built from the specified dimensions"""

    # Build a transformation matrix for the specified input. Again, Google how this works "2d transformation matrix"
    sinComp = math.sin(math.radians(degrees))
    cosComp = math.cos(math.radians(degrees))
    # Translation and rotation matrix in one because its simple to build
    transRotMatrix = Matrix(
        [
            [cosComp, -sinComp, translation.x],
            [sinComp, cosComp, translation.y],
            [0, 0, 1],
        ]
    )
    scaleMatrix = Matrix([[scale.x, 0, 0], [0, scale.y, 0], [0, 0, 1]])

    # Final transformation matrix
    transformationMatrix = transRotMatrix * scaleMatrix

    return transformationMatrix
