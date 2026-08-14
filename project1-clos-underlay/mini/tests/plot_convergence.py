#!/usr/bin/env python3
"""Chart BGP detection time, baseline vs BFD. Emits SVG directly - no dependencies."""

base = [6.76, 6.92, 6.86]
bfd  = [0.84, 0.77, 0.87]
bm, fm = sorted(base)[1], sorted(bfd)[1]

W, H = 700, 450
ML, MR, MT, MB = 80, 30, 70, 90
PW, PH = W-ML-MR, H-MT-MB
YMAX = 8.0
def y(v): return MT + PH - (v/YMAX)*PH

p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
     f'viewBox="0 0 {W} {H}" font-family="DejaVu Sans, Arial, sans-serif">',
     f'<rect width="{W}" height="{H}" fill="white"/>',
     f'<text x="{W/2}" y="26" text-anchor="middle" font-size="15" font-weight="bold">'
     'BGP peer-failure detection: default timers vs BFD</text>',
     f'<text x="{W/2}" y="46" text-anchor="middle" font-size="11" fill="#555">'
     'leaf1 detecting spine2 unresponsive (docker pause), n=3, dots = individual trials</text>']

for i in range(9):
    yy = y(i)
    p.append(f'<line x1="{ML}" y1="{yy:.1f}" x2="{ML+PW}" y2="{yy:.1f}" stroke="#ddd"/>')
    p.append(f'<text x="{ML-10}" y="{yy+4:.1f}" text-anchor="end" font-size="11" fill="#333">{i}</text>')
p.append(f'<line x1="{ML}" y1="{MT}" x2="{ML}" y2="{MT+PH}" stroke="#333" stroke-width="1.5"/>')
p.append(f'<line x1="{ML}" y1="{MT+PH}" x2="{ML+PW}" y2="{MT+PH}" stroke="#333" stroke-width="1.5"/>')
p.append(f'<text x="20" y="{MT+PH/2}" text-anchor="middle" font-size="12" '
         f'transform="rotate(-90 20 {MT+PH/2})">Detection time (seconds)</text>')

for i,(lab,sub,med,raw,col) in enumerate([
        ("Default BGP timers","hold 9s / keepalive 3s",bm,base,"#c0392b"),
        ("BFD enabled","300ms x 3",fm,bfd,"#27ae60")]):
    cx = ML + PW*(0.28 + 0.44*i); bw = 110; yy = y(med)
    p.append(f'<rect x="{cx-bw/2:.1f}" y="{yy:.1f}" width="{bw}" height="{MT+PH-yy:.1f}" fill="{col}" rx="2"/>')
    p.append(f'<text x="{cx:.1f}" y="{yy-10:.1f}" text-anchor="middle" font-size="14" font-weight="bold">{med:.2f} s</text>')
    for v in raw:
        p.append(f'<circle cx="{cx:.1f}" cy="{y(v):.1f}" r="3" fill="#111"/>')
    p.append(f'<text x="{cx:.1f}" y="{MT+PH+22:.1f}" text-anchor="middle" font-size="12" font-weight="bold">{lab}</text>')
    p.append(f'<text x="{cx:.1f}" y="{MT+PH+38:.1f}" text-anchor="middle" font-size="10" fill="#555">{sub}</text>')

red = 100*(1-fm/bm)
p.append(f'<text x="{W/2}" y="{H-18}" text-anchor="middle" font-size="12" '
         f'font-weight="bold" fill="#27ae60">{red:.0f}% reduction in detection time</text>')
p.append('</svg>')

open("docs/convergence-detection.svg","w").write("\n".join(p))
print(f"saved docs/convergence-detection.svg  baseline={bm:.2f}s bfd={fm:.2f}s reduction={red:.0f}%")
