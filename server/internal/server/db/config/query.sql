-- name: GetUserByUsername :one
SELECT * FROM users
WHERE username = ? LIMIT 1;

-- name: GetUserById :one
SELECT * FROM users
WHERE id = ? LIMIT 1;

-- name: CreateUser :one
INSERT INTO users (
    username, password_hash
) VALUES (
    ?, ?
)
RETURNING *;

