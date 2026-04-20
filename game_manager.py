from entities import Entity, EntityCollection, Player, Asteroid, Projectile
from graphics import Shape, DefinedShapes
from input_handler import InputHandler
from math2 import asVector2
import constants
import random
import turtle

class GameManager:
    def __init__(self):
        self.keyboard_handler = InputHandler()
        self.gameObjs: list[Entity] = []

    def start(self):
        turtle.tracer(0)
        turtle.setup(constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
        turtle.title("Asteroids! by Matthew")
        turtle.ht()

        self.gameRunning = True

        # Player is just another entity tracked by the game manager
        self.player = Player(shapes=DefinedShapes.PLAYER, scale=constants.PLAYER_SCALE)
        self.gameObjs.append(self.player)

        # Add a empty entity which draws the play area, just in case the player makes the window larger
        # I could limit window size, but this feels neater
        left = -constants.SCREEN_WIDTH / 2 - constants.SCREEN_BUFFER
        top = constants.SCREEN_HEIGHT / 2 + constants.SCREEN_BUFFER
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
        if len(self.asteroids) < constants.ASTEROID_MAX_COUNT:
            # Chose the direction the asteroid will be moving in
            direction = random.choice([1, -1])

            # Asteroids can start on the sides, or on the top/bottom
            if random.random() > 0.5:
                # Start on the side
                position = (
                    (constants.SCREEN_WIDTH / 2 + constants.SCREEN_BUFFER) * direction,
                    (random.random() - 0.5) * constants.SCREEN_HEIGHT,
                )

                # Randomised velocity to the opposite from where we started
                velocity = (
                    -(
                        random.random() * constants.ASTEROID_RANDOMISED_VELOCITY
                        + constants.ASTEROID_BASE_VELOCITY
                    )
                    * direction,
                    (random.random() - 0.5) * constants.ASTEROID_PERPENDICULAR_VELOCITY,
                )

            else:
                # Start on the top/bottom
                position = (
                    (random.random() - 0.5) * constants.SCREEN_WIDTH,
                    (constants.SCREEN_HEIGHT / 2 + constants.SCREEN_BUFFER) * direction,
                )

                # Randomised velocity to the opposite from where we started
                velocity = (
                    (random.random() - 0.5) * constants.ASTEROID_PERPENDICULAR_VELOCITY,
                    -(
                        random.random() * constants.ASTEROID_RANDOMISED_VELOCITY
                        + constants.ASTEROID_BASE_VELOCITY
                    )
                    * direction,
                )

            # Occasionally send an Asteroid directly towards the player (force them to move)
            if random.random() < constants.ASTEROID_SNIPER_CHANCE:
                # Adjust the velocity to have the same magnitude, but directed towards the player position
                velocity = (
                    (self.player.position - asVector2(position)).normalise()
                    * asVector2(velocity).magnitude()
                    * constants.ASTEROID_SNIPER_BOOST_FACTOR
                )

            # Randomise rotation (just for looks)
            angularVelocity = (
                random.random() - 0.5
            ) * constants.ASTEROID_ROTATION_VARIANCE

            scale = (
                random.random() * constants.ASTEROID_RANDOMISED_SCALE
                + constants.ASTEROID_BASE_SCALE
            )

            self.asteroids.add(
                Asteroid(
                    constants.ASTEROID_SEGMENT_COUNT,
                    constants.ASTEROID_SURFACE_VARIATION,
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
