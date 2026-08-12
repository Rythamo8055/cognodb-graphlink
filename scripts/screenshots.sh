#!/usr/bin/env bash
#
# Capture UI screenshots for the README using headless Firefox, and
# optionally stitch them into a narrated-style demo mp4 with ffmpeg.
#
# Usage:
#   ./scripts/screenshots.sh            # PNGs only
#   ./scripts/screenshots.sh --video    # PNGs + out.mp4
#
# Requires the app to be running at http://127.0.0.1:8091, e.g.:
#   MOCK_DB=1 uvicorn main:app --port 8091
set -euo pipefail

APP_URL="${APP_URL:-http://127.0.0.1:8091}"
OUT_DIR="images"
WIDTH=1440
HEIGHT=900
FIREFOX="/usr/bin/firefox"
FFMPEG="/usr/bin/ffmpeg"
MAKE_VIDEO=0

for arg in "$@"; do
  case "$arg" in
    --video) MAKE_VIDEO=1 ;;
    *)
      echo "unknown flag: $arg (expected --video)" >&2
      exit 2
      ;;
  esac
done

if [[ ! -x "$FIREFOX" ]]; then
  echo "firefox not found at $FIREFOX" >&2
  exit 1
fi

# Headless firefox needs a software-rendering profile here, otherwise the
# SWGL compositor fails and the capture comes out blank or hangs.
PROFILE="$(mktemp -d /tmp/graphlink-ff.XXXXXX)"
cat > "$PROFILE/user.js" <<EOF
user_pref("gfx.webrender.software", true);
user_pref("gfx.webrender.enabled", true);
user_pref("layers.acceleration.disabled", true);
user_pref("gfx.canvas.accelerated", false);
user_pref("gfx.offscreencanvas.enabled", false);
user_pref("webgl.disabled", true);
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.startup.homepage_override.mozilla.org", "about:blank");
EOF

echo "checking $APP_URL/health ..."
if ! curl -fsS "$APP_URL/health" >/dev/null 2>&1; then
  echo "the app is not running at $APP_URL" >&2
  echo "start it first, e.g.:" >&2
  echo "  MOCK_DB=1 uvicorn main:app --port 8091" >&2
  exit 1
fi
echo "app is up (mode: $(curl -fsS "$APP_URL/health" | python3 -c 'import sys,json; print(json.load(sys.stdin)["mode"])'))"

mkdir -p "$OUT_DIR"
OUT_DIR_ABS="$(cd "$OUT_DIR" && pwd)"

shot() {
  local name="$1" url="$2"
  local file="$OUT_DIR_ABS/$name.png"
  echo "capturing $file <- $url"
  # /snap server-renders the full view inline, so the capture is
  # deterministic (no async-fetch race).
  LIBGL_ALWAYS_SOFTWARE=1 "$FIREFOX" --headless --no-remote --profile "$PROFILE" \
    --screenshot "$file" --window-size="$WIDTH,$HEIGHT" "$APP_URL$url" >/dev/null 2>&1
  echo "  ${name}: $(stat -c %s "$file") bytes"
}

shot screenshot-home-investors "/snap?domain=investors&view=home"
shot screenshot-node            "/snap?domain=investors&view=node&node=PayKart"
shot screenshot-path            "/snap?domain=investors&view=path&from=Divya%20Menon&to=Ananya%20Rao"
shot screenshot-education       "/snap?domain=education&view=home"
shot screenshot-healthcare      "/snap?domain=healthcare&view=home"

rm -rf "$PROFILE"

echo
echo "captured:"
for f in "$OUT_DIR"/screenshot-*.png; do
  printf '  %-45s %s\n' "$f" "$(stat -c %s "$f") bytes"
done

if [[ "$MAKE_VIDEO" -eq 1 ]]; then
  if [[ ! -x "$FFMPEG" ]]; then
    echo "ffmpeg not found at $FFMPEG; skipping video" >&2
    exit 1
  fi
  ENCODERS="$("$FFMPEG" -hide_banner -encoders 2>/dev/null)"
  if [[ "$ENCODERS" == *libx264* ]]; then
    ENCODER="libx264"
  else
    ENCODER="mpeg4"
  fi
  echo "building out.mp4 (1 s per screenshot, encoder: $ENCODER) ..."
  "$FFMPEG" -y \
    -loop 1 -t 1 -i "$OUT_DIR_ABS/screenshot-home-investors.png" \
    -loop 1 -t 1 -i "$OUT_DIR_ABS/screenshot-node.png" \
    -loop 1 -t 1 -i "$OUT_DIR_ABS/screenshot-path.png" \
    -loop 1 -t 1 -i "$OUT_DIR_ABS/screenshot-education.png" \
    -loop 1 -t 1 -i "$OUT_DIR_ABS/screenshot-healthcare.png" \
    -filter_complex "[0:v][1:v][2:v][3:v][4:v]concat=n=5:v=1:a=0[v]" \
    -map "[v]" -c:v "$ENCODER" -b:v 2M -pix_fmt yuv420p \
    out.mp4 >/dev/null 2>&1
  echo "wrote out.mp4 ($(stat -c %s out.mp4) bytes, $(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 out.mp4 2>/dev/null || echo '?') s)"
fi

echo
echo "checklist:"
echo "  [ ] images/screenshot-home-investors.png - investors tab home"
echo "  [ ] images/screenshot-node.png           - PayKart node card"
echo "  [ ] images/screenshot-path.png           - pathfinder view"
echo "  [ ] images/screenshot-education.png      - education domain"
echo "  [ ] images/screenshot-healthcare.png     - healthcare domain"
[[ "$MAKE_VIDEO" -eq 1 ]] && echo "  [ ] out.mp4 - demo recording from the PNGs"
