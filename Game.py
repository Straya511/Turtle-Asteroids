# A couple friends were making an Asteroids clone in Python, using Turtle to render the graphics
# This is my version of the project (some inspiration taken from my friends code)

# To play the game, run the python program. Once you die, close the Turtle window to view your score (asteroids destroyed + time alive)

# Copyright 2026 Matthew Backhouse

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from pynput.keyboard import Listener, Key, KeyCode
from abc import ABC, abstractmethod
import math
import turtle
import time
import random


class Constants:
    # How far off screen the game simulation goes
    SCREEN_BUFFER = 50
    FRAME_TIME = 1 / 60
    SCREEN_WIDTH = 1200
    SCREEN_HEIGHT = 900

    # Player dimensions and stuff
    PLAYER_SCALE = 8
    # Scaled distance from the player centre at which asteroid collisions are registered
    PLAYER_HIT_RADIUS = 2

    # Player movement specifications
    PLAYER_SPEED = 0.5
    PLAYER_DRAG = 0.95
    PLAYER_ROTATION = 4

    # Projectile reload time (seconds)
    PROJECTILE_RELOAD_TIME = 0.00  # NOTE: Increase this to improve performance
    PROJECTILE_SPEED = 30
    # Arc in degrees the projectile will be shot in
    PROJECTILE_ARC_VARIANCE = 8
    PROJECTILE_LENGTH = 15

    # Asteroid instantiation rules
    ASTEROID_MAX_COUNT = 40  # NOTE: Reduce this to improve performance
    ASTEROID_ROTATION_VARIANCE = 2
    ASTEROID_SEGMENT_COUNT = 7  # NOTE: Reduce this to improve performance
    ASTEROID_SURFACE_VARIATION = 0.2
    ASTEROID_SNIPER_CHANCE = 1 / 20

    # Asteroid movement values
    ASTEROID_BASE_VELOCITY = 1.5
    ASTEROID_RANDOMISED_VELOCITY = 0.5
    ASTEROID_PERPENDICULAR_VELOCITY = 5
    ASTEROID_SNIPER_BOOST_FACTOR = 2.5

    # Asteroids shrink on damage, and get destroyed below a certain size
    ASTEROID_BASE_SCALE = 18
    ASTEROID_RANDOMISED_SCALE = 10
    ASTEROID_DAMAGE_SHRINKAGE = 0.8
    ASTEROID_MIN_SIZE = 15


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
    PROJECTILE = Shape([(0, 0), (Constants.PROJECTILE_LENGTH, 0)], closeLoop=False)


class GameObject(ABC):
    @abstractmethod
    def draw(self):
        pass

    @abstractmethod
    def update(self, game: "GameManager"):
        pass


class Entity(GameObject):
    def __init__(
        self,
        shapes: Shape | list[Shape],
        position: Vector2Like = 0,
        heading: float = 0,
        velocity: Vector2Like = 0,
        scale: Vector2Like = 1,
    ):
        if isinstance(shapes, list):
            self.shapes = shapes
        else:
            self.shapes = [shapes]
        self.position: Vector2 = asVector2(position)
        self.heading: float = heading
        self.velocity: Vector2 = asVector2(velocity)
        self.scale: Vector2 = asVector2(scale)

    def draw(self):
        """Draw the shape defined by this entity"""
        # Get the transformed points of the shape
        transformationMatrix = getTransformationMatrix(
            self.position, self.heading, self.scale
        )

        # Then draw each shape of this entity
        for shape in self.shapes:
            # Get the points
            transformed = shape.getTransformed(transformationMatrix)
            # Draw the points
            drawPoints(transformed, shape.closeLoop)

    def update(self, game: "GameManager"):
        pass

    def move(self):
        self.position += self.velocity

    def update_relative_velocity(self, velocity: Vector2):
        # Rotate the input vector to be relative to the entity
        self.velocity += velocity.rotated(self.heading)

    def checkInGameSpace(self, game: "GameManager"):
        """Verify the entity is on screen (plus a margin) and destroy itself if not"""

        # Check if the entity is off screen
        if (
            # Check sideways
            self.position.x > Constants.SCREEN_WIDTH / 2 + Constants.SCREEN_BUFFER
            or self.position.x < -Constants.SCREEN_WIDTH / 2 - Constants.SCREEN_BUFFER
            # Check vertically
            or self.position.y > Constants.SCREEN_HEIGHT / 2 + Constants.SCREEN_BUFFER
            or self.position.y < -Constants.SCREEN_HEIGHT / 2 - Constants.SCREEN_BUFFER
        ):
            self.destroy(game)

    def damage(self, game: "GameManager"):
        pass

    def destroy(self, game: "GameManager"):
        pass


class EntityCollection(GameObject):
    def __init__(self, entities: list[Entity]):
        self.entities = entities
        self.toBeRemoved: set[Entity] = set()

    def draw(self):
        for entity in self.entities:
            entity.draw()

    def update(self, game: "GameManager"):
        for entity in self.entities:
            entity.update(game)

        # Perform deletions when not iterating over list
        for entity in self.toBeRemoved:
            self.entities.remove(entity)
        self.toBeRemoved.clear()

    def add(self, entity: Entity):
        self.entities.append(entity)

    def remove(self, entity: Entity):
        # Use a set here, because in rare cases an object can be destroyed twice in one update cycle, and it only needs to be removed once
        self.toBeRemoved.add(entity)

    def __len__(self):
        return len(self.entities)


class Player(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lastProjectileTime = -100

        # Can shoot projectiles from multiple points on the player
        self.projectileSpawnPoints: list[Vector2] = [
            Vector2(1.5, 1.5),
            Vector2(1.5, -1.5),
        ]
        self.nextProjectileSpawn = 0

    def update(self, game: "GameManager"):
        self.processInput(game.keyboard_handler.inputs)
        self.move()
        self.apply_drag()
        self.checkScreenPosition(game)
        self.checkAsteroidCollisions(game)

    def processInput(self, inputs: list[Key]):
        for input in inputs:
            match input:
                case KeyCode(char="w"):
                    self.update_relative_velocity(
                        Vector2Std.FORWARD * Constants.PLAYER_SPEED
                    )

                case KeyCode(char="s"):
                    self.update_relative_velocity(
                        Vector2Std.BACKWARD * Constants.PLAYER_SPEED * 0.5
                    )

                case KeyCode(char="a"):
                    self.rotate(Constants.PLAYER_ROTATION)

                case KeyCode(char="d"):
                    self.rotate(-Constants.PLAYER_ROTATION)

                case Key.space:
                    curTime = time.perf_counter()
                    if (
                        curTime - self.lastProjectileTime
                        > Constants.PROJECTILE_RELOAD_TIME
                    ):
                        self.lastProjectileTime = curTime
                        self.shootProjectile(game)

    def rotate(self, degrees: float):
        self.heading += degrees

    def apply_drag(self):
        self.velocity *= Constants.PLAYER_DRAG

    def checkScreenPosition(self, game: "GameManager"):
        """Verify the player is on screen (plus a margin) and wrap around if not"""

        # Wrap sideways
        if self.position.x > Constants.SCREEN_WIDTH / 2 + Constants.SCREEN_BUFFER:
            self.position.x -= Constants.SCREEN_WIDTH + Constants.SCREEN_BUFFER * 2
        elif self.position.x < -Constants.SCREEN_WIDTH / 2 - Constants.SCREEN_BUFFER:
            self.position.x += Constants.SCREEN_WIDTH + Constants.SCREEN_BUFFER * 2

        # Wrap vertically
        if self.position.y > Constants.SCREEN_HEIGHT / 2 + Constants.SCREEN_BUFFER:
            self.position.y -= Constants.SCREEN_HEIGHT + Constants.SCREEN_BUFFER * 2
        elif self.position.y < -Constants.SCREEN_HEIGHT / 2 - Constants.SCREEN_BUFFER:
            self.position.y += Constants.SCREEN_HEIGHT + Constants.SCREEN_BUFFER * 2

    def shootProjectile(self, game: "GameManager"):
        # Get the point to shoot the projectile from
        matrix = getTransformationMatrix(self.position, self.heading, self.scale)
        spawnPoint = matrix.transformVector2(
            self.projectileSpawnPoints[self.nextProjectileSpawn]
        )

        # Loop to the next projectile point
        self.nextProjectileSpawn += 1
        if self.nextProjectileSpawn >= len(self.projectileSpawnPoints):
            self.nextProjectileSpawn = 0

        # Create the projectile!
        projHeading = (
            self.heading + (random.random() - 0.5) * Constants.PROJECTILE_ARC_VARIANCE
        )
        projectile = Projectile(spawnPoint, projHeading)
        game.addProjectile(projectile)

    def checkAsteroidCollisions(self, game: "GameManager"):
        for asteroid in game.asteroids.entities:
            # If the asteroid and player are closer than the sum of their radii, we were hit
            if (
                asteroid.position - self.position
            ).magnitude() < asteroid.scale.x + self.scale.x * Constants.PLAYER_HIT_RADIUS:
                game.stop()


class Asteroid(Entity):
    def __init__(
        self, pointCount: int, variance: float, angularVelocity: float, *args, **kwargs
    ):
        super().__init__(
            shapes=self.generateShape(pointCount, variance), *args, **kwargs
        )

        self.angularVelocity = angularVelocity

    def generateShape(self, pointCount: int, variance: float) -> Shape:
        """Generate a random spherical shape, with the given number of points
        Each point is moved in or out by the variance amount"""

        points: list[Vector2] = []
        startRot = random.random() * 2 * math.pi

        for i in range(pointCount):
            curRot = 2 * math.pi / pointCount * i + startRot
            curVariance = 1 + (random.random() - 0.5) * variance

            points.append(Vector2(math.sin(curRot), math.cos(curRot)) * curVariance)

        return Shape(points)

    def update(self, game: "GameManager"):
        self.move()
        self.heading += self.angularVelocity
        self.checkInGameSpace(game)

    def damage(self, game: "GameManager"):
        # Shrink by a bit, then destroy if too small
        self.scale -= Vector2Std.ONE * Constants.ASTEROID_DAMAGE_SHRINKAGE

        if self.scale.x < Constants.ASTEROID_MIN_SIZE:
            game.asteroidsDestroyed += 1
            self.destroy(game)

    def destroy(self, game):
        game.destroyAsteroid(self)


class Projectile(Entity):
    def __init__(self, position: Vector2Like, heading: float):
        super().__init__(DefinedShapes.PROJECTILE, position, heading)

        # Set the initial velocity, speed will be a constant value
        self.update_relative_velocity(Vector2(Constants.PROJECTILE_SPEED, 0))

    def update(self, game: "GameManager"):
        self.move()
        self.checkInGameSpace(game)
        self.checkAsteroidCollisions(game)

    def checkAsteroidCollisions(self, game: "GameManager"):
        """Check if this projectile will collide with any asteroids in the next time step"""

        # To check collisions, solve where the projectile line will collide with the asteroid sphere
        # Check if those points are within the projectiles movement in the next time step
        for asteroid in game.asteroids.entities:
            # Use the dot product to check if the Asteroid is in front of the projectile before running further calculations
            if self.velocity.dot(asteroid.position - self.position) > 0:
                continue

            epsilon = 0.00001

            # Get basic information
            avgRadius = asteroid.scale.x

            # Line information
            relStart = self.position - asteroid.position
            relSecond = Vector2Std.FORWARD.rotated(self.heading) + relStart
            projDistance = Constants.PROJECTILE_LENGTH + self.velocity.magnitude()

            # Convert the line to Ax + By + C = 0 as per https://math.stackexchange.com/questions/422602/convert-two-points-to-line-eq-ax-by-c-0
            a = relStart.y - relSecond.y
            b = relSecond.x - relStart.x
            c = relStart.x * relSecond.y - relSecond.x * relStart.y

            # Calculate the points of intersection, as per https://cp-algorithms.com/geometry/circle-line-intersection.html
            x0 = -a * c / (a**2 + b**2)
            y0 = -b * c / (a**2 + b**2)
            if c**2 > avgRadius**2 * (a**2 + b**2) + epsilon:
                continue
            elif abs(c**2 - avgRadius**2 * (a**2 + b**2)) < epsilon:
                # If the distance between the collision point and projectile start is less than the projectile length and how far it will travel this frame, we hit the asteroid
                if (Vector2(x0, y0) - relStart).magnitude() < projDistance:
                    asteroid.damage(game)
                    # Destroy ourselves, and stop checking for further collisions
                    self.destroy(game)
                    break
            else:
                d = avgRadius**2 - c**2 / (a**2 + b**2)
                m = math.sqrt(d / (a**2 + b**2))
                ax = x0 + b * m
                bx = x0 - b * m
                ay = y0 - a * m
                by = y0 + a * m

                # If either point is within where the projectile will be next frame, its a hit!
                if (Vector2(ax, ay) - relStart).magnitude() < projDistance or (
                    Vector2(bx, by) - relStart
                ).magnitude() < projDistance:
                    asteroid.damage(game)
                    # Destroy ourselves, and stop checking for further collisions
                    self.destroy(game)
                    break

    def destroy(self, game: "GameManager"):
        game.destroyProjectile(self)


class InputHandler:
    def __init__(self):
        self.inputs: list[Key] = []
        self.listener = Listener(
            on_press=self._onPress, on_release=self._onRelease
        ).start()

    def _onPress(self, key: Key):
        if key not in self.inputs:
            self.inputs.append(key)

    def _onRelease(self, key: Key):
        if key in self.inputs:
            self.inputs.remove(key)


class GameManager:
    def __init__(self):
        self.keyboard_handler = InputHandler()
        self.gameObjs: list[Entity] = []

    def start(self):
        turtle.tracer(0)
        turtle.setup(Constants.SCREEN_WIDTH, Constants.SCREEN_HEIGHT)
        turtle.title("Asteroids! by Matthew")
        turtle.ht()

        self.gameRunning = True

        # Player is just another entity tracked by the game manager
        self.player = Player(shapes=DefinedShapes.PLAYER, scale=Constants.PLAYER_SCALE)
        self.gameObjs.append(self.player)

        # Add a empty entity which draws the play area, just in case the player makes the window larger
        # I could limit window size, but this feels neater
        left = -Constants.SCREEN_WIDTH / 2 - Constants.SCREEN_BUFFER
        top = Constants.SCREEN_HEIGHT / 2 + Constants.SCREEN_BUFFER
        right = left * -1
        bottom = top * -1
        self.gameObjs.append(
            Entity(Shape([(left, top), (right, top), (right, bottom), (left, bottom)]))
        )

        # Then setup collections for bullets and asteroids
        self.asteroids = EntityCollection([])
        self.gameObjs.append(self.asteroids)
        self.projectiles = EntityCollection([])
        self.gameObjs.append(self.projectiles)

        # Score counter (asteroids destroyed by the player)
        self.asteroidsDestroyed = 0

    def stop(self):
        self.gameRunning = False

        # Show the game window until the user closes it, stats will be shown after
        turtle.done()

    def update(self):
        self.spawnAsteroids()

        for entity in self.gameObjs:
            entity.update(self)

    def draw(self):
        # Get rid of anything already on screen
        turtle.clear()
        for entity in self.gameObjs:
            entity.draw()
        # Refresh the screen with all our pretty art
        turtle.update()

    def spawnAsteroids(self):
        """Spawn asteroids for the player to fight, as per the game rules"""

        # For now, just spawn an Asteroid per frame until we hit the cap
        if len(self.asteroids) < Constants.ASTEROID_MAX_COUNT:
            # Chose the direction the asteroid will be moving in
            direction = random.choice([1, -1])

            # Asteroids can start on the sides, or on the top/bottom
            if random.random() > 0.5:
                # Start on the side
                position = (
                    (Constants.SCREEN_WIDTH / 2 + Constants.SCREEN_BUFFER) * direction,
                    (random.random() - 0.5) * Constants.SCREEN_HEIGHT,
                )

                # Randomised velocity to the opposite from where we started
                velocity = (
                    -(
                        random.random() * Constants.ASTEROID_RANDOMISED_VELOCITY
                        + Constants.ASTEROID_BASE_VELOCITY
                    )
                    * direction,
                    (random.random() - 0.5) * Constants.ASTEROID_PERPENDICULAR_VELOCITY,
                )

            else:
                # Start on the top/bottom
                position = (
                    (random.random() - 0.5) * Constants.SCREEN_WIDTH,
                    (Constants.SCREEN_HEIGHT / 2 + Constants.SCREEN_BUFFER) * direction,
                )

                # Randomised velocity to the opposite from where we started
                velocity = (
                    (random.random() - 0.5) * Constants.ASTEROID_PERPENDICULAR_VELOCITY,
                    -(
                        random.random() * Constants.ASTEROID_RANDOMISED_VELOCITY
                        + Constants.ASTEROID_BASE_VELOCITY
                    )
                    * direction,
                )

            # Occasionally send an Asteroid directly towards the player (force them to move)
            if random.random() < Constants.ASTEROID_SNIPER_CHANCE:
                # Adjust the velocity to have the same magnitude, but directed towards the player position
                velocity = (
                    (game.player.position - asVector2(position)).normalise()
                    * asVector2(velocity).magnitude()
                    * Constants.ASTEROID_SNIPER_BOOST_FACTOR
                )

            # Randomise rotation (just for looks)
            angularVelocity = (
                random.random() - 0.5
            ) * Constants.ASTEROID_ROTATION_VARIANCE

            scale = (
                random.random() * Constants.ASTEROID_RANDOMISED_SCALE
                + Constants.ASTEROID_BASE_SCALE
            )

            self.asteroids.add(
                Asteroid(
                    Constants.ASTEROID_SEGMENT_COUNT,
                    Constants.ASTEROID_SURFACE_VARIATION,
                    angularVelocity,
                    position=position,
                    scale=scale,
                    velocity=velocity,
                )
            )

    def addProjectile(self, projectile: Projectile):
        self.projectiles.add(projectile)

    def destroyProjectile(self, projectile: Projectile):
        self.projectiles.remove(projectile)

    def destroyAsteroid(self, astroid: Asteroid):
        self.asteroids.remove(astroid)


if __name__ == "__main__":
    # Calculate some overall stats about frame performance
    totalFrames = 0
    totalFrameTime = 0

    game = GameManager()

    try:
        # Init the game with turtle functions
        game.start()

        lastFrameTime = -100  # Arbitrary value a long time ago

        while game.gameRunning:
            # Busy wait until its time to render the next frame
            currentTime = time.perf_counter()
            if currentTime - lastFrameTime > Constants.FRAME_TIME:
                # Track frame time from the start of the frame
                lastFrameTime = time.perf_counter()

                # Tell the game to update all entities
                game.update()
                # Then draw the game
                game.draw()

                # Do some performance tracking so I can keep an eye on things
                frameTime = time.perf_counter() - currentTime
                totalFrames += 1
                totalFrameTime += frameTime
                print(
                    f"Frame time {frameTime:.5f}\t Theoretical FPS {1 / frameTime:.1f}"
                )

    except turtle.Terminator:
        # window was closed, don't do anything yet
        pass

    print(
        f"Total frames: {totalFrames} Total frame time: {totalFrameTime: .5f} Average FPS: {totalFrames / totalFrameTime: .1f}"
    )

    print(
        f"""

--- GAME OVER ---
Asteroids destroyed: {game.asteroidsDestroyed}
Seconds survived: {totalFrames * Constants.FRAME_TIME: .0f}

Try again, I dare you...
"""
    )
