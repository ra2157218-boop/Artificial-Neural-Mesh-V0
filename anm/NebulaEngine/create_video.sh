#!/bin/bash
# Script to create video from Nebula Engine frames

echo "Nebula Engine - Video Creation Script"
echo "======================================"
echo ""

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "ERROR: FFmpeg is not installed."
    echo ""
    echo "Install FFmpeg:"
    echo "  macOS: brew install ffmpeg"
    echo "  Linux: sudo apt-get install ffmpeg"
    echo ""
    exit 1
fi

# Find frame files (try both patterns)
FRAME_PATTERN="nebula_valley*.ppm"
FRAME_COUNT=$(ls -1 nebula_valley_frame_*.ppm nebula_valley_enhanced_frame_*.ppm 2>/dev/null | wc -l)

if [ $FRAME_COUNT -eq 0 ]; then
    echo "ERROR: No frame files found"
    echo ""
    echo "First run one of:"
    echo "  ./nebula_video           (standard)"
    echo "  ./nebula_video_enhanced   (enhanced with animated camera)"
    echo ""
    echo "This will generate the frame files."
    exit 1
fi

echo "Found $FRAME_COUNT frame files"
echo ""

# Determine output video name
if ls nebula_valley_enhanced_frame_*.ppm 1> /dev/null 2>&1; then
    OUTPUT_VIDEO="nebula_valley_enhanced.mp4"
    FRAME_PATTERN="nebula_valley_enhanced_frame_*.ppm"
else
    OUTPUT_VIDEO="nebula_valley.mp4"
    FRAME_PATTERN="nebula_valley_frame_*.ppm"
fi

echo "Encoding video: $OUTPUT_VIDEO"
echo "Quality: High (CRF 18)"
echo "This may take a minute..."

ffmpeg -y -framerate 30 -pattern_type glob -i "$FRAME_PATTERN" \
    -c:v libx264 -pix_fmt yuv420p -crf 18 \
    -preset medium \
    -movflags +faststart \
    "$OUTPUT_VIDEO"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Video created successfully: $OUTPUT_VIDEO"
    echo ""
    echo "Clean up frame files? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm $FRAME_PATTERN
        echo "Frame files removed."
    fi
else
    echo ""
    echo "ERROR: Video encoding failed"
    exit 1
fi
