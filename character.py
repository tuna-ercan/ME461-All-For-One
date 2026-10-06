"""The four-legged character: leg kinematics, physics and drawing.

Physics is position based: every step the body falls, then contacts push the
body out of the rock. Because legs are rigid, a foot that is pressed into the
ground by its leg pushes the body away -> extending a grounded leg fast jumps.
Grounded feet on walkable slopes don't slide (static friction), so sweeping a
planted leg moves the body like walking. Sticky feet are anchored both ways,
so they can pull the body too (climb walls, hang from ledges).

Only the body (head) has a position and velocity. Legs have no mass: each is
just two angles (thigh, bend) that follow the player's arm. Where the feet are
follows from the body position plus those angles ("kinematics").
"""
import math

import pygame

import config

V = pygame.Vector2   # short name: V(x, y) is a 2D vector with +, -, *, rotate, length...


def wrap_deg(a):
    """Bring any angle into -180..180 (e.g. 270 -> -90), so 'the shortest way round' works."""
    return (a + 180.0) % 360.0 - 180.0


def approach_angle(current, target, max_step):
    """Move `current` towards `target` by at most `max_step` degrees, the short way round."""
    diff = wrap_deg(target - current)
    return current + max(-max_step, min(max_step, diff))


class Leg:
    def __init__(self, name, hip, side, thigh, bend, scale, stretch=1.0):
        self.name = name
        self.side = side                     # -1 left, +1 right
        self.hip = V(hip) * scale            # offset from body centre
        self.length = config.SEGMENT_LENGTH * stretch * scale   # hip -> knee distance
        # the shin stick stretches, the shoe below it keeps its size (see assets.stretch_leg)
        extra = (config.SHOE_TOP - config.LEG_PIVOT[1]) * (stretch - 1)
        # which way the toe points when the shin hangs down: outward normally (= side),
        # inward for legs in config.MIRRORED_SHOES (they point up, which flips it back out)
        self.shoe_side = -side if name in config.MIRRORED_SHOES else side
        # knee -> shoe centre while the shin hangs straight down; x follows the toe direction
        self.foot_offset = V(self.shoe_side * config.FOOT_OFFSET[0], config.FOOT_OFFSET[1] + extra) * scale
        self.foot_radius = config.FOOT_RADIUS * scale
        self.rest = (thigh, bend)            # pose used at (re)start
        self.thigh, self.bend = thigh, bend  # current angles (outward convention)
        self.target_thigh, self.target_bend = thigh, bend   # angles the player asks for

        self.sticky = False         # player wants this foot sticky (mouth open)
        self.anchor = None          # world point a sticky foot is glued to
        self.grip = None            # world point a grounded foot grips by friction
        self.anchor_on = self.grip_on = None   # moving part (rotor) the anchor/grip rides on
        self.contact = False        # foot touching the ground this step

    # ------------------------------------------------------------ angles --
    def set_target(self, thigh, bend):
        self.target_thigh, self.target_bend = thigh, bend

    def update_angles(self, dt):
        """Turn towards the target, at most LEG_MAX_SPEED deg/s. The limit smooths
        out jerky arm tracking and caps how hard a leg can kick."""
        step = config.LEG_MAX_SPEED * dt
        self.thigh = wrap_deg(approach_angle(self.thigh, self.target_thigh, step))
        self.bend = wrap_deg(approach_angle(self.bend, self.target_bend, step))

    def screen_angles(self):
        """Rotation (deg, pygame convention) of thigh and shin sprites."""
        # "outward" angles are mirrored for left legs: multiplying by side (-1 / +1)
        # turns them into one screen rotation. shin direction = thigh + bend.
        return self.side * self.thigh, self.side * (self.thigh + self.bend)

    # -------------------------------------------------------- kinematics --
    def joints(self, body):
        """World positions of hip, knee and the foot (shoe) centre."""
        a_thigh, a_shin = self.screen_angles()
        hip = body + self.hip
        # V(0, length) is the thigh hanging straight down; rotating it gives the
        # thigh's real direction. Same for the shin, starting at the knee.
        knee = hip + V(0, self.length).rotate(-a_thigh)
        foot = knee + self.foot_offset.rotate(-a_shin)
        return hip, knee, foot

    def foot(self, body):
        return self.joints(body)[2]


class Character:
    def __init__(self, sprites, spawn, leg_names=tuple(config.LEGS)):
        self.sprites = sprites
        s = sprites.scale
        self.head_radius = config.HEAD_RADIUS * s
        # only the legs someone controls (1 player = 2 legs, otherwise 4)
        self.legs = {}
        for name in leg_names:
            hip, side, thigh, bend = config.LEGS[name]
            self.legs[name] = Leg(name, hip, side, thigh, bend, s, sprites.leg_stretch)
        self.reset(spawn)

    def reset(self, spawn):
        """Back to the start: standing still at `spawn`, legs in their rest pose."""
        self.pos = V(spawn)          # body (head) centre in map pixels
        self.vel = V()               # px per second
        self.head_contact = False
        for leg in self.legs.values():
            leg.thigh, leg.bend = leg.rest
            leg.set_target(*leg.rest)
            leg.anchor = leg.grip = None
            leg.anchor_on = leg.grip_on = None
            leg.contact = False

    # ------------------------------------------------------------ physics --
    def update(self, dt, terrain):
        """One physics step. While a foot is glued the body is pinned and can't
        always get out of the way, so a leg could be forced into the rock. Then
        the step is redone with that leg held still: it stops at the rock.
        Feet may only sink in a little: free feet LEG_BLOCK_TOLERANCE, sticky
        feet STICKY_SINK (looks like gripping). Glued feet pushed in by another
        leg are kept within STICKY_SINK by the solver (_cap_sink)."""
        before = self._snapshot()                       # to undo this step if needed
        depth0 = {leg.name: self._foot_depth(leg, terrain) for leg in self.legs.values()}
        old = {leg.name: (leg.thigh, leg.bend) for leg in self.legs.values()}
        for leg in self.legs.values():
            leg.update_angles(dt)
        new = {leg.name: (leg.thigh, leg.bend) for leg in self.legs.values()}
        self._step(dt, terrain)

        # Did a moving leg drive its own foot into the rock while a foot is glued?
        sunk = self._sunk_feet(depth0, terrain)
        if not sunk or not any(leg.anchor is not None for leg in self.legs.values()):
            return
        hold = [leg for leg in sunk if new[leg.name] != old[leg.name]]
        if hold:
            # undo the step and redo it with those legs not moving: they stop at the rock
            self._restore(before)
            for leg in hold:
                leg.thigh, leg.bend = old[leg.name]
            self._step(dt, terrain)

    def _step(self, dt, terrain):
        # 0) glue and grip points on a moving part (windmill rotor) move with it
        for leg in self.legs.values():
            if leg.anchor is not None and leg.anchor_on is not None:
                leg.anchor = leg.anchor_on.carry(leg.anchor)
            if leg.grip is not None and leg.grip_on is not None:
                leg.grip = leg.grip_on.carry(leg.grip)

        # 1) sticky feet: glue to the rock when close enough; let go when not sticky
        for leg in self.legs.values():
            if not leg.sticky:
                leg.anchor = None
            elif leg.anchor is None:
                foot = leg.foot(self.pos)
                if terrain.distance(*foot) < leg.foot_radius + config.STICKY_GRAB_DIST:
                    leg.anchor = foot
                    leg.anchor_on = terrain.mover_at(*foot)   # None = still rock

        # 2) predict: gravity speeds the body up, drag slows it a little, then move
        start = V(self.pos)
        self.vel.y += config.GRAVITY * dt                 # +y is down on screen
        self.vel *= max(0.0, 1.0 - config.AIR_DRAG * dt)
        self.pos += self.vel * dt

        # 3) solve: fix contacts by moving the body. Each fix can disturb another,
        #    so go round all of them a few times (Gauss-Seidel iterations).
        for _ in range(config.SOLVER_ITERATIONS):
            for leg in self.legs.values():
                self._solve_foot(leg, terrain)
            self._solve_head(terrain)
        for _ in range(2):          # last word goes to the rock: no glued foot deeper than allowed
            for leg in self.legs.values():
                if leg.anchor is not None:
                    self._cap_sink(leg, terrain)

        # 4) velocity = how far the body really moved this step / time.
        #    This is what turns a fast leg push into a jump: the push moved the
        #    body, so it now has speed and keeps flying after the foot leaves.
        self._update_contacts(terrain)
        self.vel = (self.pos - start) / dt
        if self.head_contact and not any(l.contact for l in self.legs.values()):
            self.vel *= max(0.0, 1.0 - config.HEAD_FRICTION * dt)   # head sliding on rock slows down
        if self.vel.length() > config.MAX_SPEED:
            self.vel.scale_to_length(config.MAX_SPEED)
        # stay inside the map horizontally and not below its bottom
        self.pos.x = min(max(self.pos.x, 0), terrain.width)
        self.pos.y = min(self.pos.y, terrain.height)

    def _snapshot(self):
        """Copy of everything _step changes, so a step can be undone."""
        legs = {leg.name: (V(leg.anchor) if leg.anchor is not None else None,
                           V(leg.grip) if leg.grip is not None else None,
                           leg.contact, leg.anchor_on, leg.grip_on) for leg in self.legs.values()}
        return V(self.pos), V(self.vel), self.head_contact, legs

    def _restore(self, snap):
        pos, vel, self.head_contact, legs = snap
        self.pos, self.vel = V(pos), V(vel)
        for leg in self.legs.values():
            anchor, grip, leg.contact, leg.anchor_on, leg.grip_on = legs[leg.name]
            leg.anchor = V(anchor) if anchor is not None else None
            leg.grip = V(grip) if grip is not None else None

    def _foot_depth(self, leg, terrain):
        """How far the foot circle is inside the rock (<= 0: outside)."""
        return leg.foot_radius - terrain.distance(*leg.foot(self.pos))

    def _sunk_feet(self, depth0, terrain):
        """Feet deeper in the rock than allowed and deeper than before this step."""
        out = []
        for leg in self.legs.values():
            limit = config.STICKY_SINK if leg.sticky else config.LEG_BLOCK_TOLERANCE
            d = self._foot_depth(leg, terrain)
            if d > max(limit, depth0[leg.name]) + 0.05:   # no creeping in, step by step
                out.append(leg)
        return out

    def _solve_foot(self, leg, terrain):
        foot = leg.foot(self.pos)
        if leg.anchor is not None:                       # sticky: pull or push
            # move the body part of the way so the foot gets back to its glue point
            self.pos += (leg.anchor - foot) * config.STICKY_STIFFNESS
            self._cap_sink(leg, terrain)                 # ...but never deeper than STICKY_SINK
            return
        d = terrain.distance(*foot)                      # distance of the shoe centre to rock
        if d >= leg.foot_radius:                         # shoe circle fully in the air: nothing to do
            return
        n = terrain.normal(*foot)
        self.pos += n * (leg.foot_radius - d)            # push out of the rock
        # Friction only on walkable ground: -n.y is how much the surface faces up
        # (1 = flat floor, 0 = vertical wall). Steeper than WALKABLE_SLOPE: slide.
        # A moving part (windmill rotor) has its own, much smaller limit, so a
        # non-sticky foot slips off it easily (glued feet never get here).
        mover = terrain.mover_at(*foot) if terrain.movers else None
        slope = mover.walkable_slope if mover is not None else config.WALKABLE_SLOPE
        if -n.y < math.cos(math.radians(slope)):
            leg.grip = None                              # too steep, slide
            return
        foot = leg.foot(self.pos)
        if leg.grip is None:                             # first touch: remember where
            leg.grip = V(foot)
            leg.grip_on = mover                          # standing on the rotor: grip rides along
        # tangent = along the surface. Move the body so the foot does not slide
        # along the surface away from its grip point. If the leg sweeps backwards,
        # the foot stays put and the BODY moves forward instead = walking.
        tangent = V(-n.y, n.x)
        self.pos += tangent * (leg.grip - foot).dot(tangent)   # static friction

    def _cap_sink(self, leg, terrain):
        """Push the body so this glued foot is at most STICKY_SINK inside the rock."""
        foot = leg.foot(self.pos)
        excess = leg.foot_radius - config.STICKY_SINK - terrain.distance(*foot)
        if excess > 0:
            self.pos += terrain.normal(*foot) * excess

    def _solve_head(self, terrain):
        """The head is a circle too: push it out of the rock like a foot (no friction)."""
        d = terrain.distance(*self.pos)
        self.head_contact = d < self.head_radius + config.CONTACT_EPS
        if d < self.head_radius:
            self.pos += terrain.normal(*self.pos) * (self.head_radius - d)

    def _update_contacts(self, terrain):
        """After solving: which feet touch the ground, and tear off over-stretched glue."""
        for leg in self.legs.values():
            foot = leg.foot(self.pos)
            if leg.anchor is not None:
                leg.contact = True
                if foot.distance_to(leg.anchor) > config.STICKY_BREAK_DIST:
                    leg.anchor = None                    # torn off
                continue
            leg.contact = terrain.distance(*foot) < leg.foot_radius + config.CONTACT_EPS
            if not leg.contact:
                leg.grip = None                          # lifted: forget the friction point

    # ------------------------------------------------------------ drawing --
    def draw(self, target, offset, debug=False):
        body = self.pos - offset                         # map position -> screen position
        sp = self.sprites
        for leg in self.legs.values():                   # legs first, so the head covers the hips
            hip, knee, foot = leg.joints(body)
            a_thigh, a_shin = leg.screen_angles()
            sp.thigh[leg.side].draw(target, hip, a_thigh)
            # shoe colour: purple = glued to rock, green = sticky in the air, red = normal
            shin = (sp.shin_stuck if leg.anchor is not None
                    else sp.shin_sticky if leg.sticky else sp.shin)
            shin[leg.shoe_side].draw(target, knee, a_shin)
            if debug:   # F1: collision circles (green glued, yellow touching, red in air)
                color = (0, 255, 0) if leg.anchor else (255, 255, 0) if leg.contact else (255, 0, 0)
                pygame.draw.circle(target, color, foot, leg.foot_radius, 1)
        sp.head.draw(target, body, 0)
        if debug:
            pygame.draw.circle(target, (255, 0, 255), body, self.head_radius, 1)
