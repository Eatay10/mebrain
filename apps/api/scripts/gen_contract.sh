#!/bin/sh
# openapi.yaml'dan Pydantic v2 modellerini üretir -> app/contract.py (ELLE DÜZENLEMEYİN).
set -eu
cd "$(dirname "$0")/.."
ROOT=../..
SPEC="$ROOT/knowledge/contracts/openapi.yaml"
[ -f "$SPEC" ] || SPEC="$ROOT/docs/api/openapi.yaml"
uv run datamodel-codegen \
  --input "$SPEC" --input-file-type openapi \
  --output app/contract.py \
  --output-model-type pydantic_v2.BaseModel \
  --target-python-version 3.12 \
  --snake-case-field --allow-population-by-field-name \
  --use-standard-collections --use-union-operator \
  --field-constraints --use-annotated \
  --use-subclass-enum --capitalise-enum-members --collapse-root-models \
  --use-double-quotes --disable-timestamp \
  --custom-file-header "# GENERATED from openapi.yaml by scripts/gen_contract.sh — do not edit."
echo "generated app/contract.py from $SPEC"
