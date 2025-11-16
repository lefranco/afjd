#!/bin/bash

for dir in $(ls) do
  (cd "$dir" && docker compose up -d)
done
