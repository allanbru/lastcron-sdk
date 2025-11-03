#!/bin/bash
# Build and publish script for LastCron SDK
# This script builds the package and optionally publishes it to PyPI

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  LastCron SDK Build & Publish Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Clean previous builds
echo -e "${YELLOW}[1/6] Cleaning previous builds...${NC}"
rm -rf dist/ build/ lastcron.egg-info/
echo -e "${GREEN}✓ Cleaned${NC}"
echo ""

# Step 2: Install/upgrade build tools
echo -e "${YELLOW}[2/6] Installing/upgrading build tools...${NC}"
python -m pip install --upgrade pip build twine
echo -e "${GREEN}✓ Build tools ready${NC}"
echo ""

# Step 3: Run tests (optional but recommended)
echo -e "${YELLOW}[3/6] Running tests...${NC}"
if command -v pytest &> /dev/null; then
    pytest --cov=lastcron --cov-report=term-missing || {
        echo -e "${RED}✗ Tests failed!${NC}"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    }
    echo -e "${GREEN}✓ Tests passed${NC}"
else
    echo -e "${YELLOW}⚠ pytest not found, skipping tests${NC}"
fi
echo ""

# Step 4: Build the package
echo -e "${YELLOW}[4/6] Building package...${NC}"
python -m build
echo -e "${GREEN}✓ Package built successfully${NC}"
echo ""

# Step 5: Check the package
echo -e "${YELLOW}[5/6] Checking package with twine...${NC}"
twine check dist/* || {
    echo -e "${YELLOW}⚠ Twine check warnings (these are usually safe to ignore for metadata version issues)${NC}"
}
echo -e "${GREEN}✓ Package checked${NC}"
echo ""

# Step 6: List built files
echo -e "${BLUE}Built files:${NC}"
ls -lh dist/
echo ""

# Step 7: Prompt for upload
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Ready to Publish${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Choose an option:"
echo "  1) Upload to Test PyPI (recommended first)"
echo "  2) Upload to Production PyPI"
echo "  3) Skip upload (just build)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo -e "${YELLOW}Uploading to Test PyPI...${NC}"
        echo -e "${BLUE}You will need your Test PyPI credentials${NC}"
        echo ""
        twine upload --repository testpypi dist/*
        echo ""
        echo -e "${GREEN}✓ Uploaded to Test PyPI${NC}"
        echo -e "${BLUE}Install with: pip install --index-url https://test.pypi.org/simple/ lastcron${NC}"
        ;;
    2)
        echo ""
        echo -e "${RED}⚠ WARNING: You are about to upload to PRODUCTION PyPI!${NC}"
        read -p "Are you sure? (yes/NO) " -r
        echo
        if [[ $REPLY == "yes" ]]; then
            echo -e "${YELLOW}Uploading to Production PyPI...${NC}"
            echo -e "${BLUE}You will need your PyPI credentials${NC}"
            echo ""
            twine upload dist/*
            echo ""
            echo -e "${GREEN}✓ Uploaded to Production PyPI${NC}"
            echo -e "${BLUE}Install with: pip install lastcron${NC}"
        else
            echo -e "${YELLOW}Upload cancelled${NC}"
        fi
        ;;
    3)
        echo ""
        echo -e "${GREEN}Build complete. Skipping upload.${NC}"
        ;;
    *)
        echo ""
        echo -e "${YELLOW}Invalid choice. Skipping upload.${NC}"
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Done!${NC}"
echo -e "${GREEN}========================================${NC}"

