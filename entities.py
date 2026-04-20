# from __future__ import annotations

from math2 import asVector2, Vector2, getTransformationMatrix, Vector2Like, Vector2Std
from pynput.keyboard import Key, KeyCode
from graphics import Shape, drawPoints
from abc import ABC, abstractmethod
from graphics import DefinedShapes
import constants
import random
import math
import time


class GameObject(ABC):
    @abstractmethod
    def draw(self):
        pass

    @abstractmethod
    def update(self, game):
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

    def update(self, game):
        pass

    def move(self):
        self.position += self.velocity

    def update_relative_velocity(self, velocity: Vector2):
        # Rotate the input vector to be relative to the entity
        self.velocity += velocity.rotated(self.heading)

    def checkInGameSpace(self, game):
        """Verify the entity is on screen (plus a margin) and destroy itself if not"""

        # Check if the entity is off screen
        if (
            # Check sideways
            self.position.x > constants.SCREEN_WIDTH / 2 + constants.SCREEN_BUFFER
            or self.position.x < -constants.SCREEN_WIDTH / 2 - constants.SCREEN_BUFFER
            # Check vertically
            or self.position.y > constants.SCREEN_HEIGHT / 2 + constants.SCREEN_BUFFER
            or self.position.y < -constants.SCREEN_HEIGHT / 2 - constants.SCREEN_BUFFER
        ):
            self.destroy(game)

    def damage(self, game):
        pass

    def destroy(self, game):
        pass


class EntityCollection(GameObject):
    def __init__(self, entities: list[Entity]):
        self.entities = entities
        self.toBeRemoved: set[Entity] = set()

    def draw(self):
        for entity in self.entities:
            entity.draw()

    def update(self, game):
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

    def update(self, game):
        self.processInput(game)
        self.move()
        self.apply_drag()
        self.checkScreenPosition(game)
        self.checkAsteroidCollisions(game)

    def processInput(self, game):
        inputs: list[Key] = game.keyboard_handler.inputs
        for input in inputs:
            match input:
                case KeyCode(char="w"):
                    self.update_relative_velocity(
                        Vector2Std.FORWARD * constants.PLAYER_SPEED
                    )

                case KeyCode(char="s"):
                    self.update_relative_velocity(
                        Vector2Std.BACKWARD * constants.PLAYER_SPEED * 0.5
                    )

                case KeyCode(char="a"):
                    self.rotate(constants.PLAYER_ROTATION)

                case KeyCode(char="d"):
                    self.rotate(-constants.PLAYER_ROTATION)

                case Key.space:
                    curTime = time.perf_counter()
                    if (
                        curTime - self.lastProjectileTime
                        > constants.PROJECTILE_RELOAD_TIME
                    ):
                        self.lastProjectileTime = curTime
                        self.shootProjectile(game)

    def rotate(self, degrees: float):
        self.heading += degrees

    def apply_drag(self):
        self.velocity *= constants.PLAYER_DRAG

    def checkScreenPosition(self, game):
        """Verify the player is on screen (plus a margin) and wrap around if not"""

        # Wrap sideways
        if self.position.x > constants.SCREEN_WIDTH / 2 + constants.SCREEN_BUFFER:
            self.position.x -= constants.SCREEN_WIDTH + constants.SCREEN_BUFFER * 2
        elif self.position.x < -constants.SCREEN_WIDTH / 2 - constants.SCREEN_BUFFER:
            self.position.x += constants.SCREEN_WIDTH + constants.SCREEN_BUFFER * 2

        # Wrap vertically
        if self.position.y > constants.SCREEN_HEIGHT / 2 + constants.SCREEN_BUFFER:
            self.position.y -= constants.SCREEN_HEIGHT + constants.SCREEN_BUFFER * 2
        elif self.position.y < -constants.SCREEN_HEIGHT / 2 - constants.SCREEN_BUFFER:
            self.position.y += constants.SCREEN_HEIGHT + constants.SCREEN_BUFFER * 2

    def shootProjectile(self, game):
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
            self.heading + (random.random() - 0.5) * constants.PROJECTILE_ARC_VARIANCE
        )
        projectile = Projectile(spawnPoint, projHeading)
        game.addProjectile(projectile)

    def checkAsteroidCollisions(self, game):
        for asteroid in game.asteroids.entities:
            # If the asteroid and player are closer than the sum of their radii, we were hit
            if (
                asteroid.position - self.position
            ).magnitude() < asteroid.scale.x + self.scale.x * constants.PLAYER_HIT_RADIUS:
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

    def update(self, game):
        self.move()
        self.heading += self.angularVelocity
        self.checkInGameSpace(game)

    def damage(self, game):
        # Shrink by a bit, then destroy if too small
        self.scale -= Vector2Std.ONE * constants.ASTEROID_DAMAGE_SHRINKAGE

        if self.scale.x < constants.ASTEROID_MIN_SIZE:
            game.asteroidsDestroyed += 1
            self.destroy(game)

    def destroy(self, game):
        game.destroyAsteroid(self)


class Projectile(Entity):
    def __init__(self, position: Vector2Like, heading: float):
        super().__init__(DefinedShapes.PROJECTILE, position, heading)

        # Set the initial velocity, speed will be a constant value
        self.update_relative_velocity(Vector2(constants.PROJECTILE_SPEED, 0))

    def update(self, game):
        self.move()
        self.checkInGameSpace(game)
        self.checkAsteroidCollisions(game)

    def checkAsteroidCollisions(self, game):
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
            projDistance = constants.PROJECTILE_LENGTH + self.velocity.magnitude()

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

    def destroy(self, game):
        game.destroyProjectile(self)
