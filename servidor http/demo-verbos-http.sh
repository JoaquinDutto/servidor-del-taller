#!/usr/bin/env bash

set -u

base_url="http://localhost:9292"
passed=0
failed=0

check() {
    local description="$1"
    local expected_status="$2"
    local method="$3"
    local url="$4"
    local body="${5:-}"
    local response_file
    local status

    response_file=$(mktemp)
    if [ -n "$body" ]; then
        status=$(curl -sS -o "$response_file" -w "%{http_code}" \
            -X "$method" -H "Content-Type: application/json" \
            -d "$body" "$url")
    else
        status=$(curl -sS -o "$response_file" -w "%{http_code}" \
            -X "$method" "$url")
    fi

    if [ "$status" = "$expected_status" ]; then
        printf 'PASS %-36s %s\n' "$description" "$status"
        passed=$((passed + 1))
    else
        printf 'FAIL %-36s esperado %s, recibido %s\n' \
            "$description" "$expected_status" "$status"
        cat "$response_file"
        failed=$((failed + 1))
    fi

    cat "$response_file"
    printf '\n'
    rm -f "$response_file"
}

check "GET lista vacía" 200 GET "$base_url/tasks"
check "POST crea tarea" 201 POST "$base_url/tasks" \
    '{"title":"Estudiar HTTP","done":false}'
check "GET obtiene tarea" 200 GET "$base_url/tasks/1"
check "PATCH modifica solo done" 200 PATCH "$base_url/tasks/1" \
    '{"done":true}'
check "DELETE elimina tarea" 200 DELETE "$base_url/tasks/1"
check "GET tarea eliminada" 404 GET "$base_url/tasks/1"

printf 'Resumen: %s PASS, %s FAIL\n' "$passed" "$failed"
[ "$failed" -eq 0 ]