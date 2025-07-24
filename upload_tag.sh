#!/bin/bash
TAG=$1

# Check se tag è passato
if [ -z "$TAG" ]; then
  echo "Usage: $0 <tag>"
  exit 1
fi

# Rimuove il tag se esiste
if git rev-parse "$TAG" >/dev/null 2>&1; then
  git tag -d "$TAG"
  git push origin ":refs/tags/$TAG"
fi

# Ricrea e pusha
git tag "$TAG"
git push origin "$TAG"
