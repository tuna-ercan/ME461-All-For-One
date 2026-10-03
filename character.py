"""The four-legged character: leg kinematics, physics and drawing.

Physics is position based: every step the body falls, then contacts push the
body out of the rock. Because legs are rigid, a foot that is pressed into the
ground by its leg pushes the body away -> extending a grounded leg fast jumps.
Grounded feet on walkable slopes don't slide (static friction), so sweeping a
planted leg moves the body like walking. Sticky feet are anchored both ways,
so they can pull the body too (climb walls, hang from ledges).
"""
import math

import pygame

import config

V = pygame.Vector2


def wrap_deg(a):
    return (a + 180.0) % 360.0 - 180.0


def approach_angle(current, target, max_step):
    diff = wrap_deg(target - current)
    return current + max(-max_step, min(max_step, diff))


class Leg:
    def __init__(self, name, hip, side, thigh, bend, scale, stretch=1.0):
        self.name = name
        self.side = side                     # -1 left, +1 right
        self.hip = V(hip) * scale            # offset from body centre
        self.length = config.SEGMENT_LENGTH * stretch * scale
        # the shin stick stretches, the shoe below it keeps its size (see assets.stretch_leg)
        extra = (config.SHOE_TOP - config.LEG_PIVOT[1]) * (stretch - 1)
        self.foot_offset = V(side * config.FOOT_OFFSET[0], config.FOOT_OFFSET[1] + extra) * scale
        self.foot_radius = config.FOOT_RADIUS * scale
        self.rest = (thigh, bend)
        self.thigh, self.bend = thigh, bend  # current angles (outward convention)
        self.target_thigh, self.target_bend = thigh, bend

        self.sticky = False         # player wants this foot sticky (mouth open)
        self.anchor = None          # world point a sticky foot is glued to
        self.grip = None            # world point a grounded foot grips by friction
        self.contact = False

    # ------------------------------------------------------------ angles --
    def set_target(self, thigh, bend):
        self.target_thigh, self.target_bend = thigh, bend

    def update_angles(self, dt):
        step = config.LEG_MAX_SPEED * dt
        self.thigh = wrap_deg(approach_angle(self.thigh, self.target_thigh, step))
        self.bend = wrap_deg(approach_angle(self.bend, self.target_bend, step))

    def screen_angles(self):
        """Rotation (deg, pygame convention) of thigh and shin sprites."""
        return self.side * self.thigh, self.side * (self.thigh + self.bend)

    # -------------------------------------------------------- kinematics --
    def joints(self, body):
        """World positions of hip, knee and the foot (shoe) centre."""
        a_thigh, a_shin = self.screen_angles()
        hip = body + self.hip
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
        self.legs = {}
        for name in leg_names:
            hip, side, thigh, bend = config.LEGS[name]
            self.legs[name] = Leg(name, hip, side, thigh, bend, s, sprites.leg_stretch)
        self.reset(spawn)

    def reset(self, spawn):
        self.pos = V(spawn)
        self.vel = V()
        self.head_contact = False
        for leg in self.legs.values():
            leg.thigh, leg.bend = leg.rest
            leg.set_target(*leg.rest)
            leg.anchor = leg.grip = None
            leg.contact = False

    # ------------------------------------------------------------ physics --
    def update(self, dt, terrain):
        """One physics step. While a foot is glued the body is pinned and can't
        always get out of the way, so a leg could be forced into the rock. Then
        the step is redone with that leg held still: it stops at the rock.
        Feet may only sink in a little: free feet LEG_BLOCK_TOLERANCE, sticky
        feet STICKY_SINK (looks like gripping). Glued feet pushed in by another
        leg are kept within STICKY_SINK by the solver (_cap_sink)."""
        before = self._snapshot()
        depth0 = {leg.name: self._foot_depth(leg, terrain) for leg in self.legs.values()}
        old = {leg.name: (leg.thigh, leg.bend) for leg in self.legs.values()}
        for leg in self.legs.values():
            leg.update_angles(dt)
        new = {leg.name: (leg.thigh, leg.bend) for leg in self.legs.values()}
        self._step(dt, terrain)

        sunk = self._sunk_feet(depth0, terrain)
        if not sunk or not any(leg.anchor is not None for leg in self.legs.values()):
            return
        hold = [leg for leg in sunk if new[leg.name] != old[leg.name]]
        if hold:
            self._restore(before)
            for leg in hold:
                leg.thigh, leg.bend = old[leg.name]
            self._step(dt, terrain)

    def _step(self, dt, terrain):
        for leg in self.legs.values():
            if not leg.sticky:
                leg.anchor = None
            elif leg.anchor is None:
                foot = leg.foot(self.pos)
                if terrain.distance(*foot) < leg.foot_radius + config.STICKY_GRAB_DIST:
                    leg.anchor = foot

        start = V(self.pos)
        self.vel.y += config.GRAVITY * dt
        self.vel *= max(0.0, 1.0 - config.AIR_DRAG * dt)
        self.pos += self.vel * dt

        for _ in range(config.SOLVER_ITERATIONS):
            for leg in self.legs.values():
                self._solve_foot(leg, terrain)
            self._solve_head(terrain)
        for _ in range(2):          # last word goes to the rock: no glued foot deeper than allowed
            for leg in self.legs.values():
                if leg.anchor is not None:
                    self._cap_sink(leg, terrain)

        self._update_contacts(terrain)
        self.vel = (self.pos - start) / dt
        if self.head_contact and not any(l.contact for l in self.legs.values()):
            self.vel *= max(0.0, 1.0 - config.HEAD_FRICTION * dt)
        if self.vel.length() > config.MAX_SPEED:
            self.vel.scale_to_length(config.MAX_SPEED)
        self.pos.x = min(max(self.pos.x, 0), terrain.width)
        self.pos.y = min(self.pos.y, terrain.height)

    def _snapshot(self):
        legs = {leg.name: (V(leg.anchor) if leg.anchor is not None else None,
                           V(leg.grip) if leg.grip is not None else None,
                           leg.contact) for leg in self.legs.values()}
        return V(self.pos), V(self.vel), self.head_contact, legs

    def _restore(self, snap):
        pos, vel, self.head_contact, legs = snap
        self.pos, self.vel = V(pos), V(vel)
        for leg in self.legs.values():
            anchor, grip, leg.contact = legs[leg.name]
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
            self.pos += (leg.anchor - foot) * config.STICKY_STIFFNESS
            self._cap_sink(leg, terrain)                 # ...but never deeper than STICKY_SINK
            return
        d = terrain.distance(*foot)
        if d >= leg.foot_radius:
            return
        n = terrain.normal(*foot)
        self.pos += n * (leg.foot_radius - d)            # push out of the rock
        if -n.y < math.cos(math.radians(config.WALKABLE_SLOPE)):
            leg.grip = None                              # too steep, slide
            return
        foot = leg.foot(self.pos)
        if leg.grip is None:
            leg.grip = V(foot)
        tangent = V(-n.y, n.x)
        self.pos += tangent * (leg.grip - foot).dot(tangent)   # static friction

    def _cap_sink(self, leg, terrain):
        """Push the body so this glued foot is at most STICKY_SINK inside the rock."""
        foot = leg.foot(self.pos)
        excess = leg.foot_radius - config.STICKY_SINK - terrain.distance(*foot)
        if excess > 0:
            self.pos += terrain.normal(*foot) * excess

    def _solve_head(self, terrain):
        d = terrain.distance(*self.pos)
        self.head_contact = d < self.head_radius + config.CONTACT_EPS
        if d < self.head_radius:
            self.pos += terrain.normal(*self.pos) * (self.head_radius - d)

    def _update_contacts(self, terrain):
        for leg in self.legs.values():
            foot = leg.foot(self.pos)
            if leg.anchor is not None:
                leg.contact = True
                if foot.distance_to(leg.anchor) > config.STICKY_BREAK_DIST:
                    leg.anchor = None                    # torn off
                continue
            leg.contact = terrain.distance(*foot) < leg.foot_radius + config.CONTACT_EPS
            if not leg.contact:
                leg.grip = None

    # ------------------------------------------------------------ drawing --
    def draw(self, target, offset, debug=False):
        body = self.pos - offset
        sp = self.sprites
        for leg in self.legs.values():
            hip, knee, foot = leg.joints(body)
            a_thigh, a_shin = leg.screen_angles()
            sp.thigh[leg.side].draw(target, hip, a_thigh)
            shin = (sp.shin_stuck if leg.anchor is not None
                    else sp.shin_sticky if leg.sticky else sp.shin)
            shin[leg.side].draw(target, knee, a_shin)
            if debug:
                color = (0, 255, 0) if leg.anchor else (255, 255, 0) if leg.contact else (255, 0, 0)
                pygame.draw.circle(target, color, foot, leg.foot_radius, 1)
        sp.head.draw(target, body, 0)
        if debug:
            pygame.draw.circle(target, (255, 0, 255), body, self.head_radius, 1)
