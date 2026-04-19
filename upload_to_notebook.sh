#!/bin/bash

# 使用方式: ./upload_to_notebook.sh <檔案路徑> <筆記本ID> [--enable-insights]

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "使用方式: $0 <檔案路徑> <筆記本ID> [--enable-insights]"
  exit 1
fi

FILE_PATH="$1"
NOTEBOOK_ID="$2"
ENABLE_INSIGHTS=false

# 檢查是否有 --enable-insights 參數
if [[ "$3" == "--enable-insights" ]]; then
  ENABLE_INSIGHTS=true
fi

if [ ! -f "$FILE_PATH" ]; then
  echo "錯誤: 找不到檔案 $FILE_PATH"
  exit 1
fi

TRANSFORMATIONS="[]"
MSG="關閉"

if [ "$ENABLE_INSIGHTS" = true ]; then
  TRANSFORMATIONS='["transformation:r81jle14ok5pqhhaf9v9", "transformation:6xjan1bdex95n9qj8fg7", "transformation:i67qf0y3ctfnsuxfvzjn", "transformation:mtjxqc3zc4evy1ph73km", "transformation:zjc4edn6oxpq7xhr3752"]'
  MSG="啟用 (5 個)"
fi

echo "正在上傳 $FILE_PATH 到筆記本 $NOTEBOOK_ID (Insights: $MSG)..."

RESPONSE=$(curl -s -X POST "http://localhost:5055/api/sources" \
  -H "accept: application/json" \
  -F "type=upload" \
  -F "file=@$FILE_PATH" \
  -F "title=$(basename "$FILE_PATH")" \
  -F "embed=true" \
  -F "notebooks=[\"$NOTEBOOK_ID\"]" \
  -F "transformations=$TRANSFORMATIONS")

if echo "$RESPONSE" | grep -q '"id"'; then
  echo "上傳成功！"
  echo "$RESPONSE" | python3 -m json.tool
else
  echo "上傳失敗。回應內容:"
  echo "$RESPONSE"
fi
