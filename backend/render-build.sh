#!/usr/bin/env bash
# exit on error
set -o errexit

echo "======================================================================"
echo "CRITICAL CONFIGURATION ERROR DETECTED"
echo "======================================================================"
echo "This project requires system-level dependencies (Tesseract OCR)."
echo "The 'Python 3' Native Runtime on Render does NOT support installing these."
echo ""
echo "You MUST switch your service Runtime to 'Docker'."
echo ""
echo "HOW TO FIX:"
echo "1. Go to Render Dashboard > muhasebe-api > Settings"
echo "2. Check if you can change 'Runtime' to 'Docker'"
echo "3. If locked, you must create a new Web Service and select 'Docker' as the runtime."
echo "   (Or use the 'Blueprints' tab to deploy using render.yaml)"
echo "======================================================================"

# Fail the build intentionally so the user sees the error in deployment logs
exit 1
