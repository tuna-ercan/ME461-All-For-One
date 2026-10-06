"""All the written text of the code guide. Blocks:
("h1", title) new part/chapter on a new page   ("h2", title) section   ("h3", title) sub-heading
("p", text) paragraph   ("ul", [...]) bullets   ("ol", [...]) numbered   ("fig", file, caption[, width[, crop]])
("table", rows, widths[, mono cols])   ("note", text)   ("warn", text)   ("formula", text)   ("config",)
Markup in text: `code`, **bold**, *italic*.
"""

GAME = (30, 60, 1228, 692)   # crop box of the game panel inside a window screenshot

SECTIONS_BEFORE = [
    # ================================================================ PART I
    ("h1", "Part I - The big picture"),
    ("h2", "1. What the game is"),
    ("p", "**All For One** is a co-op climbing game. Up to four people stand in front of one webcam and together "
          "control one cartoon character with four legs. Every player's arm (shoulder and elbow) drives one of the "
          "character's legs (hip and knee). There are no buttons: you push the character up the mountain by "
          "moving your arms, and you make its shoes sticky by opening your mouth. The goal is to touch the flag "
          "with the character's head as fast as possible."),
    ("fig", "shot_game_mountain.png", "The game window: the game view on the left; on the right the camera "
                                      "picture and the whole map with the character (yellow dot). P2's mouth is open, so the bottom shoes are sticky - purple = glued to "
                                      "the rock, green = sticky but still in the air."),
    ("p", "Behind that simple idea there are four separate problems, and the code is organised around them:"),
    ("ul", ["**Seeing the players** - find every person's body joints and mouth in the webcam picture "
            "(`vision.py`, using two AI models).",
            "**Turning bodies into commands** - convert arm positions into leg angles and mouth openings into "
            "sticky feet (`player_state.py`, `game.py`).",
            "**Physics** - make a character with rigid legs fall, stand, walk, jump and climb on an arbitrary "
            "drawn landscape (`terrain.py`, `character.py`).",
            "**Showing it all** - menus, the game view that follows the character, the camera preview, "
            "fullscreen (`display.py`, `menu.py`, `game.py`, `preview.py`)."]),
    ("h2", "2. Running it"),
    ("p", "Once per computer, run the setup (details in chapter 13). It creates a private Python environment "
          "with the right package versions and downloads the AI models:"),
    ("table", [["System", "Set up once", "Then start the game"],
               ["Windows", "double-click `setup.bat`", "double-click `run.bat`"],
               ["Linux", "`./setup.sh`", "`./run.sh`"]], [0.2, 0.4, 0.4]),
    ("p", "Options can be added after `run.bat` / `./run.sh` (or after `python main.py` inside the environment):"),
    ("table", [["Option", "What it does"],
               ["(none)", "Normal game with webcam 0."],
               ["--source 1", "Use another webcam (or a video file path)."],
               ["--keyboard", "No camera: legs move with Q/A W/S E/D R/F U/J I/K O/L P/; keys, "
                              "hold 1-4 to open a player's mouth. Good for testing physics."],
               ["--debug", "Start with collision circles shown (same as pressing F1)."]],
     [0.25, 0.75], (0,)),
    ("p", "In the game: **F11** fullscreen, **F5** restart, **F1** collision circles, **Esc** back to the menu. "
          "On the title screen: **OPTIONS** (or O) to tune the game, **1P TEST** (or T) for the test screen."),
    ("h2", "3. The files"),
    ("p", "Every file has one job (the assignment asked for separate files per task and object-oriented code). "
          "The right column says which class or function to look for."),
    ("table", [["File", "Job", "Main contents"],
               ["main.py", "Entry point: read the command line, choose camera or keyboard", "`main()`"],
               ["app.py", "Create the window and switch between the screens", "`App`"],
               ["config.py", "Every tunable number in one place", "constants"],
               ["settings.py", "Which settings players may change, their safe ranges, settings.json",
                "`Setting`, `Settings`"],
               ["options_menu.py", "The Options screen (sliders, switches, live readout)", "`OptionsScene`"],
               ["display.py", "The one window: game panel + camera and map panels, scaling, fullscreen",
                "`Display`"],
               ["minimap.py", "The whole-map overview under the camera", "`MiniMap`"],
               ["menu.py", "Title page, player-count page, map page", "`Menu`"],
               ["ui.py", "Buttons, sliders, switches and outlined text",
                "`Button`, `MapButton`, `Slider`, `Toggle`, `draw_text`"],
               ["game.py", "The level: loop, physics steps, HUD, timer, finish, name entry",
                "`Game`, `apply_players`"],
               ["scoreboard.py", "Finish times with team names, saved in scores.json", "`ScoreBoard`"],
               ["test_scene.py", "1-player test screen (no physics)", "`TestScene`"],
               ["maps.py", "Load a map: scale it, find start point and flag", "`GameMap`, `load_maps`"],
               ["terrain.py", "Map picture + collision (signed distance field)", "`Terrain`"],
               ["windmill.py", "Windmill map: tower picture + spinning, solid rotor", "`Windmill`"],
               ["flag.py", "The goal flag: placement, touch test, drawing", "`Flag`"],
               ["viewport.py", "The game camera that follows the character", "`Viewport`, `view_size`"],
               ["character.py", "Legs, kinematics, physics, drawing of the character", "`Leg`, `Character`"],
               ["assets.py", "Character pictures: crop, scale, stretch, recolour, rotate", "`PivotSprite`, "
                                                                                          "`CharacterSprites`"],
               ["inputs.py", "Input interface + keyboard input", "`InputSource`, `KeyboardInput`"],
               ["vision.py", "Webcam thread: pose, faces, players, mouth, head tilt", "`VisionInput` and helpers"],
               ["player_state.py", "Player data + arm-angle maths", "`PlayerState`, `limb_poses`"],
               ["preview.py", "Draws skeletons and lips on the camera picture", "`PreviewRenderer`"],
               ["export_engine.py", "Builds the TensorRT engine", "script"],
               ["download_models.py", "Downloads both AI models, reports GPU/CPU (run by the setup)", "script"],
               ["setup.ps1 / setup.bat", "Windows setup: environment, packages, models", "script"],
               ["setup.sh", "Linux setup: environment, packages, models, system checks", "script"],
               ["run.bat / run.sh", "Start the game with the environment", "script"],
               ["requirements*.txt", "Pinned package versions: game / optional GPU / optional docs tools", "lists"],
               ["tools/docs/", "Rebuilds this PDF from the code (`make_docs.py`)", "scripts"],
               ["pose_and_face_test.py", "Your original pose + face experiment (not used by the game)", "script"]],
     [0.2, 0.52, 0.28], (0,)),
    ("p", "The `assets/` folder holds the pictures: `background*.png` (sky and far scenery), `foreground*.png` "
          "(the rock you collide with - its transparent pixels are air), the character parts `head.png`, "
          "`leg-part.png`, `leg-part-with-shoe.png`, `character-demo.png` (menu picture) and `flag.png`. The "
          "windmill map adds `map3-windmillbase.png` (the tower, only a picture) and `map3-windmillblade.png` "
          "(the rotor, solid); `map3-fullmapdemo.png` shows how the map looks assembled. The two "
          "AI model files `yolo26n-pose.pt` and `face_landmarker.task` download themselves on first run."),
    ("h2", "4. How the parts fit together"),
    ("fig", "fig_architecture.png", "Who creates and uses whom. Arrows point from the user to the thing it uses.",
     0.92),
    ("p", "Reading the diagram top-down: `main.py` creates an **input source** (camera or keyboard) and gives it to "
          "`App`. `App` creates the window (`Display`), loads the maps and creates the three **scenes** (Menu, "
          "Game, TestScene). A scene is a screen with its own loop. `App.run()` asks the menu what to do, runs that "
          "scene until it returns, and goes back to the menu."),
    ("p", "The game scene uses a `GameMap` (which owns a `Terrain` for collisions, a `Flag` and, on the "
          "windmill map, a `Windmill`), a `MiniMap` (the overview under the camera) and a `ScoreBoard` "
          "(finish times in scores.json), builds a "
          "`Character` (which uses `CharacterSprites` for its pictures) and a `Viewport` (the game camera). It "
          "never talks to the webcam directly - it only calls `input.get_players()`. That is the key design idea: "
          "**the game does not know whether a camera or a keyboard is behind the input**. Both classes inherit "
          "from `InputSource` and offer the same methods (`get_players`, `get_preview`, `set_num_players`, "
          "`close`). This is called an *interface*, and it is why keyboard mode was trivial to add."),
    ("h2", "5. One frame, start to finish"),
    ("p", "Two things run at the same time (two *threads*). The **vision thread** reads the webcam and runs the AI "
          "models as fast as it can (about 30-40 times per second). The **game thread** runs the game at a steady "
          "60 frames per second. They meet in one place: a small shared box with the newest results, protected by "
          "a *lock* so the game never reads a result while the vision thread is half-way through writing it."),
    ("fig", "fig_threads.png", "The two loops and the shared results between them."),
    ("p", "Why two threads? Running the AI models takes 20-110 ms per picture. If the game waited for them every "
          "frame, it would stutter at 9-30 FPS. With a separate thread the game always runs smoothly and simply "
          "uses the newest available result."),
    ("h3", "Start-up, in order"),
    ("ol", ["`main()` parses the command line and creates `VisionInput` - this loads the pose model (picking "
            "TensorRT, GPU or CPU), the face model, opens the webcam and starts the vision thread.",
            "`App.__init__` starts pygame, applies the player's saved settings from `settings.json` "
            "(chapter 12) and creates the `Display` (the window).",
            "`load_maps()` loads every map in `config.MAPS`: scales the pictures, computes the collision field, "
            "places the flag and finds the start point (about 2 seconds in total).",
            "The three scenes are created. `App.run()` shows the menu.",
            "The player picks PLAY, a player count and a map; `Game.run(players, map)` starts the level."]),
    ("h3", "Every game frame (Game.run)"),
    ("ol", ["`clock.tick(60)` waits so frames are 1/60 s apart and returns the real time since the last frame "
            "(`dt`).",
            "Keyboard/window events: Esc, F5, F1, F11, closing the window.",
            "`input.get_players()` returns one `PlayerState` per player (limb angles, mouth, head tilt).",
            "`apply_players` copies each controlling limb's angles into its leg as a *target*, and sets each "
            "leg's `sticky` flag from the mouth.",
            "Physics: `character.update()` three times with `dt/3` each (substeps).",
            "The viewport glides towards the character; the timer runs; the flag touch is checked.",
            "Drawing: map part, flag, character, knee dots, texts, timer, and `display.present()` shows it."]),
    ("h2", "6. Coordinates, units and conventions"),
    ("p", "Most confusion in game code comes from coordinates. These are the conventions used everywhere here:"),
    ("ul", ["**Map pixels** are the unit of the world. All maps are scaled so the mountain map is 2164 px tall "
            "(`MAP_HEIGHT`); positions, speeds (px/s) and gravity (px/s^2) are in map pixels.",
            "**y points down** (screen convention). Gravity is `+y`; \"up\" means a smaller y. The HUD height % is "
            "computed as `map height - y`.",
            "**Three sizes of picture**: the *map* (e.g. 4096 x 2164), the *canvas* (1365 x 721, the size the "
            "scenes draw at = what the viewport shows) and the *window* (whatever fits your screen). "
            "`display.present()` scales canvas to window; `display.to_canvas()` converts mouse clicks back.",
            "**Screen position = map position - viewport position.** That is why every `draw()` gets an `offset`.",
            "**Angles are degrees.** Leg and arm angles use the *outward* convention below.",
            "**Colours**: pygame uses (R, G, B), OpenCV uses (B, G, R). `config.PLAYER_COLORS_BGR` is the "
            "master list and the RGB list is made by reversing each tuple."]),
    ("fig", "fig_angles.png", "Left: a leg is two angles. Right: left legs are mirrored so 'away from the body' is "
                              "positive on both sides."),
    ("p", "A leg is fully described by two numbers: **thigh** = the hip angle measured from straight down "
          "(0 = hanging, 90 = sideways, 180 = up) and **bend** = how much the shin turns relative to the thigh. "
          "The *same* two numbers are measured on the player's arm (shoulder angle and elbow angle), which is why "
          "an arm can drive a leg directly: arm hanging down -> leg hanging down, arm raised -> leg raised."),
    ("p", "To draw or compute a leg on screen, the outward angle is multiplied by the leg's `side` (-1 left, +1 "
          "right) to get a normal screen rotation (`Leg.screen_angles`)."),

    # ================================================================ PART II
    ("h1", "Part II - The core systems"),
    ("h2", "7. Terrain and collision: the signed distance field"),
    ("p", "The landscape is a drawing, not a set of boxes or polygons, so collision must work on pixels. The "
          "foreground picture's transparency decides what is solid: a pixel more than half opaque is rock. "
          "`Terrain` turns that yes/no mask into a **signed distance field (SDF)**: a table with one number per "
          "pixel telling how far that pixel is from the nearest rock surface - positive in the air, negative "
          "inside rock, zero on the surface."),
    ("fig", "fig_sdf.png", "A part of the mountain. Right: the distance field; the black line is distance 0 (the "
                           "surface), dashed lines are every 30 px, arrows are the normals (the way out)."),
    ("p", "OpenCV computes this table once per map with `cv2.distanceTransform` (run on the air and on the rock, "
          "then subtracted). After that, three questions are cheap lookups:"),
    ("ul", ["**Is this point inside rock, and how deep?** `terrain.distance(x, y)`. A foot circle of radius r is "
            "in the ground when `distance < r`, and it is `r - distance` deep.",
            "**Which way is out?** `terrain.normal(x, y)` - the direction in which the distance grows fastest "
            "(its gradient), found by sampling the distance 2 px left/right and up/down.",
            "**Where is the ground under the sky in this column?** `terrain.ground_y(x)`, used to place the flag."]),
    ("formula", "distance(x, y) = bilinear blend of the 4 table cells around (x, y)\n"
                "normal = normalize( d(x+2,y) - d(x-2,y) ,  d(x,y+2) - d(x,y-2) )"),
    ("p", "**Bilinear blending** means the distance changes smoothly between pixels instead of in 1 px steps, "
          "which keeps the physics from jittering. Points outside the map are handled specially: beyond the left "
          "and right edges counts as ever-deeper rock (invisible walls), and above the top edge the top row "
          "continues upward - sky stays sky, but a solid top border (like the cave's) becomes rock that gets "
          "deeper going up, so nothing can escape through it."),
    ("h3", "Moving parts: the windmill rotor"),
    ("p", "The windmill map has a solid part that moves. Its rotor gets its own distance table, made once "
          "for the rotor standing still. To ask how far a point is from the rotor *now*, the point is turned "
          "back around the hub by the rotor's current angle and looked up in that still table - turning the "
          "question is much cheaper than rebuilding the table 180 times a second. `Terrain.distance` returns "
          "the nearest of the rock and every moving part, so the physics needs no special code to collide with "
          "the rotor. `Terrain.mover_at` tells which moving part a point touches."),
    ("formula", "local point = hub + rotate(point - hub, -angle)\n"
                "rotor distance(point) = still table at the local point"),
    ("p", "The rotor turns clockwise at `rps` = 0.25 turns per second (set per map in `MAPS`). The tower is just "
          "part of the map picture and has no collision. Drawing the rotor means rotating a big picture every "
          "frame, so it is cut into four pieces (three blades and the hub); only pieces inside the view are "
          "rotated. The tower and the rotor are drawn after the character, so the character passes behind "
          "them."),
    ("fig", "shot_game_windmill.png", "The windmill map: the rotor is solid and turning; the map panel shows it too.",
     0.85, GAME),
    ("h2", "8. Physics of the character"),
    ("p", "The character is deliberately simple: **only the body (the head) has a position and a velocity**. It "
          "cannot rotate. The legs have no mass - each leg is just two angles that turn towards the angles the "
          "player asks for, at most 420 degrees per second. Where a foot is follows from the body position plus "
          "the two angles (*kinematics*, `Leg.joints`):"),
    ("formula", "hip  = body + hip_offset\nknee = hip  + rotate((0, thigh_length), thigh angle)\n"
                "foot = knee + rotate(foot_offset, shin angle)        # shin angle = thigh + bend"),
    ("p", "The method is **position-based dynamics** (PBD): instead of computing forces, each step first moves "
          "the body freely, then *corrects its position* until all contacts are satisfied, and finally derives "
          "the velocity from how far the body actually moved. One `_step` does:"),
    ("ol", ["**Sticky feet** - a sticky foot that is within 8 px of the rock gets *glued*: its position is "
            "remembered as an anchor. A foot that stops being sticky lets go.",
            "**Predict** - add gravity to the velocity, apply a little air drag, move the body by velocity x dt.",
            "**Solve** (4 passes) - for every foot: if glued, move the body so the foot goes back towards its "
            "anchor; otherwise, if the foot is inside rock, push the body out along the normal and apply friction. "
            "Then push the head out of the rock. Each correction can upset another, so the passes repeat "
            "(the Gauss-Seidel method).",
            "**Rock has the last word** - two extra passes make sure no glued foot is more than 6 px deep.",
            "**Velocity** - `velocity = (new position - old position) / dt`, then limits (head friction, "
            "max speed, stay inside the map). The 1500 px/s limit applies to the whole speed whenever "
            "something pushed or pulled the body; in free flight only the falling speed is limited, so a "
            "sideways fling keeps its sideways speed instead of drifting down slowly."]),
    ("h3", "Why this gives jumping and walking for free"),
    ("p", "**Jumping**: if a planted leg straightens quickly, its foot would go into the ground. The solver "
          "pushes the body up instead, by exactly the amount the foot would have sunk. Because velocity is "
          "*measured* from the movement, the body now has upward speed and keeps flying after the foot leaves "
          "the ground. The recording below comes from the real physics:"),
    ("fig", "fig_jump.png", "A recorded jump on the mountain: the thigh angle drops (leg straightens), the body gets "
                            "about 950 px/s upward, rises ~240 px and lands."),
    ("p", "**Walking**: when a free foot first touches walkable ground (flatter than 55 degrees) it remembers that "
          "point (`grip`). While it stays down, the solver does not let the foot slide along the surface "
          "(*static friction*). So if the player sweeps the leg backwards, the foot cannot move - the body moves "
          "forward instead. On steeper slopes there is no grip and feet slide, which is what makes walls need "
          "sticky feet."),
    ("p", "**Climbing**: a glued foot works in both directions - it can push *and pull* the body. Hanging from a "
          "ledge, a player can bend the glued leg to pull the body up. If the glue is stretched more than 40 px "
          "it tears off."),
    ("p", "**Riding the rotor**: a foot glued to the rotor remembers that (`anchor_on`). At the start of every "
          "physics step its anchor is turned with the rotor (`Windmill.carry`), so the body is pulled along. "
          "Because velocity is measured from movement, letting go flings the character with the speed it had. "
          "Free (non-sticky) feet only grip the rotor where it is flatter than `ROTOR_WALKABLE_SLOPE` (10 "
          "degrees instead of 55), so without sticky feet the character slips off the blades quickly. A blade "
          "that overlapped a free foot or the head deeply would push it out in one step - a huge kick - so "
          "leaving a blade may be at most `ROTOR_PUSH_SPEED` (400 px/s) faster than the blade moves there "
          "(`Windmill.velocity_at`)."),
    ("h3", "Keeping feet out of the rock while glued"),
    ("p", "With a foot glued, the body is pinned and cannot always move out of the way, so a leg could be forced "
          "into the rock. `Character.update` therefore checks every step: if a moving leg pushed its own foot "
          "deeper than allowed (3 px for free feet, 6 px for sticky feet), the step is undone and redone with "
          "that leg held still - the leg stops at the rock. A glued foot pushed in by *another* leg is held at "
          "6 px by the extra solver passes."),
    ("h3", "Substeps"),
    ("p", "Physics runs three times per frame with a third of the time each. Smaller steps mean feet move less "
          "per step, so they cannot jump through thin rock, and the solver stays stable."),
    ("table", [["Setting", "Value", "Effect when you raise it"],
               ["GRAVITY", "2000 px/s^2", "Heavier, falls faster, lower jumps"],
               ["LEG_MAX_SPEED", "420 deg/s", "Legs react faster, kicks and jumps get stronger"],
               ["MAX_SPEED", "1500 px/s", "Allows faster flights"],
               ["WALKABLE_SLOPE", "55 deg", "Feet grip on steeper slopes without sticking"],
               ["SOLVER_ITERATIONS", "4", "Stiffer, more exact contacts (slower)"],
               ["STICKY_BREAK_DIST", "40 px", "Glue holds longer before tearing off"],
               ["PHYSICS_SUBSTEPS", "3", "More stable, slower"]], [0.3, 0.2, 0.5], (0, 1)),
    ("h2", "9. From the camera to the legs"),
    ("p", "`VisionInput._loop` runs in the background thread. For each webcam frame it does:"),
    ("ol", ["**Mirror** the picture so it behaves like a mirror (your right hand appears on the right).",
            "**Pose**: YOLO finds every person and 17 body keypoints each, with a confidence per keypoint.",
            "**Number the players** (`assign_players`): take the n biggest people (closest to the camera) and "
            "number them left to right. With fewer people than players, the picture is split into n vertical "
            "strips and you get the number of the strip you stand in.",
            "**Faces**: MediaPipe finds face landmarks on the whole frame. `match_faces` gives each face to the "
            "person whose head keypoints are closest in pixels (closest pairs first). A player without a face "
            "gets a second try on a crop around their head.",
            "**Per player**: limb angles (`limb_poses`) smoothed by `AngleSmoother`, the mouth state "
            "(`MouthTracker`) and, with one player, the head tilt (`HeadTilt`).",
            "**Preview**: draw the skeletons and lips on a copy of the frame (`PreviewRenderer`).",
            "Store the results under the lock."]),
    ("fig", "fig_keypoints.png", "Left: the 17 keypoints of one body. Right: the four face points used for the "
                                 "mouth."),
    ("h3", "Arm angles"),
    ("p", "For an arm, the shoulder angle is the direction of shoulder -> elbow and the elbow angle is the "
          "direction of elbow -> wrist, both measured from 'down' and corrected by the torso direction (shoulders "
          "-> hips) so leaning does not swing the legs. Left limbs are mirrored (multiplied by -1) to get the "
          "outward convention. Sides come from where the joints are on screen, not from the model's left/right "
          "labels, because on a mirrored picture those can be swapped."),
    ("formula", "heading(v) = atan2(v.x, v.y)                 # angle from straight down\n"
                "thigh = side * wrap(heading(elbow - shoulder) - torso)\n"
                "bend  = wrap(side * wrap(heading(wrist - elbow) - torso) - thigh)"),
    ("p", "Keypoints jitter by a few pixels every frame. `AngleSmoother` applies an *exponential moving average* "
          "(EMA): each new value moves the smoothed value 60% of the way. It is *wrap-safe*: going from 179 to "
          "-179 degrees is treated as a 2 degree step, not a 358 degree swing."),
    ("h3", "Mouth: open or closed"),
    ("p", "The mouth ratio is the gap between the lips divided by the mouth width. Dividing by the width makes it "
          "the same whether the face is near (big) or far (small). The ratio is smoothed, then a **hysteresis** "
          "decides the state: it opens only above 0.35 and closes only below 0.25. Between the two lines the "
          "state stays as it was, so a ratio hovering around one value cannot make the feet flicker."),
    ("fig", "fig_mouth.png", "Hysteresis on a made-up recording: the 0.30 bump at t = 3.8 s is not enough to open; "
                             "noise around the thresholds does not toggle the state."),
    ("p", "If the face is lost for a moment, the last state is kept for 0.5 s before it falls back to closed."),
    ("h3", "Head tilt (1 player)"),
    ("p", "With one player, both legs belong to the same mouth, so the sideways tilt of the head picks which foot "
          "the open mouth makes sticky. The roll angle is the slope of the line between the ears (or the eyes if "
          "an ear is hidden). Tilting right (right ear lower) beyond 10 degrees selects the right foot, tilting "
          "left the left foot; in between, the last choice is kept."),
    ("h2", "10. Drawing"),
    ("h3", "Sprites that rotate around a joint"),
    ("p", "All character pictures share one 500 x 500 canvas, and the joint positions were measured on it "
          "(`config.LEG_PIVOT` etc.). `PivotSprite.draw` rotates an image around its joint: pygame rotates "
          "around the image centre, so the code rotates the vector from the joint to the centre by the same angle "
          "and places the rotated image's centre there - the joint ends up exactly where it should."),
    ("p", "Which way a toe points: the shoe picture points right while the shin hangs down, so left legs use a "
          "mirrored copy to point outward. The two upper legs are usually raised, which turns the shoe upside "
          "down and its toe inward - so the legs listed in `config.MIRRORED_SHOES` (the upper two) use the "
          "opposite copy, and their toes point outward too, like in `character-demo.png`. The foot's "
          "collision circle follows the same choice (`Leg.shoe_side`)."),
    ("p", "Pictures are prepared once: cropped to their content (so rotating is cheap), scaled, mirrored for left "
          "legs (toes point outward) and recoloured. The recolour filter takes clearly red pixels and moves their "
          "'redness' into other channels, which keeps the shading: green = sticky, purple = glued. For the "
          "1-player long legs, `stretch_leg` stretches only the black stick part and moves the shoe down unchanged."),
    ("h3", "One window, three panels"),
    ("p", "Every scene draws onto the same canvas (1365 x 721). `Display.present()` fills the window, scales the "
          "canvas into the left panel, draws the newest camera picture at the top of the right column and the "
          "map overview under it, and calls "
          "`pygame.display.flip()`, which shows the finished frame all at once (no flicker). F11 recreates the "
          "window in fullscreen and recomputes the layout."),
    ("p", "The map panel (`MiniMap`) shows the whole map with its flag, a white frame around the part the game "
          "view shows and a yellow dot for the character. The shrunk map picture is made once per panel size; "
          "only the frame, the dot and the windmill rotor are drawn each frame. On the other screens the panel "
          "shows a short note."),
    ("fig", "shot_game_debug.png", "F1 debug view: magenta = head circle, feet circles coloured green (glued), "
                                   "yellow (touching) or red (in the air).", 0.85, GAME),
    ("h2", "11. The screens"),
    ("p", "The menu has three pages in one loop (`page` = title, players, maps). PLAY leads to the player count, "
          "then to the map. 1P TEST opens the test screen. Every button position is a fraction of the canvas size."),
    ("fig", "shot_menu_maps.png", "The map page. Each picture is the whole map shrunk, with its flag; the cards are laid "
                          "out side by side with equal gaps.", 0.85, GAME),
    ("fig", "shot_test.png", "The 1-player test screen: no physics, the body stays still and the legs follow the "
                             "arms; mouth state in big letters.", 0.85, GAME),
    ("fig", "shot_complete.png", "Touching the flag with the head stops the timer and asks for the team name.",
     0.85, GAME),
    ("h3", "The score board"),
    ("p", "After the flag, the team types a name (up to 16 characters, any keyboard layout - the letters arrive "
          "as `TEXTINPUT` events). **Enter** saves, **Esc** skips saving. The board then shows the 8 fastest "
          "times on this map with this many players; the new run is gold, and if it is not in the top 8 it "
          "takes the last line with its real place. Enter goes to the menu, F5 plays again."),
    ("p", "`ScoreBoard` keeps every saved run in `scores.json` (name, map, player count, time, date) and never "
          "deletes any. It writes a temporary file first and then swaps it in, so a crash cannot leave a "
          "half-written file. A broken file is renamed to `scores.json.broken` and the board starts empty. "
          "Like `settings.json`, the file is not in git."),
    ("fig", "shot_scores.png", "The score board after saving (demo names).", 0.85, GAME),

    ("h2", "12. Options and settings"),
    ("p", "The **OPTIONS** button on the title screen lets players tune the game without touching code: camera, "
          "mouth, head tilt, controls, physics and fullscreen. Changes apply at once and are remembered in "
          "`settings.json` next to the game."),
    ("fig", "shot_options.png", "The Mouth tab. The green line shows each player's live mouth score, so the "
                                "thresholds can be set while watching it. A gold * marks a changed value.",
     0.85, GAME),
    ("h3", "How a setting reaches the game"),
    ("p", "There is no separate settings system inside the game: every part already reads its numbers from "
          "`config` (for example `config.GRAVITY` in the physics step). A `Setting` in `settings.py` names one of "
          "those values, and `Settings.set()` simply writes the new value into `config` - so the next physics "
          "step, the next mouth check or the next arm reading already uses it."),
    ("ol", ["Start-up: `App` creates `Settings`, which first remembers the values written in `config.py` as the "
            "defaults, then `load()` reads `settings.json` and applies it.",
            "In the Options screen a slider or switch calls `settings.set(key, value)`.",
            "Leaving the screen (BACK, Esc or closing the window) calls `save()`, which writes only the values "
            "that differ from the defaults. **RESET TO DEFAULTS** puts the `config.py` values back."]),
    ("p", "For this to work a value must be *read when used*, not copied once at start-up. Two places did copy: "
          "`limb_poses` (joint confidence) and `AngleSmoother` (arm smoothing); they now read `config` each time."),
    ("h3", "Why it cannot break the game"),
    ("ul", ["Only safe values are offered. Things like the camera number, model files, sprite geometry or solver "
            "internals are not in the list, because a wrong value there stops the game.",
            "Every number has a minimum, maximum and step (`Setting.clamp`); anything outside is pulled back in.",
            "The two mouth thresholds are kept in order: 'close' always stays at least 0.05 below 'open'.",
            "A missing, broken or hand-edited `settings.json` never crashes the game: wrong types and unknown "
            "names are ignored, numbers are clamped, unreadable files fall back to the defaults.",
            "`settings.json` is not in git: every computer keeps its own tuning."]),
    ("table", [["Tab", "Settings"],
               ["Camera", "mirror on/off, joint confidence needed"],
               ["Mouth", "open threshold, close threshold, smoothing, keep state when the face is lost"],
               ["Head tilt", "switch angle, swap sides (1 player)"],
               ["Controls", "leg speed, arm smoothing"],
               ["Physics", "gravity, grip on slopes, sticky-foot tear-off distance"],
               ["Display", "fullscreen (applied at once, remembered)"]], [0.2, 0.8]),

    ("h2", "13. The Python environment (Windows and Linux)"),
    ("p", "The game depends on a few big libraries (PyTorch, Ultralytics, MediaPipe, OpenCV, pygame) that change "
          "often. To make the game install the same way on every computer, it runs in its own **virtual "
          "environment**: a private folder `.venv` with exactly the tested package versions, separate from any "
          "other Python projects on the computer."),
    ("h3", "What the setup script does"),
    ("ol", ["Finds **Python 3.12** - exactly that version, because newer ones (3.13, 3.14) do not have "
            "mediapipe/PyTorch packages yet. If it is missing, Windows offers to install it with `winget`; "
            "Linux offers to get it with `uv`, which downloads a private Python 3.12 for your user (no "
            "`sudo`, the system Python is not changed).",
            "Creates `.venv` with Python's built-in `venv` module (or updates it if it exists). A `.venv` "
            "made with another Python version is deleted and rebuilt with 3.12.",
            "Installs **PyTorch first**: the CUDA build when an NVIDIA GPU is found (`nvidia-smi`), otherwise the "
            "small CPU build. It must come first, because `ultralytics` would otherwise pull a default build.",
            "Installs the pinned game packages from `requirements.txt`.",
            "Optionally (NVIDIA only, asks y/N) installs TensorRT and builds the engine (`export_engine.py`).",
            "Runs `download_models.py`: downloads both AI models and reports whether the GPU will be used."]),
    ("table", [["File", "Contents"],
               ["requirements.txt", "pygame, numpy, OpenCV, mediapipe, ultralytics (exact versions). Both OpenCV "
                                    "packages are pinned to the same version: they install the same `cv2` module "
                                    "and would overwrite each other otherwise."],
               ["requirements-gpu.txt", "TensorRT (optional, NVIDIA)"],
               ["requirements-dev.txt", "tools to rebuild this PDF (not needed to play)"]], [0.3, 0.7], (0,)),
    ("h3", "Linux specifics"),
    ("ul", ["`setup.sh` checks things Windows does not need: that the `venv` module is installed "
            "(`sudo apt install python3.12-venv`), that OpenCV finds its system library "
            "(`sudo apt install libgl1 libglib2.0-0`), and that your user may open the webcam "
            "(`sudo usermod -aG video $USER`, then log in again).",
            "Fonts: the game asks for a list of fonts (`config.FONT_*`) and uses the first one installed - Arial "
            "and Consolas on Windows, DejaVu or Liberation on Linux. If no emoji font exists, the sheep in the "
            "menu is simply left out instead of showing an empty box.",
            "NVIDIA on Linux: the CUDA 13 build of PyTorch needs driver 580 or newer; with an older driver "
            "`download_models.py` says so and the game runs on the CPU. The TensorRT engine must be built on "
            "each computer anyway (`export_engine.py`), because it only works on the GPU it was made for.",
            "`.gitattributes` keeps `.sh` files with Linux line endings even when committed from Windows."]),
]


# ======================================================================= PART III
# (file, purpose, [(anchor text found on the first line of the block, explanation), ...]) in file order
FILES = [
    ("main.py",
     "The entry point. It only reads the command line, creates the right input source and starts the app.",
     [('"""All For One', "Module docstring: how to start the program and what to install."),
      ("import argparse", "Imports. `KeyboardInput` is cheap to import; the camera input is imported later."),
      ("def main():", "Warn if this is not Python 3.12 (the version the packages are pinned for)."),
      ("# Describe the command-line", "Declare the four command-line options; `parse_args` reads what the user "
                                      "typed."),
      ("# Both input sources", "Pick the input source. The vision module is imported only here because loading "
                               "torch/ultralytics/mediapipe takes seconds."),
      ("App(source", "Create the app with that source and run it until the player quits."),
      ("# Run main() only", "Standard Python idiom: run `main()` only when the file is started directly.")]),
    ("app.py",
     "Owns the window and the three scenes, and switches between them. Each scene's `run()` returns where to go "
     "next.",
     [('"""App:', "Docstring explaining scenes."),
      ("import pygame", "Imports of every scene and helper."),
      ("class App:", "Constructor: start pygame, title the window."),
      ("# Saved player settings", "Load `settings.json` into `config` before anything is built (chapter 12)."),
      ("# The window must exist", "Create the display first (images can only be converted for fast drawing once "
                                  "a window exists), then load maps, then the scenes."),
      ("def run(self):", "The switchboard loop: menu -> chosen scene (game, test or options) -> back to menu, "
                         "until quit. The `finally` block always stops the camera thread and closes pygame, even "
                         "after a crash.")]),
    ("config.py",
     "Every number that changes how the game looks or feels. Nothing here runs logic; the other files read these "
     "values. The Part IV reference table lists every setting.",
     [('"""All tunable', "Docstring: units and colour conventions."),
      ("ROOT = ", "Paths: the project folder and the assets folder, built from this file's location."),
      ("def asset(name):", "Helper: full path of an asset picture."),
      ("# ---", "Maps: reference height, the list of maps (name, pictures, spawn, scale) and how high the "
                "character starts."),
      ("map / view --",
       "Game view size, window layout, frame rate, physics substeps, camera smoothing, sky colour."),
      ("character size --",
       "Character size and the geometry measured on the 500 px sprite canvas (head, joints, feet)."),
      ("LEGS = {", "The four legs: hip position, side, rest pose."),
      ("# Who drives which leg", "Control schemes for 1-4 players: (player, limb, leg) rows."),
      ("MAX_PLAYERS", "Player limit, leg stretch for 1 player, where the shoe starts in the shin picture."),
      ("flag --",
       "Flag size and placement settings."),
      ("physics --", "Physics constants."),
      ("vision --",
       "Camera, model files, keypoint threshold, face matching and crop settings, mouth and head-tilt "
       "thresholds, smoothing, colours."),
      ("fonts --", "Font lists with Windows and Linux names; pygame uses the first one installed."),
      ("menu --", "Title and credit text.")]),
    ("settings.py",
     "Everything about player settings: which config values the Options screen may change, the safe range of "
     "each, and loading/saving `settings.json` (chapter 12).",
     [('"""Player-tunable', "Docstring: how settings flow into `config`, and why they cannot break the game."),
      ("import json", "Imports, the file location and the minimum gap between the mouth thresholds."),
      ("@dataclass", "`Setting`: one tunable value - config name, label, tab, type, range, step, unit, help."),
      ("def clamp", "Convert a value to the right type and force it into the safe range (None if impossible)."),
      ("GROUPS = ", "The tabs, and the list of all tunable settings with their ranges and help texts."),
      ("BY_KEY", "Look-up table: config name -> Setting."),
      ("class Settings:", "Remember the config.py values as the defaults."),
      ("def get(self, key)", "Current value (read from config)."),
      ("def set(self, key, value)", "Clamp, write into config, keep 'close' below 'open'."),
      ("def reset", "Put the defaults back."),
      ("def changed", "Only the values that differ from the defaults."),
      ("def load", "Read settings.json safely; anything wrong is skipped."),
      ("def save", "Write the changed values (or delete the file when nothing changed).")]),
    ("display.py",
     "The single window. Scenes draw on a fixed-size canvas; this class scales it into the window next to the "
     "camera picture and handles fullscreen.",
     [('"""The single app window', "Docstring with the layout sketch."),
      ("import pygame", "Imports."),
      ("class Display:", "Constructor: layout size in canvas units (game + camera + margins), create the window "
                         "and the canvas."),
      ("def _set_mode", "Create the window: fullscreen at screen size, or windowed at the biggest scale that fits "
                        "92% of the desktop."),
      ("def _layout", "Compute where the game panel, the camera panel (top of the right column, 4:3) and the "
                      "map panel (the rest of the column) go for a given window size."),
      ("def toggle_fullscreen", "Switch mode."),
      ("def handle_event", "Keys every scene shares (F11). Returns True if it used the event."),
      ("def to_canvas", "Convert a mouse position from window pixels to canvas pixels."),
      ("def present", "Draw the frame: background, scaled canvas, frame, camera, map; then `flip()` shows it."),
      ("def _draw_camera", "Turn the newest camera frame (numpy) into a pygame image only when it changed, fit it "
                           "into the panel, or show 'no camera'."),
      ("def _draw_map", "Let the game draw the map overview (it passes a function), or show a note.")]),
    ("minimap.py",
     "The whole map in the panel under the camera (chapter 10).",
     [('"""Map overview', "Docstring and imports."),
      ("MARKER", "Colours of the character dot and the view frame."),
      ("class MiniMap:", "Remembers its map and the cached small picture."),
      ("def _picture", "The map with its flag shrunk to the panel size; redone only when the size changes."),
      ("def draw", "Fit the map into the panel keeping its shape, draw the turning rotor, the frame of the "
                   "visible area and the character dot (kept inside the picture).")]),
    ("menu.py",
     "The menu screen with its three pages. Returns what the player chose.",
     [('"""Main menu', "Docstring: how the page loop works."),
      ("import pygame", "Imports."),
      ("PLAYER_INFO", "Help text on the player-count buttons."),
      ("class Menu:", "Constructor: backdrop picture, demo character, fonts."),
      ("cx = w // 2", "Create every button: PLAY, 1P TEST, the four player-count buttons, BACK and one picture "
                      "button per map, laid out side by side with equal gaps."),
      ("def run(self):", "The menu loop: handle quit/F11, convert mouse positions to canvas pixels, react to "
                         "keys and clicks depending on the page, then draw."),
      ("def _render_emoji", "Render the sheep with an emoji font, or None if none is installed (Linux)."),
      ("def draw_credit", "Draw the credit line, with the sheep if it could be rendered."),
      ("def draw(self, page):", "Draw the current page.")]),
    ("ui.py",
     "Reusable drawing helpers for the screens.",
     [('"""Small UI', "Docstring."),
      ("def draw_text", "Text with a black outline: the text is pasted 8 times in black around its position, "
                        "then once in colour on top."),
      ("class Button:", "A rounded clickable rectangle."),
      ("def clicked", "True for a left click inside the button."),
      ("def draw(self, surface, mouse=None):", "Hover effect, shadow, body, border, label and optional subtitle "
                                               "lines."),
      ("class MapButton", "A button that shows a map picture with its name; reuses Button's click test."),
      ("class Slider:", "A slider: mouse x -> value snapped to the step; click or drag; draws track, fill and "
                        "knob."),
      ("class Toggle:", "An on/off switch: click to flip; draws a pill with a knob left (off) or right (on).")]),
    ("game.py",
     "The level itself: the game loop, players -> legs, physics substeps, camera, timer, flag, HUD and the "
     "finish screen.",
     [('"""Game scene', "Docstring listing the six steps of every frame."),
      ("import pygame", "Imports."),
      ("BOARD_ROWS", "Rows of the score board; readable leg names for the HUD."),
      ("def apply_players", "For each (player, limb, leg) row of the scheme: copy the limb's angles to the leg as "
                            "its target and set the leg's sticky flag from the mouth (and head tilt)."),
      ("class Game:", "Constructor: fonts, clock, sprite scale (character = 1/8 of the map height), score board "
                      "and name-entry state."),
      ("def spawn_point", "Start position of the current map."),
      ("def build_character", "Create a character with only the controlled legs; sprites are cached per leg "
                              "length."),
      ("def restart", "Back to the start: rotor, character (at a spot where no foot is in the rock), view, "
                      "timer, name entry."),
      ("def run(self, num_players, game_map):", "Set up the map, view, input and character, then the frame loop: "
                                                "events (typing the name first), players, physics substeps "
                                                "(the rotor turns too), camera, timer, flag check, drawing."),
      ("def complete", "Flag touched: stop the timer, compare with the saved best, start the name entry."),
      ("def name_key", "Typing: characters, Backspace, Enter saves to the score board, Esc skips."),
      ("def apply_players(self, players):", "Method wrapper around the module function."),
      ("def draw(self, players):", "Draw in painter's order (map, flag, character, windmill in front, HUD) and present."),
      ("def draw_minimap", "Called by the display to draw the map panel."),
      ("def draw_leg_owners", "Coloured dot on each knee showing which player drives that leg."),
      ("def draw_hud", "Player lines and the info line."),
      ("def format_time", "Seconds -> mm:ss.cc."),
      ("def draw_complete", "Dark overlay with COMPLETED!, time and best time, then name entry or board."),
      ("def draw_name_entry", "Question, text box with a blinking cursor, help line."),
      ("def draw_board", "Top 8 for this map and player count; this run in gold, on the last line if lower."),
      ("def _fit", "Shorten a long name with '...' so it never runs into the time column."),
      ("def _cell", "One table cell aligned left or right."),
      ("def draw_timer", "Timer in the top-right corner (gold when finished)."),
      ("def _text", "Small text with a shadow.")]),
    ("scoreboard.py",
     "Finish times with team names, kept in scores.json (chapter 11).",
     [('"""Score board', "Docstring with the file format."),
      ("import datetime", "Imports, file path and longest name."),
      ("class ScoreBoard:", "Load the file at start."),
      ("def _load", "Read the file; keep only well-formed rows; rename a broken file instead of crashing."),
      ("def _save", "Write a temporary file, then swap it in."),
      ("def add", "Store a run with the date and save."),
      ("def ranking", "Runs on one map with one player count, fastest first."),
      ("def best", "The fastest time or None.")]),
    ("test_scene.py",
     "1-player test screen: same input and leg logic as the game, but no physics, so the player can check the "
     "controls.",
     [('"""1-player test', "Docstring."),
      ("import pygame", "Imports."),
      ("PLAYERS = 1", "Settings: one player, bigger character, white background."),
      ("class TestScene:", "Constructor: centre position, scheme, its own (bigger) character and fonts."),
      ("def run(self):", "Loop: events, players, `apply_players`, move only the leg angles, draw."),
      ("def draw(self, st):", "White background, character, the mouth state in huge letters, sticky side and "
                              "head roll, help line.")]),
    ("options_menu.py",
     "The Options screen: tabs on the left, the settings of the selected tab as sliders and switches on the "
     "right, a help line and a live readout (chapter 12).",
     [('"""Options screen', "Docstring and imports."),
      ("ROW_H", "Height of one setting row."),
      ("def format_value", "Value -> text: ON/OFF, or the number with the decimals of its step and its unit."),
      ("class OptionsScene:", "Constructor: dark backdrop and fonts."),
      ("# left column", "One tab button per group."),
      ("# right panel", "One row per setting: label position, value position and its widget."),
      ("self.reset = Button", "RESET TO DEFAULTS and BACK buttons."),
      ("def visible", "The settings of the selected tab."),
      ("def run(self):", "Loop: track 1 player on the Head tilt tab (tilt is only measured then), else up to 4; "
                         "handle quit/F11/Esc/BACK (all save), Reset, tabs, switches and sliders; draw."),
      ("def _apply_fullscreen", "Make the window match the Fullscreen setting at once."),
      ("def draw(self):", "Backdrop, title, tabs, panel with rows (changed values in gold with *), live line, "
                          "help line, buttons."),
      ("def _live_text", "Live mouth scores (Mouth tab) or head roll (Head tilt tab) from the camera.")]),
    ("maps.py",
     "Turns an entry of `config.MAPS` into a playable map.",
     [('"""Playable maps', "Docstring and imports."),
      ("THUMB_HEIGHT", "Height of the menu picture."),
      ("class GameMap:", "Load both pictures and scale them to the common height (times the map's own scale)."),
      ("self.terrain = Terrain", "Build collision."),
      ("self.windmill = None", "Windmill maps: paint the tower into the map picture and add the rotor as a "
                               "moving solid part; then place the flag and find the start point."),
      ("# Small picture for", "Make the menu thumbnail with the flag (and rotor) pasted on it."),
      ("def reset(self):", "Moving parts: reset, turn, draw big and small. Maps without them do nothing."),
      ("def _find_spawn", "From the configured point: go up out of rock if needed, then find floor and ceiling "
                          "and start above the floor (or mid-gap in a low tunnel)."),
      ("def load_maps", "Build every map in the list.")]),
    ("windmill.py",
     "The windmill: a tower picture and a solid, spinning rotor (chapter 7).",
     [('"""Windmill:', "Docstring: how the rotor collision works and how feet ride along."),
      ("import math", "Imports."),
      ("PAD = 48", "Empty border of the rotor's table; radius of the hub piece."),
      ("class Windmill:", "Speed, slipperiness, hub position (scaled to the map), angle; crop and scale the tower picture."),
      ("# rotor: crop", "Crop the rotor picture to its content and scale it."),
      ("# collision table", "Distance table of the still rotor with a border, and how far it reaches."),
      ("def _split", "Cut the rotor into three blades and the hub for fast drawing."),
      ("def reset", "Back to angle 0."),
      ("def update", "Turn by 360 x rps x dt; remember this turn and the cosine/sine for lookups."),
      ("def velocity_at", "Speed of the rotor surface at a point (for limiting pushes)."),
      ("def carry", "Turn a point stuck on the rotor by the last turn."),
      ("def distance", "Far away: a safe estimate. Near: turn the point back and look it up in the table."),
      ("def draw(self", "Draw the tower, then rotate and draw the rotor pieces inside the view (after the "
                        "character, so the windmill is in front of it)."),
      ("def draw_small", "The rotor for the map panel and the menu picture.")]),
    ("terrain.py",
     "Map picture and collision via a signed distance field (see chapter 7).",
     [('"""Map image', "Docstring explaining the signed distance field."),
      ("import math", "Imports."),
      ("class Terrain:", "Constructor: compose the map picture (sky, background, foreground)."),
      ("# Alpha channel of", "Build the solid mask from the foreground alpha, add invisible side walls, compute "
                             "the distance field."),
      ("self.movers = []", "Moving solid parts (the windmill rotor) are added here by the map."),
      ("def _signed_distance", "Two distance transforms (air -> rock, rock -> air) subtracted."),
      ("def distance", "Distance to the nearest solid thing: rock or a moving part."),
      ("def mover_at", "Which moving part a point touches, if any (for feet that ride the rotor)."),
      ("def rock_distance", "Smooth lookup of the rock distance with special rules outside the map."),
      ("def normal", "Direction out of the rock from the distance gradient."),
      ("def ground_y", "First rock below the open sky in a column (used for the flag).")]),
    ("flag.py",
     "The goal flag.",
     [('"""Goal flag', "Docstring and imports."),
      ("class Flag:", "Load and size the flag; build its pixel mask."),
      ("# stand on the highest", "Find the right-most ground with room for the flag and take the highest point "
                                 "near it; place the pole foot there."),
      ("def touches", "Pixel-perfect test: draw the head as a circle mask and check overlap with the flag mask."),
      ("def draw", "Draw at its screen position.")]),
    ("viewport.py",
     "The game camera (the visible part of the map).",
     [('"""Game camera', "Docstring."),
      ("def view_size", "View size: 1/3 of the reference height, mountain map's shape."),
      ("class Viewport:", "Holds the map size, view size and top-left position."),
      ("def _clamped", "Keep the view inside the map."),
      ("def snap", "Jump to a target."),
      ("def follow", "Glide towards a target (fast when far, slow when close)."),
      ("def rect", "Visible area as a rectangle.")]),
    ("character.py",
     "The heart of the game: legs, kinematics, the physics step and drawing (see chapter 8).",
     [('"""The four-legged', "Docstring: how the physics works."),
      ("import math", "Imports and the short vector name `V`."),
      ("def wrap_deg", "Angle helpers: wrap to -180..180 and turn towards a target the short way."),
      ("class Leg:", "One leg: geometry (scaled and stretched), rest pose, current and target angles, sticky "
                     "state."),
      ("def set_target", "Store the angles the player asks for."),
      ("def update_angles", "Turn towards the target at most LEG_MAX_SPEED."),
      ("def screen_angles", "Outward angles -> screen rotations."),
      ("def joints", "Hip, knee and foot positions (kinematics)."),
      ("class Character:", "The character: head radius and the controlled legs."),
      ("def reset", "Back to the start pose."),
      ("def free_spot", "Find a start point where the head and all feet are clear of the rock (long 1-player "
                        "legs would otherwise start inside the ground and be thrown up)."),
      ("def update", "One physics step with the 'undo and hold the leg' check."),
      ("def _step", "The position-based physics step: move glue/grip points that sit on the rotor, glue, "
                    "predict, solve, cap, velocity."),
      ("def _snapshot", "Save / restore everything a step changes."),
      ("def _foot_depth", "How deep a foot is in the rock."),
      ("def _sunk_feet", "Feet deeper than allowed and deeper than before."),
      ("def _solve_foot", "Glued: pull towards the anchor. Free: push out of rock, then static friction on "
                          "walkable ground (much less on the rotor)."),
      ("def _cap_sink", "Limit a glued foot's depth."),
      ("def _solve_head", "Push the head circle out of the rock."),
      ("def _update_contacts", "Contact flags, tear off over-stretched glue, forget grips of lifted feet."),
      ("def draw", "Legs then head; shoe colour by state; optional debug circles.")]),
    ("assets.py",
     "Prepares the character pictures (see chapter 10).",
     [('"""Character images', "Docstring and imports."),
      ("class PivotSprite:", "An image plus the joint it rotates around."),
      ("def draw(self, target, pos, angle):", "Rotate around the joint (see chapter 10)."),
      ("def flipped", "Mirror image with mirrored joint."),
      ("def _crop_scale", "Crop the empty canvas away, scale, move the joint along."),
      ("def stretch_leg", "Make a leg picture longer without stretching the shoe."),
      ("def recolor_red", "Turn the red shoe green or purple while keeping its shading."),
      ("class CharacterSprites:", "Build all pictures once: head, thigh, shin in red/green/purple, each for left "
                                  "and right.")]),
    ("inputs.py",
     "The input interface and the keyboard input.",
     [('"""Input sources', "Docstring and imports."),
      ("class InputSource:", "The interface: every input offers these methods."),
      ("class KeyboardInput", "Keyboard input: key layout and mouth keys."),
      ("def __init__(self):", "Start every leg at its rest pose."),
      ("def get_players(self):", "Turn held keys into angle changes, then hand each leg's pose to the player/limb "
                                 "that drives it.")]),
    ("vision.py",
     "Everything about the webcam: the background thread, both AI models and the per-player trackers (see "
     "chapter 9 and Part V).",
     [('"""Webcam -> players', "Docstring with the per-frame pipeline."),
      ("import os", "Imports."),
      ("class Person:", "One detected body: keypoints, confidences, box, face, player number."),
      ("def area", "Box size (closeness to camera)."),
      ("def center_x", "Left/right position."),
      ("def head_center", "Average of visible head keypoints."),
      ("def shoulder_width", "Body size for distance limits."),
      ("def head_box", "Square crop around the head for the face fallback."),
      ("class PoseDetector:", "Load YOLO on the fastest backend (TensorRT > GPU > CPU)."),
      ("def detect(self, frame):", "Run YOLO, convert results to Person objects."),
      ("class FaceDetector:", "Load MediaPipe (download the model if missing): VIDEO-mode for frames, IMAGE-mode "
                              "for crops."),
      ("def _mp_image", "BGR numpy -> MediaPipe RGB image."),
      ("def detect_full", "Faces on the whole frame, as pixel arrays."),
      ("def detect_crop", "Face in a head crop, mapped back to frame pixels."),
      ("def close(self):", "Release the models."),
      ("def match_faces", "Assign faces to bodies by pixel distance, closest first."),
      ("def assign_players", "Number the biggest people left to right."),
      ("def mouth_ratio", "Lip gap / mouth width."),
      ("class MouthTracker:", "Smoothing, hysteresis and timeout for one player's mouth."),
      ("class HeadTilt:", "Ear-line roll angle -> sticky side, with a dead zone."),
      ("class VisionInput", "The camera input: models, camera, lock, thread start."),
      ("def set_num_players", "Ask the thread to switch player count."),
      ("def _reset_players", "Fresh trackers for a new player count."),
      ("def _loop", "The background loop: read, mirror, process, FPS, preview, store under the lock."),
      ("def _process", "One frame -> PlayerStates."),
      ("def get_players", "Newest states (game thread)."),
      ("def get_preview", "Newest preview picture (game thread)."),
      ("def close(self):", "Stop the thread, release camera and models.")]),
    ("player_state.py",
     "Data passed from input to game, and the arm-angle maths (see chapter 9).",
     [('"""What the game needs', "Docstring with the 17 COCO keypoints."),
      ("import math", "Imports and keypoint index constants."),
      ("class LimbPose:", "Two angles from one limb."),
      ("class PlayerState:", "Everything known about one player this frame."),
      ("def _heading", "Angle helpers."),
      ("def limb_chains", "Which keypoints form which limb, by screen side."),
      ("def limb_poses", "Torso direction and the two angles for every visible limb."),
      ("class AngleSmoother:", "Wrap-safe exponential moving average.")]),
    ("preview.py",
     "Draws the annotated camera picture.",
     [('"""Draws the camera', "Docstring and imports."),
      ("# pairs of COCO", "Which points to connect: body skeleton, lips, leg labels."),
      ("class PreviewRenderer:", "Grey skeleton for everybody, controlling limbs thick and coloured, player label, "
                                 "lips."),
      ("def _draw_mouth", "Lip outline, yellow and thicker when open."),
      ("def _draw_hud", "FPS line and one status line per player.")]),
    ("export_engine.py",
     "Builds the TensorRT engine for the pose model (see Part V).",
     [('"""Build the TensorRT', "Docstring: when and why to run it."),
      ("from ultralytics", "Imports."),
      ('if __name__ == "__main__":', "Export with half precision at 640 px on GPU 0.")]),
    ("download_models.py",
     "Run by the setup scripts: downloads both models and tells you whether the GPU will be used.",
     [('"""Download the two', "Docstring and imports."),
      ("def main", "Work in the project folder (where the game looks for the models)."),
      ("if os.path.exists(config.FACE_MODEL)", "Download the face model if missing."),
      ("from ultralytics import YOLO", "Loading YOLO once downloads the pose model."),
      ("import torch", "Report: GPU (and TensorRT engine), NVIDIA GPU that PyTorch cannot use (driver too old), "
                       "or CPU."),
      ('if __name__ == "__main__":', "Run main() when started directly.")]),
    ("setup.ps1",
     "Windows setup (double-click `setup.bat`, which runs this with permission to execute scripts).",
     [("# All For One - one-time setup", "What it does and how to start it."),
      ("param(", "Options -TensorRT / -NoTensorRT (skip the question); stop on errors; work in the script's "
                 "folder."),
      ("function Step", "Helpers: print a step title; stop with a message if the last command failed."),
      ("$TorchVersion", "The pinned PyTorch versions."),
      ('Step "1/6', "Find Python 3.12 (`py -3.12`, `python`, or the default install folder); if missing, "
                    "offer `winget install Python.Python.3.12`."),
      ('Step "2/6', "Rebuild .venv if it was made with another Python version; create it (or reuse it); "
                    "update pip."),
      ('Step "3/6', "PyTorch: CUDA build if `nvidia-smi` exists, else the CPU build."),
      ('Step "4/6', "The game's packages from requirements.txt."),
      ('Step "5/6', "Optional TensorRT: ask (or use the option), install, build the engine."),
      ('Step "6/6', "Download the models and report GPU/CPU."),
      ("Done!", "Tell the user how to start the game.")]),
    ("setup.sh",
     "Linux setup. Same steps as setup.ps1 plus Linux checks (venv package, OpenCV system library, webcam "
     "permission).",
     [("#!/usr/bin/env bash", "Run with bash; what it does and how to start it."),
      ("set -euo pipefail", "Stop on any error, unset variable or failed pipe; work in the script's folder."),
      ("TRT=ask", "Read the --tensorrt / --no-tensorrt options."),
      ("TORCH=(", "Pinned PyTorch versions and print helpers."),
      ('step "1/6', "Find Python 3.12: `python3.12`/`python3`/`python`, else with `uv` if installed, else "
                    "offer to install uv (or show the deadsnakes alternative) and stop."),
      ('step "2/6', "Rebuild .venv if it was made with another Python version; create it; if that fails, "
                    "explain the missing python3.12-venv package."),
      ('step "3/6', "PyTorch: CUDA build if an NVIDIA GPU answers `nvidia-smi -L`, else the CPU build."),
      ('step "4/6', "Game packages; check that OpenCV can load (libGL) and explain the fix if not."),
      ('step "5/6', "Optional TensorRT: ask only in an interactive terminal."),
      ('step "6/6', "Download the models and report GPU/CPU."),
      ("# webcam check", "Warn if there is no /dev/video* device or no permission to read it."),
      ("Done! Start the game", "Tell the user how to start the game.")]),
    ("requirements.txt",
     "The pinned versions of the game's packages (PyTorch is installed separately by the setup scripts).",
     [("# Packages the game needs", "Why the versions are pinned and why PyTorch is not in this list."),
      ("pygame==", "pygame and numpy with their exact tested versions."),
      ("# Both OpenCV packages", "Both OpenCV packages at one version (they share the `cv2` module)."),
      ("mediapipe==", "The two AI libraries.")]),
]


# ======================================================================= PART IV + V
SECTIONS_AFTER = [
    ("h1", "Part IV - Reference"),
    ("h2", "14. Every setting in config.py"),
    ("p", "Read straight from the file when this guide was built. Grey rows are the section headers of the file."),
    ("config",),
    ("h2", "15. How do I...?"),
    ("p", "Most player-facing values can be changed in the **OPTIONS** screen without touching code; the table "
          "lists where everything lives in the code."),
    ("table", [["I want to...", "Change this"],
               ["set the game up on a new computer", "Windows: `setup.bat`. Linux: `./setup.sh`. Then `run.bat` / "
                                                     "`./run.sh`."],
               ["tune mouth, legs, physics while playing", "The OPTIONS screen (saved in `settings.json`)."],
               ["offer a new value in the Options screen", "Add a `Setting` to `SETTINGS` in settings.py with a "
                                                           "safe range. The code must read that config value when "
                                                           "it uses it (not copy it at start-up)."],
               ["rebuild this PDF after code changes", "`pip install -r requirements-dev.txt` once, then "
                                                       "`python tools/docs/make_docs.py`. Text is in "
                                                       "`tools/docs/content.py`."],
               ["update a package version", "Change the pin in requirements.txt, run the setup again, test."],
               ["add a map", "Put `background-x.png` and `foreground-x.png` (transparent = air) in `assets/` and "
                             "add an entry to `MAPS` in config.py with a spawn point (fractions of the map) and "
                             "optionally a `scale`. The flag and the menu picture are automatic."],
               ["add a windmill to a map", "Add a `\"windmill\"` entry (tower and rotor pictures, hub in image "
                                           "pixels, `rps`) to the map in `MAPS`, like the Windmill map."],
               ["change the rotor speed / slipperiness", "`\"rps\"` of the map in `MAPS` / "
                                                         "`ROTOR_WALKABLE_SLOPE`."],
               ["clear the score board", "Delete `scores.json` (or remove lines from it)."],
               ["make jumps stronger / weaker", "`LEG_MAX_SPEED` (how fast legs straighten) or `GRAVITY`."],
               ["change who controls which leg", "`CONTROL_SCHEMES` - each row is (player, limb, leg)."],
               ["make the mouth easier to trigger", "Lower `MOUTH_OPEN_T` (and keep `MOUTH_CLOSE_T` about 0.1 lower)."],
               ["make legs smoother / more responsive", "`ANGLE_EMA` (lower = smoother, slower)."],
               ["change the character size", "`CHARACTER_FRACTION` (relative to the map height)."],
               ["make a map bigger relative to the character", "That map's `\"scale\"` in `MAPS`."],
               ["change the player colours", "`PLAYER_COLORS_BGR` (blue, green, red order!)."],
               ["switch head-tilt direction", "`HEAD_TILT_INVERT`."],
               ["start in fullscreen", "`START_FULLSCREEN = True`."],
               ["use the camera without mirroring", "`MIRROR_CAMERA = False`."]], [0.32, 0.68]),
    ("h2", "16. Glossary"),
    ("table", [["Word", "Meaning here"],
               ["anchor", "The point where a sticky foot is glued to the rock."],
               ["bilinear interpolation", "Blending the 4 nearest table values by distance, for smooth results "
                                          "between pixels."],
               ["blit", "Copy (paste) one picture onto another (pygame)."],
               ["canvas", "The fixed-size picture every scene draws on."],
               ["delta time (dt)", "Seconds since the last frame/step; movement = speed x dt."],
               ["EMA", "Exponential moving average: smooth = smooth + a x (new - smooth)."],
               ["Gauss-Seidel", "Fixing constraints one after another, repeated a few times."],
               ["hysteresis", "Two thresholds (on/off) with a gap so a value near the edge does not flicker."],
               ["inference", "Running a trained AI model on new input."],
               ["keypoint / landmark", "A named point found by a model (body joint / face point)."],
               ["kinematics", "Computing joint positions from angles and lengths."],
               ["lock", "Makes one thread wait while another changes shared data."],
               ["normal", "Unit vector pointing straight out of a surface."],
               ["pinned version", "An exact package version in requirements.txt (==), so every install is the "
                                  "same."],
               ["PBD", "Position-based dynamics: move, correct positions, derive velocity."],
               ["SDF", "Signed distance field: distance to the nearest surface, negative inside."],
               ["substep", "One of several smaller physics steps inside one frame."],
               ["tangent", "Direction along a surface (normal turned 90 degrees)."],
               ["thread", "A part of the program that runs at the same time as others."],
               ["TensorRT / FP16", "NVIDIA's optimiser for running networks on its GPUs / 16-bit numbers."],
               ["virtual environment (.venv)", "A private Python installation for one project, with its own "
                                              "packages."]],
     [0.26, 0.74]),

    ("h1", "Part V - How the AI models work"),
    ("p", "This part explains the two models at the level needed to use them well, without the mathematics of "
          "training."),
    ("h2", "17. Pose detection: YOLO"),
    ("p", "**What it does.** Given a picture, `yolo26n-pose` returns for every person a box, a person-confidence "
          "and 17 keypoints (x, y and a confidence 0..1 for each). It is a *neural network*: millions of numbers "
          "(weights) learned by training on the COCO dataset, where people were labelled by hand with these 17 "
          "points."),
    ("p", "**How it works, roughly.** YOLO stands for *You Only Look Once*: the whole picture goes through the "
          "network a single time and all people come out together, which is why it is fast enough for live video."),
    ("ol", ["The frame is resized to fit 640 x 640 (padding the rest) and turned into numbers.",
            "The *backbone* (stacked convolution layers) turns the picture into feature maps: coarse grids where "
            "each cell describes what is in its region - edges first, then shapes, then body parts.",
            "The *neck* combines feature maps of different sizes, so both near (big) and far (small) people are "
            "found.",
            "The *head* predicts, for each grid cell, whether a person is centred there, the box, and the 17 "
            "keypoint positions with their confidences.",
            "Overlapping duplicates are removed, leaving one result per person. (Ultralytics designs the YOLO26 "
            "family to do this inside the network, without a separate clean-up step.)"]),
    ("p", "The **n** means *nano*, the smallest and fastest size. Bigger sizes (s, m, l, x) are more accurate on "
          "small or far people but slower. **Keypoint confidence** drops for hidden or blurry joints; the game "
          "ignores keypoints below 0.5, and a limb with a missing joint simply keeps its last angle."),
    ("h3", "Speed: CPU, GPU and TensorRT"),
    ("p", "A network is mostly multiplication of large tables of numbers, which a graphics card does in parallel. "
          "With the CUDA build of PyTorch the model runs on the RTX GPU. **TensorRT** goes further: it compiles the "
          "network for *this specific* GPU - merging layers, choosing the fastest routines and using 16-bit "
          "numbers (FP16) instead of 32-bit. That is why the `.engine` file only works on the computer it was built "
          "on."),
    ("table", [["Backend", "Pose model per frame", "Whole vision step per frame"],
               ["CPU", "about 51 ms", "about 110 ms (9 FPS)"],
               ["GPU (CUDA PyTorch)", "about 12 ms", "about 33 ms"],
               ["TensorRT FP16", "about 5 ms", "about 23 ms (40+ FPS)"]], [0.34, 0.33, 0.33]),
    ("p", "Measured on the development laptop (RTX 4070 Laptop) on a sample photo; the rest of the vision step "
          "is mostly the face model, which runs on the CPU."),
    ("h2", "18. Face landmarks: MediaPipe Face Landmarker"),
    ("p", "**What it does.** For every face it returns **478 landmarks**: 468 points of a face mesh (outline, "
          "eyebrows, eyes, nose, lips) plus 10 iris points, each as a position relative to the picture. It can "
          "also return 52 *blendshape* scores such as `jawOpen` (your original test script printed this); the game "
          "uses the simpler lip-gap ratio instead, because it also works on the head-crop fallback."),
    ("p", "**How it works.** It is two networks in a row:"),
    ("ol", ["A small, very fast **face detector** (BlazeFace) finds where faces are and how they are rotated.",
            "Each face is cut out, straightened and resized, and a **landmark network** predicts the positions of "
            "all 478 points at once (it *regresses* the coordinates: the output layer simply is the list of x, y, "
            "z values)."]),
    ("p", "In **VIDEO mode** (used on the full frame) it *tracks*: the landmarks of the previous frame tell it "
          "where the face is now, so the detector can often be skipped - faster and steadier. That is why it needs "
          "increasing timestamps. **IMAGE mode** (used for head crops) treats every picture independently, which "
          "is right there because consecutive crops can come from different people."),
    ("h2", "19. Limits to keep in mind"),
    ("ul", ["**Distance**: the face model is meant for faces within about two metres; far away, faces get too "
            "small. The head-crop fallback enlarges small faces, which helps.",
            "**Light and blur**: dark rooms and fast arm movement lower keypoint confidence; limbs then hold their "
            "last angle.",
            "**Overlap**: players standing behind each other can swap numbers or hide limbs; standing side by side "
            "works best.",
            "**Side view**: a head turned far sideways hides one ear and much of the mouth; head tilt falls back "
            "to the eyes, the mouth may be lost briefly (kept for 0.5 s).",
            "**Mirroring**: the model's own left/right labels can be wrong on a mirrored picture - the code uses "
            "screen positions instead (chapter 9)."]),
    ("note", "Everything in this guide refers to the code as it is in the repository at the time of writing. "
             "The tables in Part III find their line numbers automatically from the real files, so they match the "
             "listings."),
]
