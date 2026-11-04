"""Camera picker: a web page with the built scene (scene.glb) that you can orbit, pan and zoom, nothing else.
It opens at the recommended camera of each view with the same lens and frame as the Blender render; the camera
you end at is shown as `x, y, z, tx, ty, tz, lens` (copy it into the scene file, or `steelfig set-camera` writes
it). `steelfig view <out_dir>` writes viewer.html and serves the folder on http://localhost:<port>/viewer.html."""
import os, json, sys, re, http.server, socketserver, threading, webbrowser

THREE = "0.160.0"
PAGE = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>steelfig camera</title>
<style>
 html,body{margin:0;height:100%;background:#f4f4f5;font:13px/1.4 -apple-system,Helvetica,Arial,sans-serif;color:#222}
 #wrap{position:fixed;inset:0;display:flex;flex-direction:column}
 #bar{display:flex;gap:10px;align-items:center;padding:8px 12px;background:#fff;border-bottom:1px solid #ddd}
 #stage{flex:1;position:relative;display:flex;align-items:center;justify-content:center}
 canvas{background:#fff;box-shadow:0 0 0 1px #ccc}
 code{font:12px/1 ui-monospace,Menlo,monospace;background:#eee;padding:4px 6px;border-radius:3px}
 button,select{font:inherit;padding:4px 8px}
 #hint{color:#666}
</style></head><body><div id="wrap">
<div id="bar">
 <select id="view"></select>
 <code id="cam">—</code>
 <button id="copy">copy</button>
 <button id="reset">reset</button>
 <span id="hint">drag: orbit · right-drag / shift-drag: pan · wheel: zoom (moves the camera, lens stays)</span>
</div>
<div id="stage"></div></div>
<script type="importmap">{"imports":{"three":"https://unpkg.com/three@__V__/build/three.module.js","three/addons/":"https://unpkg.com/three@__V__/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const VIEWS = __VIEWS__;  // [{name, cam:[x,y,z,tx,ty,tz,lens], res:[w,h]}]
const SENSOR = 36;        // Blender default sensor width, mm (sensor fit AUTO: fov on the wider side)
const stage = document.getElementById('stage'), sel = document.getElementById('view'), out = document.getElementById('cam');
const renderer = new THREE.WebGLRenderer({antialias:true, preserveDrawingBuffer:true});
renderer.setPixelRatio(window.devicePixelRatio); stage.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0xffffff);
scene.add(new THREE.HemisphereLight(0xffffff, 0xb9bcc0, 1.1));
const sun = new THREE.DirectionalLight(0xffffff, 1.6); sun.position.set(5,-8,10); scene.add(sun);
const sun2 = new THREE.DirectionalLight(0xffffff, 0.5); sun2.position.set(-6,6,4); scene.add(sun2);
const camera = new THREE.PerspectiveCamera(40, 1.5, 0.05, 2000); camera.up.set(0,0,1);
const controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = false; controls.screenSpacePanning = true;
let cur = 0, aspect = 1.5;
function size(){ const W = Math.max(80, stage.clientWidth - 24), H = Math.max(60, stage.clientHeight - 24); let w = W, h = W/aspect; if (h > H){ h = H; w = H*aspect; }
  renderer.setSize(w, h, false); renderer.domElement.style.width = w+'px'; renderer.domElement.style.height = h+'px'; camera.aspect = aspect; setLens(lens); }
let lens = 40;
function setLens(l){ lens = l; const hfov = 2*Math.atan(SENSOR/2/l); camera.fov = 2*Math.atan(Math.tan(hfov/2)/aspect)*180/Math.PI; camera.updateProjectionMatrix(); }
function apply(v){ const c = v.cam; aspect = v.res ? v.res[0]/v.res[1] : 1.5; size(); camera.position.set(c[0],c[1],c[2]); controls.target.set(c[3],c[4],c[5]); setLens(c[6]); controls.update(); }
function readout(){ const p = camera.position, t = controls.target; const s = [p.x,p.y,p.z,t.x,t.y,t.z].map(v=>v.toFixed(3)).join(', ') + ', ' + lens.toFixed(0);
  out.textContent = s; window.cam = {view: VIEWS[cur].name, cam: [p.x,p.y,p.z,t.x,t.y,t.z,lens].map(v=>+v.toFixed(4))}; }
VIEWS.forEach((v,i)=>{ const o = document.createElement('option'); o.value = i; o.textContent = v.name; sel.appendChild(o); });
sel.onchange = ()=>{ cur = +sel.value; apply(VIEWS[cur]); readout(); };
document.getElementById('reset').onclick = ()=>{ apply(VIEWS[cur]); readout(); };
document.getElementById('copy').onclick = ()=>{ navigator.clipboard.writeText(out.textContent); };
window.addEventListener('resize', size);
new GLTFLoader().load('scene.glb', g => { scene.add(g.scene); if (VIEWS.length){ apply(VIEWS[cur]); } readout(); animate(); }, undefined, e => { out.textContent = 'could not load scene.glb: ' + e; });
function animate(){ requestAnimationFrame(animate); controls.update(); readout(); renderer.render(scene, camera); }
</script></body></html>
"""


def views_of(out_dir):
    sc = json.load(open(os.path.join(out_dir, "scene.json"), encoding="utf-8"))
    res = None
    try:
        from steelfig import style; res = style.load(sc.get("style"))["render"]["resolution"]
    except Exception: pass
    vs = []
    for v in sc.get("view", []):
        cam = None
        jp = os.path.join(out_dir, v["name"] + ".json")
        if os.path.exists(jp): cam = json.load(open(jp, encoding="utf-8")).get("camera")
        if cam is None and isinstance(v.get("camera"), list): cam = v["camera"]
        if cam: vs.append(dict(name=v["name"], cam=cam, res=v.get("res") or res))
    return vs


def write(out_dir):
    p = os.path.join(out_dir, "viewer.html")
    open(p, "w", encoding="utf-8").write(PAGE.replace("__V__", THREE).replace("__VIEWS__", json.dumps(views_of(out_dir))))
    return p


def serve(out_dir, port=8765, open_browser=False):
    write(out_dir)
    os.chdir(out_dir)
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    socketserver.TCPServer.allow_reuse_address = True
    while True:
        try: httpd = socketserver.TCPServer(("127.0.0.1", port), Q); break
        except OSError: port += 1
    url = "http://127.0.0.1:%d/viewer.html" % port
    print("viewer:", url, "(Ctrl-C to stop)"); sys.stdout.flush()
    if open_browser: webbrowser.open(url)
    try: httpd.serve_forever()
    except KeyboardInterrupt: pass


def set_camera(scene_path, view, cam):
    """write `camera = [x, y, z, tx, ty, tz, lens]` into the named [[view]] of a scene file."""
    s = open(scene_path, encoding="utf-8").read()
    cam = [float(x) for x in (cam.split(",") if isinstance(cam, str) else cam)]
    line = "camera = [%s]" % ", ".join(("%.3f" % v).rstrip("0").rstrip(".") if i < 6 else "%g" % v for i, v in enumerate(cam))
    pat = re.compile(r'(\[\[view\]\]\s*\nname\s*=\s*"%s"\s*\n(?:(?!\[\[).*\n)*?)camera\s*=\s*\[[^\]]*\]' % re.escape(view))
    new, n = pat.subn(lambda m: m.group(1) + line, s)
    if not n: raise SystemExit("view %r with a camera line not found in %s" % (view, scene_path))
    open(scene_path, "w", encoding="utf-8").write(new); print("set", view, line)
