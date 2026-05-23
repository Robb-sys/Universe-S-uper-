import pygame
import moderngl
import glm

pygame.init()

pygame.display.set_mode(
    (1280, 720),
    pygame.OPENGL | pygame.DOUBLEBUF
)

ctx = moderngl.create_context()

clock = pygame.time.Clock()

running = True

camera_pos = glm.vec3(0, 0, 3)

def cameramovement(dt):

    global camera_pos

    keys = pygame.key.get_pressed()

    speed = 5

    if keys[pygame.K_w]:
        camera_pos.z -= speed * dt

    if keys[pygame.K_s]:
        camera_pos.z += speed * dt

    if keys[pygame.K_a]:
        camera_pos.x -= speed * dt

    if keys[pygame.K_d]:
        camera_pos.x += speed * dt

while running:

    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    cameramovement(dt)

    ctx.clear(0.1, 0.1, 0.1)

    pygame.display.flip()

pygame.quit()
