#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

rm -f gamepack/*.pyi gamepack/endworld/*.pyi

stubgen --include-private -o /tmp/gamepack-stubs gamepack/
cp -r /tmp/gamepack-stubs/GamePack/gamepack/*.pyi gamepack/
cp -r /tmp/gamepack-stubs/GamePack/gamepack/endworld/*.pyi gamepack/endworld/
ruff check --fix gamepack/*.pyi gamepack/endworld/*.pyi
black gamepack/*.pyi gamepack/endworld/*.pyi
