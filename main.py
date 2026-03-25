import pygame
import sys
import math
import json
from random import random

pygame.init()

# ---------------------------
# CONFIG
# ---------------------------
WIDTH, HEIGHT = 800, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Race Dash Prototype")
clock = pygame.time.Clock()

# COLORS
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 140, 0)
RED = (255, 0, 0)
BLUE = (0, 120, 255)
WHITE = (230, 230, 230)
GRAY = (60, 60, 60)
DARK_GRAY = (30, 30, 30)

# ---------------------------
# STATE
# ---------------------------
state = {
    "rpm": 0,
    "speed": 0,
    "tempPercent": 0.6,
    "gForce": 0.0,
    "neutral": True,
    "oilWarning": True,
    "lap": {
        "count": 0,
        "current": 0,
        "last": 0,
        "best": 0
    },
    "gps": {
        "lat": 51.0,
        "lon": -0.1
    }
}

# TRACK DATA
laps = []
currentLapPoints = []
bestLapIndex = -1
lastLapColor = WHITE

trackRect = pygame.Rect(20, 140, 300, 300)

# ---------------------------
# GLOBAL SIM STATE (FIXED)
# ---------------------------
gpsAngle = 0
rpmDirection = 1

# ---------------------------
# JSON INPUT
# ---------------------------
def update_from_json(data):
    for key in data:
        if key in state:
            if isinstance(state[key], dict):
                state[key].update(data[key])
            else:
                state[key] = data[key]

# ---------------------------
# DEMO DATA
# ---------------------------
def demo_data(dt):
    global gpsAngle, rpmDirection, bestLapIndex, lastLapColor

    state["rpm"] += 120 * rpmDirection

    if state["rpm"] > 13000:
        state["rpm"] = 13000
        rpmDirection = -1
    if state["rpm"] < 2000:
        rpmDirection = 1

    state["speed"] = int(state["rpm"] / 130)

    state["tempPercent"] = 0.5 + math.sin(pygame.time.get_ticks() * 0.001) * 0.1

    # GPS movement
    gpsAngle += 0.01

    radius = 0.001 + 0.0002 * math.sin(pygame.time.get_ticks() * 0.0007)
    offset = 0.00015 * math.sin(gpsAngle * 3 + pygame.time.get_ticks() * 0.001)

    state["gps"]["lat"] = 51.0 + math.cos(gpsAngle) * (radius + offset)
    state["gps"]["lon"] = -0.1 + math.sin(gpsAngle) * (radius - offset)

    # G-force
    state["gForce"] += 0.02 * math.sin(pygame.time.get_ticks() * 0.002) + 0.02 * random() - 0.01
    state["gForce"] = max(0, min(state["gForce"], 3))

    # Lap timing
    state["lap"]["current"] += dt

    # Lap complete
    if gpsAngle >= math.pi * 2:
        gpsAngle = 0

        state["lap"]["count"] += 1
        state["lap"]["last"] = state["lap"]["current"]

        completed_lap = currentLapPoints.copy()
        currentLapPoints.clear()

        # store only last 3 laps
        laps.append(completed_lap)
        if len(laps) > 3:
            laps.pop(0)

        if state["lap"]["best"] == 0 or state["lap"]["current"] < state["lap"]["best"]:
            state["lap"]["best"] = state["lap"]["current"]
            bestLapIndex = len(laps) - 1
            lastLapColor = BLUE
        else:
            lastLapColor = RED

        state["lap"]["current"] = 0

# ---------------------------
# TRACK UPDATE
# ---------------------------
def update_track():
    lat = state["gps"]["lat"]
    lon = state["gps"]["lon"]
    currentLapPoints.append((lat, lon))

# ---------------------------
# DRAW FUNCTIONS
# ---------------------------
def draw_rpm_bar():
    rpmPercent = min(state["rpm"] / 13000, 1.0)

    barWidth = 500
    barX = (WIDTH - barWidth) // 2
    barY = 20

    segments = 20
    spacing = 5
    segmentWidth = (barWidth - (segments - 1) * spacing) // segments

    for i in range(segments):
        x = barX + i * (segmentWidth + spacing)

        if i < segments * rpmPercent:
            color = GREEN if i < 10 else ORANGE if i < 16 else RED
        else:
            color = DARK_GRAY

        pygame.draw.rect(screen, color, (x, barY, segmentWidth, 30), border_radius=4)

    if state["neutral"]:
        font = pygame.font.SysFont("Arial", 60, bold=True)
        surf = font.render("N", True, GREEN)
        screen.blit(surf, (barX + barWidth + 70, barY - 2))

    if state["oilWarning"]:
        font = pygame.font.SysFont("Arial", 24, bold=True)
        surf = font.render("LOW OIL PRESSURE!", True, RED)
        screen.blit(surf, (WIDTH//2 - surf.get_width()//2, barY + 50))

def draw_text():
    font_big = pygame.font.SysFont("Arial", 140)
    font_med = pygame.font.SysFont("Arial", 40)
    font_small = pygame.font.SysFont("Arial", 28)

    speedSurface = font_big.render(str(state["speed"]), True, WHITE)
    screen.blit(speedSurface, (WIDTH//2 - speedSurface.get_width()//2, 150))

    rpmSurface = font_med.render(str(state["rpm"]), True, GREEN)
    screen.blit(rpmSurface, (WIDTH//2 - rpmSurface.get_width()//2, 260))

    lap = state["lap"]

    screen.blit(font_small.render(f"Laps: {lap['count']}", True, WHITE), (20, 20))
    screen.blit(font_small.render(f"Current: {lap['current']:.2f}", True, WHITE), (20, 50))
    screen.blit(font_small.render(f"Last: {lap['last']:.2f}", True, lastLapColor), (20, 80))
    screen.blit(font_small.render(f"Best: {lap['best']:.2f}", True, BLUE), (20, 110))

def draw_track():
    pygame.draw.rect(screen, (20, 20, 20), trackRect, border_radius=12)
    pygame.draw.rect(screen, (0, 120, 0), trackRect, 2, border_radius=12)

    allPoints = []
    for lap in laps:
        allPoints.extend(lap)
    allPoints.extend(currentLapPoints)

    if len(allPoints) < 2:
        return

    lats = [p[0] for p in allPoints]
    lons = [p[1] for p in allPoints]

    minLat, maxLat = min(lats), max(lats)
    minLon, maxLon = min(lons), max(lons)

    latRange = maxLat - minLat or 0.00001
    lonRange = maxLon - minLon or 0.00001

    def convert(points):
        result = []
        for lat, lon in points:
            x = trackRect.x + int(((lon - minLon) / lonRange) * trackRect.width)
            y = trackRect.y + int((1 - (lat - minLat) / latRange) * trackRect.height)
            result.append((x, y))
        return result

    for i, lap in enumerate(laps):
        pts = convert(lap)
        if len(pts) > 1:
            color = BLUE if i == bestLapIndex else RED
            pygame.draw.lines(screen, color, False, pts, 3)

    currentPts = convert(currentLapPoints)
    if len(currentPts) > 1:
        pygame.draw.lines(screen, GREEN, False, currentPts, 3)
        pygame.draw.circle(screen, RED, currentPts[-1], 6)

def draw_temp_bar():
    x = WIDTH - 80
    y = 120
    h = 300

    temp = state["tempPercent"]
    color = GREEN if temp < 0.7 else ORANGE if temp < 0.9 else RED

    pygame.draw.rect(screen, GRAY, (x, y, 40, h), border_radius=8)

    filled = h * temp
    pygame.draw.rect(screen, color, (x, y + (h - filled), 40, filled), border_radius=8)

    font = pygame.font.SysFont("Arial", 24, bold=True)
    g = font.render(f"G: {state['gForce']:.2f}", True, WHITE)
    screen.blit(g, (x - 20, y + h + 10))

# ---------------------------
# MAIN LOOP
# ---------------------------
running = True
USE_DEMO = True

while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if USE_DEMO:
        demo_data(dt)
    else:
        json_input = '{"rpm":5000,"speed":80}'
        update_from_json(json.loads(json_input))

    update_track()

    screen.fill(BLACK)

    draw_rpm_bar()
    draw_text()
    draw_track()
    draw_temp_bar()

    pygame.display.flip()

pygame.quit()
sys.exit()