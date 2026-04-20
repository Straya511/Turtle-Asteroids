# A couple friends were making an Asteroids clone in Python, using Turtle to render the graphics
# This is my version of the project (some inspiration taken from my friends code)

# To play the game, run the python program. Once you die, close the Turtle window to view your score (asteroids destroyed + time alive)

# Copyright 2026 Matthew Backhouse

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.



from game_manager import GameManager 
import constants
import turtle
import time




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
            if currentTime - lastFrameTime > constants.FRAME_TIME:
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
Seconds survived: {totalFrames * constants.FRAME_TIME: .0f}

Try again, I dare you...
"""
    )
