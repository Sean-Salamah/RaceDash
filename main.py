import pygame
import sys
import math

pygame.init()


# SCREEN SETUP


width = 800
height = 480
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Race Dash Prototype")


# COLORS


black  = (0, 0, 0)
green  = (0, 255, 0)
orange = (255, 140, 0)
red    = (255, 0, 0)
blue   = (0, 120, 255)
white  = (230, 230, 230)
gray   = (60, 60, 60)
darkGray = (30, 30, 30)

clock = pygame.time.Clock()


# SIM DATA


rpm = 0
speed = 0
rpmDirection = 1
tempPercent = 0.6
gForce = 0.0

neutral = True
oilPressureWarning = True

lapCounter = 0
lapTime = 0
lastLapTime = 0
bestLapTime = 0
lastLapColor = white
bestLapIndex = -1



# GPS TRACK SYSTEM 


laps = []                  # Stores completed laps
currentLapPoints = []      # Points for active lap

baseLat = 51.0
baseLon = -0.1
gpsAngle = 0

trackRect = pygame.Rect(20, 140, 300, 300)   # Slightly moved down to avoid UI overlap


# MAIN LOOP


running = True
while running:

    deltaTime = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False


    # SIM ENGINE


    rpm += 120 * rpmDirection

    if rpm > 13000:
        rpm = 13000
        rpmDirection = -1

    if rpm < 2000:
        rpmDirection = 1

    speed = int(rpm / 130)

    tempPercent = 0.5 + (math.sin(pygame.time.get_ticks() * 0.001) * 0.1)


    # SIM GPS


    gpsAngle += 0.01
    radius = 0.001

    currentLat = baseLat + math.cos(gpsAngle) * radius
    currentLon = baseLon + math.sin(gpsAngle) * radius

    currentLapPoints.append((currentLat, currentLon))


    # LAP DETECTION


    lapTime += deltaTime

    if gpsAngle >= math.pi * 2:

        gpsAngle = 0
        lapCounter += 1

        lastLapTime = lapTime

        # Store completed lap
        laps.append(currentLapPoints.copy())
        currentLapPoints = []

        # Determine best lap
        if bestLapTime == 0 or lapTime < bestLapTime:
            bestLapTime = lapTime
            bestLapIndex = len(laps) - 1
            lastLapColor = green
        else:
            lastLapColor = red

        lapTime = 0


    # DRAW
    screen.fill(black)

  
    # RPM BAR
 
    rpmPercent = min(rpm / 13000, 1.0)

    barTotalWidth = 500
    barHeight = 30
    barX = (width - barTotalWidth) // 2
    barY = 20

    segments = 20
    spacing = 5
    segmentWidth = (barTotalWidth - (segments - 1) * spacing) // segments

    for i in range(segments):
        x = barX + i * (segmentWidth + spacing)

        if i < segments * rpmPercent:
            if i < 10:
                color = green
            elif i < 16:
                color = orange
            else:
                color = red
        else:
            color = darkGray

        pygame.draw.rect(screen, color, (x, barY, segmentWidth, barHeight), border_radius=4)

    # neutral indicator
    if neutral:
        neutralFont = pygame.font.SysFont("Arial", 60, bold=True)
        neutralSurface = neutralFont.render("N", True, green)
        screen.blit(neutralSurface, (barX + barTotalWidth + 70, barY - 2))

    # Low Oil Pressure Warning
    if oilPressureWarning:
        warningFont = pygame.font.SysFont("Arial", 24, bold=True)
        warningSurface = warningFont.render("LOW OIL PRESSURE!", True, red)
        screen.blit(warningSurface, (width//2 - warningSurface.get_width()//2, barY + 50 + barHeight + 10))

    # RPM NUMBER


    rpmFont = pygame.font.SysFont("Arial", 40)
    rpmSurface = rpmFont.render(str(rpm), True, green)
    screen.blit(rpmSurface, (width//2 - rpmSurface.get_width()//2, 70))


    # SPEED DISPLAY


    speedFont = pygame.font.SysFont("Arial", 140)
    speedSurface = speedFont.render(str(speed), True, white)
    screen.blit(speedSurface, (width//2 - speedSurface.get_width()//2, 150))

    # LAP INFO PANEL

    timeFont = pygame.font.SysFont("Arial", 28)

    screen.blit(timeFont.render(f"Laps: {lapCounter}", True, white), (20, 20))
    screen.blit(timeFont.render(f"Current: {lapTime:.2f}", True, white), (20, 50))
    screen.blit(timeFont.render(f"Last: {lastLapTime:.2f}", True, lastLapColor), (20, 80))
    screen.blit(timeFont.render(f"Best: {bestLapTime:.2f}", True, blue), (20, 110))


    # TRACK MAP


    pygame.draw.rect(screen, (20, 20, 20), trackRect, border_radius=12)
    pygame.draw.rect(screen, (0, 120, 0), trackRect, 2, border_radius=12)

    # Gather ALL points for scaling
    allPoints = []
    for lap in laps:
        allPoints.extend(lap)
    allPoints.extend(currentLapPoints)

    if len(allPoints) > 1:

        lats = [p[0] for p in allPoints]
        lons = [p[1] for p in allPoints]

        minLat = min(lats)
        maxLat = max(lats)
        minLon = min(lons)
        maxLon = max(lons)

        latRange = maxLat - minLat or 0.00001
        lonRange = maxLon - minLon or 0.00001

        def convertToScreen(points):
            screenPts = []
            for lat, lon in points:
                xNorm = (lon - minLon) / lonRange
                yNorm = (lat - minLat) / latRange
                x = trackRect.x + int(xNorm * trackRect.width)
                y = trackRect.y + int((1 - yNorm) * trackRect.height)
                screenPts.append((x, y))
            return screenPts

        # Draw completed laps
        for i, lap in enumerate(laps):
            pts = convertToScreen(lap)
            if len(pts) > 1:
                if i == bestLapIndex:
                    color = blue
                else:
                    color = orange
                pygame.draw.lines(screen, color, False, pts, 3)

        # Draw current lap
        currentPts = convertToScreen(currentLapPoints)
        if len(currentPts) > 1:
            pygame.draw.lines(screen, green, False, currentPts, 3)
            pygame.draw.circle(screen, red, currentPts[-1], 6)

               

    # TEMP BAR

    tempBarHeight = 300
    tempBarWidth = 40
    tempBarX = width - 80
    tempBarY = 120

    # Colour logic
    if tempPercent < 0.7:
        tempColor = green
    elif tempPercent < 0.9:
        tempColor = orange
    else:
        tempColor = red

    # G-Force display
    gForceFont = pygame.font.SysFont("Arial", 24, bold=True)
    gForceSurface = gForceFont.render(f"G: {gForce:.2f}", True, white)
    screen.blit(gForceSurface, (tempBarX - 20, tempBarY + tempBarHeight + 10))
    
    # Background
    pygame.draw.rect(screen, gray, 
                     (tempBarX, tempBarY, tempBarWidth, tempBarHeight), 
                     border_radius=8)

    # Filled amount
    filledHeight = tempBarHeight * tempPercent

    pygame.draw.rect(
        screen,
        tempColor,
        (
            tempBarX,
            tempBarY + (tempBarHeight - filledHeight),
            tempBarWidth,
            filledHeight
        ),
        border_radius=8
    )

    pygame.display.flip()

pygame.quit()
sys.exit()