#!/bin/bash
# GitHub Issue WebUI Launcher
# Fetches issues from GitHub and launches the WebUI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${1:-blackif/claw_hjm}"
PROJECT_NAME="${2:-claw_hjm}"

# Load API Key from config
CONFIG_FILE="${CONFIG_FILE:-/home/ubuntu/.openclaw/workspace/config.json}"
if [ -f "$CONFIG_FILE" ]; then
    API_KEY=$(jq -r '.api.dashscope_key // empty' "$CONFIG_FILE" 2>/dev/null)
    if [ -n "$API_KEY" ] && [ "$API_KEY" != "null" ]; then
        export DASHSCOPE_API_KEY="$API_KEY"
        echo "✅ API Key 已加载"
    fi
fi

echo "🔍 Fetching issues from $REPO..."

# Fetch open issues with full details
ISSUES_JSON=$(gh issue list --repo "$REPO" --state open \
  --json number,title,body,createdAt,updatedAt,author,labels,comments \
  --limit 100)

# Add owner and repo fields to each issue
ISSUES_WITH_REPO=$(echo "$ISSUES_JSON" | jq --arg repo "$REPO" '
  .[] | . + {
    owner: ($repo | split("/")[0]),
    repo: $repo
  }
' | jq -s '.')

echo "📊 Found $(echo "$ISSUES_WITH_REPO" | jq 'length') open issues"

# Export and launch
export ISSUES_JSON="$ISSUES_WITH_REPO"
export PROJECT_NAME="$PROJECT_NAME"

echo "🚀 Launching WebUI..."
python3 "$SCRIPT_DIR/app.py" \
  --host 0.0.0.0 \
  --port 7860 \
  --config "$CONFIG_FILE"
