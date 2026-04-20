from math2 import Vector2, asVector2, Vector2Like, Matrix
import constants
import turtle

class Shape:
    """A shape to be drawn on screen. Defined by an array of Vectors."""

    def __init__(self, points: list[Vector2Like], closeLoop: bool = True):
        self.points: Vector2 = [asVector2(point) for point in points]
        self.closeLoop = closeLoop

    def first(self):
        return self.points[0].tuple()

    def getTransformed(self, transformationMatrix: Matrix) -> list[Vector2]:
        """Return this shape, transformed by the specified parameters"""

        return [transformationMatrix.transformVector2(point) for point in self.points]


def drawPoints(points: list[Vector2], closeLoop: bool):
    # Go to the starting position
    turtle.up()
    turtle.setposition(points[0].tuple())
    turtle.down()

    # Step along each point in the path
    for point in points[1:]:
        turtle.setposition(point.tuple())

    # Close the loop if applicable
    if closeLoop:
        turtle.setposition(points[0].tuple())


class DefinedShapes:
    """Contains pre-defined shapes, packaged here neatly"""

    # This defines the player model, and its detailing. Change these coordinates to adjust the player model
    PLAYER = [
        Shape(
            [
                (6, 0),
                (2, -1),
                (1, -2),
                (-4, -3),
                (-2, -2),
                (-3, -1),
                (-3, 1),
                (-2, 2),
                (-4, 3),
                (1, 2),
                (2, 1),
            ]
        ),
        Shape(
            [
                (-3, 1),
                (6, 0),
            ],
            closeLoop=False,
        ),
        Shape(
            [
                (-3, -1),
                (6, 0),
            ],
            closeLoop=False,
        ),
    ]

    # Straight line going right
    PROJECTILE = Shape([(0, 0), (constants.PROJECTILE_LENGTH, 0)], closeLoop=False)
