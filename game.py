"""
Initially adapted/learned from:
http://programarcadegames.com/python_examples/f.php?file=platform_scroller.py

Requires Python3, pygame package
"""

import pygame
import os

"""
Controls:
Left/Right arrows or A/D to move left/right. You gain speed over time, to a cap.
Up arrow, W, or SPACE to jump. Holding it makes you jump further.
S to skip level (some could be impossible with weird indents).
Q to quit.


Gameplay considerations:
Ideally the combination of SPEED_MAX, GRAV, GRAV_REDUCTION, and LINE_WIDTH 
should be such that the player can jump 2x indents near the apex of the a single jump
if they hold jump.
The player should also be able to use small hops to cross single lines at max speed
i.e _-_-_-_-_ you should be able to jump along the top platforms at max speed

TODOs/ideas:
Keep track of average velocity over the run
If hazards are introduced, keep track of furthest line reached
End of game screen with stats etc
Show controls on screen
Extract globals/constants to some config file
Other hazards (e.g. a small spike) for going over some line length
"""

# Global constants

# Colors
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Screen dimensions
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900

# Dimensions
LINE_WIDTH = 180
LINE_HEIGHT = 65

# Config
START_OFFSET = 700
RIGHT_LIMIT = 500
LEFT_LIMIT = 150
SPEED_MIN = 6
SPEED_MAX = 12
JUMP_FORCE = -13
ACCEL_X = .04
GRAV = 1
GRAV_REDUCTION = -(0.45 * GRAV)


class Player(pygame.sprite.Sprite):
    """ This class represents the rectangle at the bottom that the player controls. """
    width = 40
    height = 60

    def __init__(self):
        # Call the parent's constructor
        super().__init__()

        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        self.image = pygame.Surface([Player.width, Player.height])
        self.image.fill(RED)

        # Set a referance to the image rect.
        self.rect = self.image.get_rect()

        # Set speed vector of player
        self.change_x = 0
        self.change_y = 0

        # List of sprites we can bump against
        self.level = None

    def update(self):
        """ Move the player. """
        self.update_x()
        self.update_y()

    def update_x(self):
        # Move left/right
        self.rect.x += self.change_x
        # See if we hit anything
        block_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        for block in block_hit_list:
            # If we are moving right,
            # set our right side to the left side of the item we hit
            if self.change_x > 0:
                self.rect.right = block.rect.left
            elif self.change_x < 0:
                # Otherwise if we are moving left, do the opposite.
                self.rect.left = block.rect.right

    def update_y(self):
        # Add effect of gravity
        self.change_y += GRAV
        # Move up/down
        self.rect.y += self.change_y
        # Check and see if we hit anything
        block_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        for block in block_hit_list:

            # Reset our position based on the top/bottom of the object.
            if self.change_y > 0:
                self.rect.bottom = block.rect.top
            elif self.change_y < 0:
                self.rect.top = block.rect.bottom

            # Stop our vertical movement
            self.change_y = 0

        # See if we are on the ground.
        if self.rect.y >= SCREEN_HEIGHT - self.rect.height and self.change_y >= 0:
            self.change_y = 0
            self.rect.y = SCREEN_HEIGHT - self.rect.height

    def jump(self):
        """ Called when user hits 'jump' button. """
        if self.on_ground():
            self.change_y = JUMP_FORCE

    def float(self):
        if not self.on_ground():
            self.change_y += GRAV_REDUCTION

    def on_ground(self):
        # move down 2px and check collision. Apparently just 1px is buggy
        self.rect.y += 2
        platform_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        self.rect.y -= 2
        return len(platform_hit_list) > 0 or self.rect.bottom >= SCREEN_HEIGHT

    def acc_left(self):
        """ Called when the user hits the left arrow. """
        if self.change_x > -SPEED_MIN:
            self.change_x = -SPEED_MIN
        elif self.change_x <= -SPEED_MAX:
            self.change_x = -SPEED_MAX
        else:
            self.change_x -= ACCEL_X

    def acc_right(self):
        """ Called when the user hits the right arrow. """
        if self.change_x < SPEED_MIN:
            self.change_x = SPEED_MIN
        elif self.change_x >= SPEED_MAX:
            self.change_x = SPEED_MAX
        else:
            self.change_x += ACCEL_X

    def stop(self):
        """ Called when the user lets off the keyboard. """
        self.change_x = 0


class Platform(pygame.sprite.Sprite):
    """ Platform the user can jump on. Visualization of a line of code via indent"""
    def __init__(self, width, height):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()


class Level:
    def __init__(self, player, platforms, end):
        """ Represents the level
        :param player: Not entirely sure what this is needed for tbh
        :param platforms: All the platforms [width, height, x, y] representing lines
        :param end: Endpoint of the level
        """
        self.platform_list = pygame.sprite.Group()
        self.player = player
        self.level_limit = end
        for platform in platforms:
            block = Platform(platform[0], platform[1])
            block.rect.x = platform[2]
            block.rect.y = platform[3]
            block.player = self.player
            self.platform_list.add(block)

        # How far this world has been scrolled left/right
        self.world_shift = 0

    def update(self):
        """ Update everything on this level """
        self.platform_list.update()

    def draw(self, screen):
        """ Draw all background + platforms on this level """
        screen.fill(BLACK)  # Draw the background
        self.platform_list.draw(screen)  # Draw all the sprites/platforms

    def shift_world(self, shift_x):
        """ When the user moves left/right against the barrier
        and we need to scroll everything """

        # Keep track of the shift amount
        self.world_shift += shift_x

        # Go through all the sprites and shift
        for platform in self.platform_list:
            platform.rect.x += shift_x


def count_spaces(line):
    """ Number of leading spaces for a single line """
    return len(line) - len(line.lstrip())


def get_indent_standard(lines):
    """ Number of leading spaces for a single line """
    for line in lines:
        spaces = count_spaces(line)
        if spaces:
            return spaces
    return 2  # File had no idents, return arbitrary/unsused default


def indent(line, spaces_per_line):
    """ Indent level of a given line """
    return count_spaces(line) / spaces_per_line


def make_platform_dimensions(lines):
    """ Makes [width, height, x, y] formatted input for platform creation """
    indent_format = get_indent_standard(lines)
    heights = [indent(x, indent_format) * LINE_HEIGHT for x in lines]
    return [[LINE_WIDTH, y, START_OFFSET + (x * LINE_WIDTH), SCREEN_HEIGHT - y] for x, y in enumerate(heights)]


def make_levels(player):
    """ Loop over files to visualize and make levels out of them """
    dir = "./levels/"
    levels = []
    for file in os.listdir(dir):
        src_lines = []
        with open(dir + file) as src:
            src_lines = [x.replace("\t", "  ").rstrip() for x in src.readlines()]  # Replace tabs with 2 spaces
        sprites = make_platform_dimensions(src_lines)
        level_end = -(sprites[-1][2] + sprites[-1][0])
        levels.append(Level(player, sprites, level_end))
    return levels


def end_game():
    """ Exit for now. Later add end of game message """
    pygame.quit()
    exit(0)


def advance_level(current_level, current_level_no, levels, player):
    if current_level_no < len(levels) - 1:
        player.rect.x = LEFT_LIMIT
        current_level_no += 1
        current_level = levels[current_level_no]
        player.level = current_level
    else:
        end_game()
    return current_level


def main():
    """ Main Program """

    pygame.init()

    # Set the height and width of the screen and window title
    size = [SCREEN_WIDTH, SCREEN_HEIGHT]
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("Side-scrolling Platformer")

    # Create the player
    player = Player()

    # Create all the levels
    levels = make_levels(player)

    # Set the current level
    current_level_no = 0
    current_level = levels[current_level_no]

    active_sprite_list = pygame.sprite.Group()
    player.level = current_level

    player.rect.x = RIGHT_LIMIT - player.width  # Start at right scroll border
    player.rect.y = SCREEN_HEIGHT - player.rect.height  # Start on ground
    active_sprite_list.add(player)

    # Loop until the user clicks the close button.
    done = False

    # Used to manage how fast the screen updates
    clock = pygame.time.Clock()

    # Current status of directional keys
    r_down = False
    l_down = False
    u_down = False

    # Used to prevent auto-bunnyhopping. Active while holding up
    jump_lock = False

    """ Main program loop until user exits or game quits """
    while not done:
        skip = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

            # Check for pressed keys
            if event.type == pygame.KEYDOWN:
                key = event.key
                if key == pygame.K_LEFT or key == pygame.K_a:
                    l_down = True
                if key == pygame.K_RIGHT or key == pygame.K_d:
                    r_down = True
                if key == pygame.K_UP or key == pygame.K_w or key == pygame.K_SPACE:
                    u_down = True
                if key == pygame.K_q:
                    end_game()
                if key == pygame.K_s:
                    skip = True

            # Check for released keys
            if event.type == pygame.KEYUP:
                key = event.key
                if key == pygame.K_LEFT or key == pygame.K_a:
                    l_down = False
                if key == pygame.K_RIGHT or key == pygame.K_d:
                    r_down = False
                if key == pygame.K_UP or key == pygame.K_w  or key == pygame.K_SPACE:
                    u_down = False
                    jump_lock = False

        # Jump if on the ground, reduce grav if airborne (or haven't released UP)
        if u_down:
            if jump_lock:
                player.float()
            else:
                player.jump()
                jump_lock = True

        if r_down and l_down:
            pass  # Do nothing, but maintain speed
        elif r_down:
            player.acc_right()
        elif l_down:
            player.acc_left()
        else:
            player.stop()

        # Update the player.
        active_sprite_list.update()

        # Update items in the level
        current_level.update()

        # If the player gets near the right side, shift the world left (-x)
        if player.rect.right >= RIGHT_LIMIT:
            diff = player.rect.right - RIGHT_LIMIT
            player.rect.right = RIGHT_LIMIT
            current_level.shift_world(-diff)

        # If the player gets near the left side, shift the world right (+x)
        if player.rect.left <= LEFT_LIMIT:
            diff = LEFT_LIMIT - player.rect.left
            player.rect.left = LEFT_LIMIT
            current_level.shift_world(diff)

        # If the player gets to the end of the level, go to the next level
        current_position = player.rect.x + current_level.world_shift

        if skip or current_position < current_level.level_limit:
            current_level = advance_level(current_level, current_level_no, levels, player)
 
        # ALL CODE TO DRAW SHOULD GO BELOW THIS COMMENT
        current_level.draw(screen)
        active_sprite_list.draw(screen)
        # ALL CODE TO DRAW SHOULD GO ABOVE THIS COMMENT
 
        # Limit to 60 frames per second
        clock.tick(60)
 
        # Update the screen
        pygame.display.flip()
 
    # Be IDLE friendly. If you forget this line, the program will 'hang' on exit.
    pygame.quit()

if __name__ == "__main__":
    main()