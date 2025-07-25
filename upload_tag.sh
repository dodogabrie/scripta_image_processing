#!/bin/bash
TAG=$1

# Check se tag è passato
if [ -z "$TAG" ]; then
  echo "Usage: $0 <tag>"
  exit 1
fi

# Rimuove tag locale e remoto se esiste
if git rev-parse "$TAG" >/dev/null 2>&1; then
  git tag -d "$TAG"
  git push origin ":refs/tags/$TAG"
fi

# Rimuove release GitHub se esiste
if gh release view "$TAG" >/dev/null 2>&1; then
  gh release delete "$TAG" -y
fi

# Crea e pusha nuovo tag
git tag "$TAG"
git push origin "$TAG"
