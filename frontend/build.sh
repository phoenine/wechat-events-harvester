#!/bin/bash

# 设置路径变量
DIST_DIR="dist"
# 构建前端产物，仅输出到 frontend/dist，用于独立前端容器
npm run build
echo "前端构建完成：$DIST_DIR"
