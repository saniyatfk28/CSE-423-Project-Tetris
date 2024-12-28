#tetris
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import sys
import time

# Game settings
class GameSettings:
    def __init__(self, width=10, height=20):
        self.GRID_WIDTH = width
        self.GRID_HEIGHT = height
        self.CELL_SIZE = 30
        self.SCREEN_WIDTH = self.GRID_WIDTH * self.CELL_SIZE + 200
        self.SCREEN_HEIGHT = self.GRID_HEIGHT * self.CELL_SIZE
        self.BACKGROUND_COLOR = (0.0, 0.2, 0.2)
        self.intensity_level = 0
        self.terminate_flag = False


# Tetromino definitions
SHAPES = {
    'I': [(0, 0), (0, 1), (0, 2), (0, 3)],
    'O': [(0, 0), (1, 0), (0, 1), (1, 1)],
    'T': [(0, 0), (1, 0), (2, 0), (1, 1)],
    'S': [(1, 0), (2, 0), (0, 1), (1, 1)],
    'Z': [(0, 0), (1, 0), (1, 1), (2, 1)],
    'J': [(0, 0), (0, 1), (1, 1), (2, 1)],
    'L': [(2, 0), (0, 1), (1, 1), (2, 1)],
    'BOMB': [(0, 0)]  # Special bomb block
}


class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.velocity_x = random.uniform(-2, 2)
        self.velocity_y = random.uniform(1, 4)
        self.lifetime = 1.0  # Seconds
        self.birth_time = time.time()


class TetrisGame:
    
    def __init__(self):
        self.settings = GameSettings()
        self.grid = [[0] * self.settings.GRID_WIDTH for _ in range(self.settings.GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.particles = []
        self.score = 0
        self.game_over = False
        self.fall_time = time.time()
        self.fall_speed = 1.0  # Seconds between automatic falls
        self.paused = False
        self.restart_button = (self.settings.SCREEN_WIDTH // 2 - 60, self.settings.SCREEN_HEIGHT // 2, 120, 30)
        self.quit_button = (self.settings.SCREEN_WIDTH // 2 - 60, self.settings.SCREEN_HEIGHT // 2 + 40, 120, 30)
        self.start_button = (self.settings.SCREEN_WIDTH // 2 - 60, self.settings.SCREEN_HEIGHT // 2 + 80, 120, 30)

    def midpoint_line(self, x1, y1, x2, y2):
        """Draw line using midpoint algorithm with GL_POINTS"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1

        glBegin(GL_POINTS)
        if dx > dy:
            steps = dx
            xi = 1 if x2 > x1 else -1
            d = (2 * dy) - dx
            while x != x2:
                glVertex2f(x, y)
                if d > 0:
                    y += 1 if y2 > y1 else -1
                    d -= 2 * dx
                d += 2 * dy
                x += xi
        else:
            steps = dy
            yi = 1 if y2 > y1 else -1
            d = (2 * dx) - dy
            while y != y2:
                glVertex2f(x, y)
                if d > 0:
                    x += 1 if x2 > x1 else -1
                    d -= 2 * dy
                d += 2 * dx
                y += yi
        glEnd()

    def draw_block(self, x, y, color=(1.0, 1.0, 1.0)):
        """Draw a single block using GL_POINTS"""
        glColor3f(*color)
        size = self.settings.CELL_SIZE

        # Draw block outline using midpoint line algorithm
        self.midpoint_line(x, y, x + size, y)
        self.midpoint_line(x + size, y, x + size, y + size)
        self.midpoint_line(x + size, y + size, x, y + size)
        self.midpoint_line(x, y + size, x, y)

    def new_piece(self):
        """Generate a new tetromino piece"""
        shape_name = random.choice(list(SHAPES.keys()))
        shape = SHAPES[shape_name]
        return {
            'shape': shape,
            'x': self.settings.GRID_WIDTH // 2 - 1,
            'y': 0,
            'type': shape_name
        }

    def create_particles(self, row):
        """Create particles for row clearing effect"""
        for x in range(self.settings.GRID_WIDTH):
            for _ in range(5):  # 5 particles per block
                self.particles.append(Particle(
                    x * self.settings.CELL_SIZE,
                    row * self.settings.CELL_SIZE
                ))

    def update_particles(self):
        """Update particle positions and remove dead particles"""
        current_time = time.time()
        self.particles = [p for p in self.particles
                          if current_time - p.birth_time < p.lifetime]

        for particle in self.particles:
            particle.x += particle.velocity_x
            particle.y += particle.velocity_y
            particle.velocity_y -= 0.1  # Gravity effect

    def draw_particles(self):
        """Draw all active particles"""
        glBegin(GL_POINTS)
        glColor3f(1.0, 1.0, 0.0)  # Yellow particles
        for particle in self.particles:
            glVertex2f(particle.x, particle.y)
        glEnd()

    def clear_rows(self):
        """Clear completed rows and apply gravity"""
        rows_cleared = 0
        y = self.settings.GRID_HEIGHT - 1
        while y >= 0:
            if all(self.grid[y]):
                self.create_particles(y)
                rows_cleared += 1
                # Move all rows above down
                for row in range(y, 0, -1):
                    self.grid[row] = self.grid[row - 1][:]
                self.grid[0] = [0] * self.settings.GRID_WIDTH
            else:
                y -= 1
        return rows_cleared

    def update_background(self):
        """Update background based on score/intensity"""
        intensity = min(self.score // 1000, 2)  # 0, 1, or 2
        if intensity != self.settings.intensity_level:
            self.settings.intensity_level = intensity
            self.settings.BACKGROUND_COLOR = (
                0.0,
                0.0,
                0.2 + (intensity * 0.2)
            )

    def bomb_effect(self, x, y):
        """Apply bomb block effect"""
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                new_x = x + dx
                new_y = y + dy
                if (0 <= new_x < self.settings.GRID_WIDTH and
                        0 <= new_y < self.settings.GRID_HEIGHT):
                    self.grid[new_y][new_x] = 0
        self.create_particles(y)  # Create explosion particles

    def move_piece(self, dx, dy):
        """Move the current piece if possible"""
        if not self.current_piece or self.game_over or self.paused:
            return False

        new_x = self.current_piece['x'] + dx
        new_y = self.current_piece['y'] + dy  # Fixed line - it was incomplete before

        # Check if the move is valid
        if self.is_valid_move(new_x, new_y, self.current_piece['shape']):
            self.current_piece['x'] = new_x
            self.current_piece['y'] = new_y
            return True
        else:
            print(f"Move to ({new_x}, {new_y}) is invalid!")
            return False


    def rotate_piece(self):
        if self.current_piece['type'] == "bomb":
            # Bomb blocks do not rotate
            return

        # Get the current shape and calculate the centroid
        current_shape = self.current_piece['shape']
        center_x = sum(x for x, _ in current_shape) / len(current_shape)
        center_y = sum(y for _, y in current_shape) / len(current_shape)

        # Calculate the new rotated shape
        new_shape = []
        for x, y in current_shape:
            rx, ry = x - center_x, y - center_y
            new_x = int(round(-ry + center_x))
            new_y = int(round(rx + center_y))
            new_shape.append((new_x, new_y))

        # Validate the rotation
        if self.is_valid_move(self.current_piece['x'], self.current_piece['y'], new_shape):
            self.current_piece['shape'] = new_shape
        else:
            # Simple wall-kick system: Try slight shifts if rotation fails
            offsets = [(1, 0), (-1, 0), (0, -1)]  # Right, Left, Down
            for dx, dy in offsets:
                if self.is_valid_move(
                    self.current_piece['x'] + dx, self.current_piece['y'] + dy, new_shape
                ):
                    self.current_piece['x'] += dx
                    self.current_piece['y'] += dy
                    self.current_piece['shape'] = new_shape
                    return

        # If rotation fails completely, do nothing
        print("Rotation invalid due to collision or out of bounds")

    def is_valid_move(self, x, y, shape):
        """Check if the move is valid."""
        for block_x, block_y in shape:
            grid_x = x + block_x
            grid_y = y + block_y

            # Check if the block is out of bounds
            if grid_x < 0 or grid_x >= self.settings.GRID_WIDTH or grid_y >= self.settings.GRID_HEIGHT:
                print(f"Block ({grid_x}, {grid_y}) is out of bounds!")
                return False

            # Check for collisions within the grid
            if grid_y >= 0:  # Ignore collision checks for blocks above the grid
                if self.grid[grid_y][grid_x]:
                    print(f"Block ({grid_x}, {grid_y}) is colliding with another block!")
                    return False

        return True

        

    def drop_piece(self):
        """Drop the current piece to the bottom"""
        while self.move_piece(0, 1):
            pass
        self.place_piece()

    def place_piece(self):
        """Place the current piece on the grid"""
        if not self.current_piece:
            return

        # Check if the current piece goes out of bounds or collides with existing blocks
        for x, y in self.current_piece['shape']:
            grid_x = self.current_piece['x'] + x
            grid_y = self.current_piece['y'] + y
            if grid_y < 0:  # If any block is above the top of the grid
                self.game_over = True
                return  # Exit early if game over

        # Place the piece on the grid
        for x, y in self.current_piece['shape']:
            grid_x = self.current_piece['x'] + x
            grid_y = self.current_piece['y'] + y
            if 0 <= grid_y < self.settings.GRID_HEIGHT:
                self.grid[grid_y][grid_x] = 1

        if self.current_piece['type'] == 'BOMB':
            self.bomb_effect(self.current_piece['x'], self.current_piece['y'])

        rows_cleared = self.clear_rows()
        self.score += rows_cleared * 100
        self.update_background()

        # Generate a new piece and check if it is valid
        self.current_piece = self.new_piece()

        # Check if the new piece can be placed at the top
        if not self.is_valid_move(self.current_piece['x'], self.current_piece['y'],self.current_piece['shape']):
            self.game_over = True


    def toggle_pause(self):
        """Toggle game pause state"""
        self.paused = not self.paused
        if not self.paused:
            self.fall_time = time.time()

    def update(self):
        """Update game state"""
        if self.game_over or self.paused:
            return

        current_time = time.time()
        if current_time - self.fall_time > self.fall_speed:
            if not self.move_piece(0, 1):
                self.place_piece()
            self.fall_time = current_time

        self.update_particles()
        glutPostRedisplay()

    def draw(self):
        """Main drawing function"""
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        # If the game is over, draw the game-over screen
        if self.game_over:
            print("Game Over! Showing menu.")  # Debug statement
            self.draw_game_over_menu()  # Draw the game-over menu
            glutSwapBuffers()
            return  # Skip drawing the game grid and pieces when game is over

        # Draw game elements if the game is not over
        self.draw_game_elements()
        glutSwapBuffers()

    def draw_game_elements(self):
        """Draw game elements like blocks, pieces, and particles"""
        glClearColor(*self.settings.BACKGROUND_COLOR, 1.0)

        # Draw border of the game area
        glColor3f(1.0, 1.0, 1.0)
        self.midpoint_line(0, 0, self.settings.GRID_WIDTH * self.settings.CELL_SIZE, 0)
        self.midpoint_line(self.settings.GRID_WIDTH * self.settings.CELL_SIZE, 0,
                           self.settings.GRID_WIDTH * self.settings.CELL_SIZE,
                           self.settings.GRID_HEIGHT * self.settings.CELL_SIZE)
        self.midpoint_line(self.settings.GRID_WIDTH * self.settings.CELL_SIZE,
                           self.settings.GRID_HEIGHT * self.settings.CELL_SIZE,
                           0, self.settings.GRID_HEIGHT * self.settings.CELL_SIZE)
        self.midpoint_line(0, self.settings.GRID_HEIGHT * self.settings.CELL_SIZE, 0, 0)

        # Draw grid
        for y in range(self.settings.GRID_HEIGHT):
            for x in range(self.settings.GRID_WIDTH):
                if self.grid[y][x]:
                    self.draw_block(
                        x * self.settings.CELL_SIZE,
                        y * self.settings.CELL_SIZE
                    )

        # Draw current piece
        if self.current_piece:
            for x, y in self.current_piece['shape']:
                self.draw_block(
                    (self.current_piece['x'] + x) * self.settings.CELL_SIZE,
                    (self.current_piece['y'] + y) * self.settings.CELL_SIZE,
                    (1.0, 0.0, 0.0) if self.current_piece['type'] == 'BOMB'
                    else (1.0, 1.0, 1.0)
                )

        # Draw particles
        self.draw_particles()

        # Force the drawing to be shown
        glFlush()

   
    def draw_button(self, x, y, width, height, text):
        """Draw a button with text"""
        glColor3f(0.0, 0.0, 1.0)  # Blue button color
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + width, y)
        glVertex2f(x + width, y + height)
        glVertex2f(x, y + height)
        glEnd()

        # Draw text on the button
        glColor3f(1.0, 1.0, 1.0)  # White text color
        self.draw_text(x + width // 4, y + height // 2, text, size=15)

    def draw_text(self, x, y, text, size=10):
        """Draw text at a specific position"""
        glPushMatrix()
        glTranslatef(x, y, 0)
        glScalef(1.0, 1.0, 0)
        
        # OpenGL has no native text rendering, we use GLUT to display text
        for c in text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
        
        glPopMatrix()

    def check_game_over(self):
        """Check if the game is over (e.g., pieces stacked up)"""
        if any(self.grid[0]):  # If the top row is full
            self.game_over = True
            print("Game Over!")
    def draw_game_over_menu(self):
        """Draw the game-over menu with options to start or quit"""
        glColor3f(1.0, 1.0, 1.0)
        
        # Display Game Over text
        self.draw_text(self.settings.SCREEN_WIDTH // 2 - 50, self.settings.SCREEN_HEIGHT // 3, "Game Over!", size=100)
        
        # Draw Start button
        self.draw_button(*self.start_button, "Start")

        # Draw Quit button
        self.draw_button(*self.quit_button, "Quit")

    def handle_mouse_click(self, button, state, x, y):
        """Handle mouse click events"""
        if self.game_over:
            if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
                # Check if the click is on the Start button
                if (self.start_button[0] <= x <= self.start_button[0] + self.start_button[2] and self.start_button[1] <= y <= self.start_button[1] + self.start_button[3]):
                    print("Starting new game...")
                    self.__init__()  # Reinitialize the game to start fresh
                # Check if the click is on the Quit button
                elif (self.quit_button[0] <= x <= self.quit_button[0] + self.quit_button[2] and self.quit_button[1] <= y <= self.quit_button[1] + self.quit_button[3]):
                    print("Quitting game...")
                    glutLeaveMainLoop()
                return

def keyboard(key, x, y):
    """Handle keyboard input"""
    global terminate_flag
    game = TetrisGame.instance

    if game.game_over:
        if key == b'r' or key == b'R':  # Restart game
            print("Restarting game...")  # Debug statement
            game.__init__()  # Reinitialize the game
        elif key == b'q' or key == b'Q':  # Quit game
            print("Quitting game...")  # Debug statement
            glutLeaveMainLoop()
        return

    if key == b'a' or key == b'A':  # Move left
        game.move_piece(-1, 0)
    elif key == b'd' or key == b'D':  # Move right
        game.move_piece(1, 0)
    elif key == b's' or key == b'S':  # Move down
        game.move_piece(0, 1)
    elif key == b'w' or key == b'W':  # Rotate
        game.rotate_piece()
    elif key == b' ':  # Space bar - drop piece
        game.drop_piece()
    elif key == b'p' or key == b'P':  # Pause
        game.toggle_pause()
    elif key == b'q' or key == b'Q':  # Quit
        terminate_flag = True
    
    if terminate_flag:
        try:
            glutDestroyWindow(glutGetWindow())  # Destroy the current GLUT window
        except Exception as e:
            print(f"Error while destroying the window: {e}")
        sys.exit()  # Exit the program



def special_keys(key, x, y):
    """Handle special keyboard input"""
    game = TetrisGame.instance

    if game.game_over or game.paused:
        return

    if key == GLUT_KEY_LEFT:
        game.move_piece(-1, 0)
    elif key == GLUT_KEY_RIGHT:
        game.move_piece(1, 0)
    elif key == GLUT_KEY_DOWN:
        game.move_piece(0, 1)
    elif key == GLUT_KEY_UP:
        game.rotate_piece()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)

    # Create game instance
    game = TetrisGame()
    TetrisGame.instance = game  # Store instance for keyboard handler

    # Set window size and position
    glutInitWindowSize(game.settings.SCREEN_WIDTH, game.settings.SCREEN_HEIGHT)
    glutInitWindowPosition(100, 100)  # Position the window on the screen
    glutCreateWindow(b"Tetris")

    # Initialize OpenGL settings
    glClearColor(0.0, 0.0, 0.2, 1.0)  # Set background color
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, game.settings.SCREEN_WIDTH, game.settings.SCREEN_HEIGHT, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)

    # Enable point size and smooth points
    glEnable(GL_POINT_SMOOTH)
    glPointSize(2.0)

    # Register callbacks
    glutDisplayFunc(game.draw)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutIdleFunc(game.update)
    glutMouseFunc(game.handle_mouse_click)  # Register mouse click event

    glutMainLoop()


def update_timer(value):
    """Timer function to trigger updates"""
    game = TetrisGame.instance
    game.update()
    glutTimerFunc(16, update_timer, 0)  # 60 FPS approximately


# Also modify the update method:
def update(self):
    """Update game state"""
    if self.game_over or self.paused:
        return

    current_time = time.time()
    if current_time - self.fall_time > self.fall_speed:
        if not self.move_piece(0, 1):
            self.place_piece()
        self.fall_time = current_time

    self.update_particles()
    self.check_game_over()
    glutPostRedisplay()  # Request a redraw


if __name__ == "__main__":
    main()