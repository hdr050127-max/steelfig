# Pitfalls learned (D2 2026-10-09, lab 2026-10-29, D3 2026-11-03)

- **Z purlin orientation.** `zsec` puts the bottom flange ON the line and the web along `up`; give `up` the roof
  normal (not +z) on a sloping rafter, otherwise the purlin leans or pierces the chord. The first D2 samples had
  purlins running through the top chord for this reason.
- **Freestyle colour is linear.** A line colour of 0.06 renders mid grey after the view transform. Engineering
  outlines must be black: `setup()` uses (0, 0, 0). (Knowledge base: practices/blender-freestyle-linear-color.)
- **Render engine name.** Blender 5.2 lists only `BLENDER_EEVEE`; `setup()` tries that then `BLENDER_EEVEE_NEXT`
  (4.2–4.x). Cycles is not needed for this flat style.
- **Boolean cuts need the EXACT solver** and solid cutters (`solid_prism`, `box`); trimming diagonals at a chord
  face with a thin box leaves slivers. Delete cutters afterwards (`delete`).
- **Member ends on sloping faces**: use `cut0` / `cut1` planes on `isec` / `prism` / `shs`, not a longer member
  poking through. A column under a rafter: `cut1=(point_on_roof_line, roof_normal)`.
- **`top=True` for rafters.** Model the rafter line as the TOP flange (the roof surface) so stepped haunches of
  different depths share one flush top; purlins then sit on `top(x)` exactly.
- **Crop and anchors.** `render()` crops to the meshes; anchors outside the meshes (arrow tails, dimension
  offsets, waves, grid bubbles) must be passed in `bounds_extra` or they fall outside the image. Anchors are
  normalised to the cropped image, so a figure is re-rendered whenever the geometry or camera changes, and the
  overlay script is rerun after every render (it reads the JSON).
- **quick mode first.** EEVEE renders these scenes in seconds, but boolean cuts and big scenes add up; check composition with `quick` (half
  size), then render full. Camera from the command line: `cam=x,y,z,tx,ty,tz,lens`.
- **Transparent PNG → JPEG.** The PNG has a transparent film; `overlay.flatten()` puts white behind it and saves a
  JPEG (~10× smaller) for the report. The D2 report kept PNGs and grew to 16 MB.
- **Balloon placement is manual.** dx, dy in cm from the anchor; look at the preview PDF and move balloons off
  members and off each other. Leaders should not cross; put balloons outside the drawing where possible.
- **Repeated part, one number.** `("anchor", "", dx, dy, 3)` draws balloon 3 again without a key line.
- **The preview compiles from the report directory** (`cwd=rep`) so `images/blender/…` resolves the same way as in
  the report. The report preamble needs `arrows.meta`, `\definecolor{acc}`, and the `\ball` macro (`overlay.PRE`).
- **Hatching on section cuts**: `hatch_mat(plane=...)` matches the viewing direction of the cut; for a cut seen
  along y use "xz".
- **Keep the figure script and overlay script next to the report generator** (e.g. `tmp/<job>/blender/`), with the
  render directory outside the report so re-renders do not litter it.
- **Blender's Python is its own**: nothing from the system Python (PIL, numpy versions) is available inside the
  figure script; do image post-processing in `overlay.py` (system Python).
- **Model import draws nothing for a member** when its PROP name is neither a catalogue designation nor in
  `sections`; the build prints `WARNING build_model: no section for members […]`. Microstran names like
  `200x200x9.0 SHS` are matched after normalising, but `Top_chord` needs a mapping entry.
- **Section-cut faces** get the hatch material through the boolean modifier's material transfer; the cutter is a
  50 m box on the +normal side, so put the point exactly on the cut plane and keep the scene inside 50 m of it.
- **A boolean cut of a hollow section** can leave a diagonal Freestyle line across the inner face (its quads are
  re-triangulated); crease angle 135° hides most of them. Rotate the view or hide the far wall if one shows.
- **Hidden lines showing through a long member** (extra lines on a flat web, edges of members behind it): Freestyle
  loses occluders that are very long and thin. `build_scene.py` calls `B.split_long_faces()` before rendering; a
  Python API figure with long members should call it too, after any `boolean_cut` and before the views. Neither
  triangulating the faces nor `use_culling = False` cures it.
- **`crop` on a view** is the bounding box of the two points as projected on screen and cannot go beyond the camera
  frame: on a perspective view pick points that differ along the screen's horizontal, and on an orthographic view raise
  `scale` until the whole crop is in frame (a plan cut off at one side means `scale` is too small).
