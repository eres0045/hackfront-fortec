#!/usr/bin/env bash
# WhyCode demo video: terminal screenshots + Fish Audio narration + captions.
# Sections: title / Q1 / Q2 / refusal / closing. Holds = narration + tail.
set -euo pipefail
cd "$(dirname "$0")"
rm -f narration/v4b.mp3

D1=$(ffprobe -v error -show_entries format=duration -of csv=p=0 narration/v1.mp3)
D2=$(ffprobe -v error -show_entries format=duration -of csv=p=0 narration/v2.mp3)
D3=$(ffprobe -v error -show_entries format=duration -of csv=p=0 narration/v3.mp3)
D4=$(ffprobe -v error -show_entries format=duration -of csv=p=0 narration/v4.mp3)
D5=$(ffprobe -v error -show_entries format=duration -of csv=p=0 narration/v5.mp3)
S1=$(python3 -c "print($D1+2)")
S2=$(python3 -c "print($D2+1.5)")
S3=$(python3 -c "print($D3+1.5)")
S4=$(python3 -c "print($D4+1.5)")
S5=$(python3 -c "print($D5+2)")
T2=$(python3 -c "print($S1)")
T3=$(python3 -c "print($S1+$S2)")
T4=$(python3 -c "print($S1+$S2+$S3)")
T5=$(python3 -c "print($S1+$S2+$S3+$S4)")
TOT=$(python3 -c "print($S1+$S2+$S3+$S4+$S5)")
echo "sections: $S1 $S2 $S3 $S4 $S5 total $TOT"

i=0
for spec in "title $S1" "q1 $S2" "q2 $S3" "refusal $S4" "closing $S5"; do
  set -- $spec
  ffmpeg -y -v error -loop 1 -i shot-$1.png -t "$2" -r 30 \
    -c:v libx264 -pix_fmt yuv420p seg-$1.mp4
done
printf "file 'seg-title.mp4'\nfile 'seg-q1.mp4'\nfile 'seg-q2.mp4'\nfile 'seg-refusal.mp4'\nfile 'seg-closing.mp4'\n" > list.txt
ffmpeg -y -v error -f concat -safe 0 -i list.txt -c copy assembled.mp4

printf 'WhyCode — ask a codebase why it is the way it is' > cap0.txt
printf 'A real answer, with cited evidence' > cap1.txt
printf 'Same for template tags — traced to its ticket' > cap2.txt
printf 'No evidence? It refuses instead of inventing' > cap3.txt
printf 'WhyCode by FORTEC — repo on screen' > cap4.txt

MS1=$(python3 -c "print(int($S1*1000))")
MS2=$(python3 -c "print(int(($S1+$S2)*1000))")
MS3=$(python3 -c "print(int(($S1+$S2+$S3)*1000))")
MS4=$(python3 -c "print(int(($S1+$S2+$S3+$S4)*1000))")
FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
# Step 1: mux narration (video copied, audio mixed).
ffmpeg -y -v error -i assembled.mp4 \
  -i narration/v1.mp3 -i narration/v2.mp3 -i narration/v3.mp3 \
  -i narration/v4.mp3 -i narration/v5.mp3 \
  -filter_complex "[1:a]adelay=0|0[a1];[2:a]adelay=${MS1}|${MS1}[a2];[3:a]adelay=${MS2}|${MS2}[a3];[4:a]adelay=${MS3}|${MS3}[a4];[5:a]adelay=${MS4}|${MS4}[a5];[a1][a2][a3][a4][a5]amix=inputs=5:normalize=0,apad,atrim=0:${TOT}[aout]" \
  -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 160k video-audio.mp4
# Step 2: burn captions (video re-encoded).
ffmpeg -y -v error -i video-audio.mp4 \
  -vf "drawtext=fontfile=${FONT}:textfile=cap0.txt:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=14:x=(w-text_w)/2:y=h-70:enable='between(t,0,${T2})',drawtext=fontfile=${FONT}:textfile=cap1.txt:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=14:x=(w-text_w)/2:y=h-70:enable='between(t,${T2},${T3})',drawtext=fontfile=${FONT}:textfile=cap2.txt:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=14:x=(w-text_w)/2:y=h-70:enable='between(t,${T3},${T4})',drawtext=fontfile=${FONT}:textfile=cap3.txt:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=14:x=(w-text_w)/2:y=h-70:enable='between(t,${T4},${T5})',drawtext=fontfile=${FONT}:textfile=cap4.txt:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=14:x=(w-text_w)/2:y=h-70:enable='gte(t,${T5})'" \
  -c:v libx264 -pix_fmt yuv420p -c:a copy -movflags +faststart \
  whycode-demo-video.mp4
echo "=== VIDEO DONE ==="
ffprobe -v error -show_entries stream=codec_type,codec_name -show_entries format=duration,size -of default=nw=1 whycode-demo-video.mp4
