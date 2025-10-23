from ursina import *

app = Ursina()

# Get screen resolution (approximate)
import ctypes
user32 = ctypes.windll.user32
screen_width = user32.GetSystemMetrics(0)
screen_height = user32.GetSystemMetrics(1)

window.size = (screen_width, screen_height)
window.borderless = True  # optional to remove window frame

# Your game code below...
from ursina import *
import math, random

app = Ursina()

window.fullscreen = True
window.color = color.rgb(120, 180, 255)  # Sky blue background


# =========================
#   PLAYER (RAY)
# =========================
class Ray(Entity):
    def __init__(self):
        super().__init__(
            position=(0, 1, 0),
            collider='box',
            origin_y=-0.5
        )

        self.speed = 5
        self.sprint_multiplier = 2
        self.charging = False
        self.tilt_angle = 0

        # --- Body ---
        self.torso = Entity(parent=self, model='cube', scale=(0.7, 1.1, 0.4), y=1.1, color=color.rgb(25, 25, 25))
        self.head = Entity(parent=self, model='sphere', scale=0.35, y=1.9, color=color.rgb(255, 240, 220))

        # Aura encompassing whole character
        self.aura = Entity(parent=self, model='sphere', scale=3, color=color.azure, alpha=0.2)

        # Energy streaks container
        self.streaks = []

    def update(self):
        # Stop movement if charging aura
        if not held_keys['control']:
            move = Vec3(
                held_keys['d'] - held_keys['a'],
                0,
                held_keys['w'] - held_keys['s']
            ).normalized()

            current_speed = self.speed
            if held_keys['shift']:
                current_speed *= self.sprint_multiplier

            forward = Vec3(math.sin(math.radians(camera.rotation_y)), 0, math.cos(math.radians(camera.rotation_y)))
            right = Vec3(forward.z, 0, -forward.x)
            direction = (forward * move.z + right * move.x).normalized()

            if direction.length() > 0:
                self.position += direction * current_speed * time.dt
                self.look_at(self.position + direction)
                self.rotation_x = 0
                self.rotation_z = 0

                # Character tilt (forwards when moving)
                target_tilt = 5
                if held_keys['shift']:
                    target_tilt = 10
                self.tilt_angle = lerp(self.tilt_angle, target_tilt, time.dt * 5)
                self.rotation_x = self.tilt_angle
            else:
                # Reset tilt when not moving
                self.tilt_angle = lerp(self.tilt_angle, 0, time.dt * 5)
                self.rotation_x = self.tilt_angle

        # Charging aura
        if held_keys['control']:
            self.charging = True
            self.aura.alpha = min(0.4, self.aura.alpha + time.dt * 2)
            self.aura.scale = 3 + 0.1 * math.sin(time.time() * 10)

            # Spawn energy streaks
            if random.random() < 0.1:
                offset = Vec3(random.uniform(-1,1), 0, random.uniform(-1,1))
                streak = Entity(parent=self, model='cube', scale=(0.05,0.2,0.05),
                                color=color.white, position=Vec3(0,0.5,0)+offset)
                self.streaks.append(streak)
        else:
            self.charging = False
            self.aura.alpha = max(0, self.aura.alpha - time.dt * 2)

        # Update streaks
        for streak in self.streaks:
            streak.y += 2 * time.dt
            streak.alpha -= 1.5 * time.dt
        # Remove invisible streaks
        self.streaks = [s for s in self.streaks if s.alpha > 0]


# =========================
#   CAMERA CONTROLLER
# =========================
class ThirdPersonCamera(Entity):
    def __init__(self, target):
        super().__init__()
        self.target = target
        self.camera_distance = 6.0
        self.rotation_y = 0.0
        self.rotation_x = 20.0
        self.sensitivity = 35
        self.min_pitch = -10
        self.max_pitch = 45
        self.min_height = 1.0
        mouse.locked = True
        invoke(self.reset_camera, delay=0.1)
        self.ui_box = None

    def reset_camera(self):
        self.rotation_y = self.target.rotation_y
        self.rotation_x = 20
        camera.position = self.target.world_position + Vec3(0, 1.5, -self.camera_distance)
        camera.look_at(self.target.world_position + Vec3(0, 1.3, 0))
        camera.rotation_z = 0

    def update(self):
        delta_x = mouse.velocity[0]
        delta_y = mouse.velocity[1]

        self.rotation_y -= delta_x * self.sensitivity
        self.rotation_x -= delta_y * self.sensitivity
        self.rotation_x = clamp(self.rotation_x, self.min_pitch, self.max_pitch)

        if held_keys['scroll up']:
            self.camera_distance = max(3.0, self.camera_distance - 0.25)
        if held_keys['scroll down']:
            self.camera_distance = min(10.0, self.camera_distance + 0.25)

        yaw_rad = math.radians(self.rotation_y)
        pitch_rad = math.radians(self.rotation_x)
        forward = Vec3(
            math.sin(yaw_rad) * math.cos(pitch_rad),
            math.sin(pitch_rad),
            math.cos(yaw_rad) * math.cos(pitch_rad)
        )

        target_cam_pos = self.target.world_position + Vec3(0, 1.5, 0) - forward * self.camera_distance
        target_cam_pos.y = max(target_cam_pos.y, self.min_height)
        camera.position = lerp(camera.position, target_cam_pos, 8 * time.dt)

        camera.rotation_x = self.rotation_x
        camera.rotation_y = self.rotation_y
        camera.rotation_z = 0
        camera.look_at(self.target.world_position + Vec3(0, 1.3, 0))

        # Toggle mouse + UI box with N key
        if held_keys['n']:
            mouse.locked = not mouse.locked
            if not self.ui_box:
                self.ui_box = Entity(parent=camera.ui, model='quad', color=color.gray,
                                     position=(-0.6, -0.4), scale=(0.7, 0.5), enabled=False)
            self.ui_box.enabled = not self.ui_box.enabled


# =========================
#   CLOUD SYSTEM
# =========================
class Cloud(Entity):
    def __init__(self, position):
        super().__init__(
            model='cube',
            color=color.rgba(255, 255, 255, 180),
            scale=(random.uniform(3, 7), 1.5, random.uniform(2, 6)),
            position=position,
            eternal=True,
            shadow=True
        )
        self.speed = random.uniform(0.3, 0.8)

    def update(self):
        self.x += self.speed * time.dt
        if self.x > 120:
            self.x = -120
            self.z = random.uniform(-100, 100)
            self.scale_x = random.uniform(3, 7)
            self.scale_z = random.uniform(2, 6)


def generate_clouds(num=25):
    clouds = []
    for _ in range(num):
        pos = Vec3(random.uniform(-100, 100), random.uniform(50, 70), random.uniform(-100, 100))
        clouds.append(Cloud(pos))
    return clouds


# =========================
#   UI BARS (HP, STAMINA, AURA)
# =========================
def create_ui_bars():
    bg_color = color.rgb(60, 60, 60)
    # Background rectangles
    bg_hp = Entity(parent=camera.ui, model='quad', color=bg_color, scale=(0.4, 0.03), position=(-0.5, 0.45))
    bg_stamina = Entity(parent=camera.ui, model='quad', color=bg_color, scale=(0.4, 0.03), position=(-0.5, 0.41))
    bg_aura = Entity(parent=camera.ui, model='quad', color=bg_color, scale=(0.4, 0.03), position=(-0.5, 0.37))

    # Bars themselves
    hp_bar = Entity(parent=camera.ui, model='quad', color=color.green, scale=(0.38, 0.025), position=(-0.5, 0.45))
    stamina_bar = Entity(parent=camera.ui, model='quad', color=color.yellow, scale=(0.38, 0.025), position=(-0.5, 0.41))
    aura_bar = Entity(parent=camera.ui, model='quad', color=color.azure, scale=(0.38, 0.025), position=(-0.5, 0.37))

    # Triangle caps (fixed)
    def add_triangle_cap(x, y, color_in):
        verts = [Vec3(0, 0, 0), Vec3(0.02, 0.0125, 0), Vec3(0.02, -0.0125, 0)]
        tris = [0, 1, 2]
        mesh = Mesh(vertices=verts, triangles=tris, mode='triangle')
        return Entity(parent=camera.ui, model=mesh, color=color_in, position=(x, y))

    add_triangle_cap(-0.45, 0.45, color.green)
    add_triangle_cap(-0.45, 0.41, color.yellow)
    add_triangle_cap(-0.45, 0.37, color.azure)


# =========================
#   WORLD SETUP
# =========================
ray = Ray()
camera_controller = ThirdPersonCamera(ray)

# Ground and lighting
ground = Entity(model='plane', texture='white_cube', color=color.gray, scale=(100, 1, 100), collider='box')
DirectionalLight(shadows=True).look_at(Vec3(1, -1, -1))

# Clouds
clouds = generate_clouds(35)

# UI bars
create_ui_bars()

# UI Text
Text(
    "WASD = Move | SHIFT = Sprint | CTRL = Charge Aura | Scroll = Zoom | N = Toggle Menu",
    origin=(0, -18),
    scale=1.1
)

app.run()
