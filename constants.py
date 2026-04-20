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
