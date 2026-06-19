#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

stubgen --include-private --parse-only -o /tmp/gamepack-stubs gamepack/
cp -r /tmp/gamepack-stubs/GamePack/gamepack/*.pyi gamepack/
ruff check --fix gamepack/*.pyi gamepack/endworld/*.pyi
black gamepack/*.pyi gamepack/endworld/*.pyi
