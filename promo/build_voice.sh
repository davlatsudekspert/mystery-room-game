#!/usr/bin/env bash
# English narration (offline neural TTS, piper + the openly licensed voice en_GB-cori-high) and the sting.
#   PROMO_WORK=/tmp/promo_work promo/build_voice.sh
# Needs: python3 -m venv + pip (piper-tts), network access to PyPI and huggingface.co for the first run only.
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${PROMO_WORK:-/tmp/promo_work}"
mkdir -p "$WORK/voice" "$WORK/piper"
if [ ! -x "$WORK/piper/venv/bin/piper" ]; then
	python3 -m venv "$WORK/piper/venv"
	"$WORK/piper/venv/bin/pip" install -q piper-tts
fi
B=https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/cori/high
for e in onnx onnx.json; do [ -f "$WORK/piper/en_GB-cori-high.$e" ] || curl -sSL -o "$WORK/piper/en_GB-cori-high.$e" "$B/en_GB-cori-high.$e"; done
while IFS='|' read -r id txt; do
	echo "$txt" | "$WORK/piper/venv/bin/piper" -m "$WORK/piper/en_GB-cori-high.onnx" --length-scale 1.18 --noise-scale 0.5 \
		--noise-w-scale 0.6 --sentence-silence 0.45 -f "$WORK/voice/raw_$id.wav" 2>/dev/null
	# slow, calm, a little room: 48 kHz, low cut, a touch of body, short reverb
	sox "$WORK/voice/raw_$id.wav" -r 48000 "$WORK/voice/$id.wav" gain -9 highpass 90 equalizer 180 1.0q 2 reverb 18 40 70 gain -n -3 pad 0 0.3
	rm -f "$WORK/voice/raw_$id.wav"
done < "$ROOT/promo/narration_lines.txt"
# Final sting (original, synthesized with sox): sub boom + dark minor pad + a short high shimmer, long tail.
sox -n -c 2 "$WORK/sting_a.wav" synth 4.5 sine 46 sine 92 fade h 0.02 4.5 3.8 gain -4
sox -n -c 2 "$WORK/sting_b.wav" synth 4.5 sine 220 sine 261.6 sine 329.6 tremolo 0.4 30 fade h 1.2 4.5 2.8 gain -22
sox -n -c 2 "$WORK/sting_c.wav" synth 3 sine 1760 sine 2349 fade h 0.01 3 2.5 gain -30 pad 0.15 0
sox -m "$WORK/sting_a.wav" "$WORK/sting_b.wav" "$WORK/sting_c.wav" -r 48000 -c 2 "$WORK/sting.wav" reverb 40 50 100 gain -n -3
rm -f "$WORK"/sting_[abc].wav
