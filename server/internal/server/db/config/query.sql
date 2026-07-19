-- name: GetUserByUsername :one
SELECT * FROM users
WHERE username = ? LIMIT 1;

-- name: CreateUser :one
INSERT INTO users (
    username, password_hash
) VALUES (
    ?, ?
)
RETURNING *;


-- name: CreatePlayer :one
INSERT INTO players (
    user_id, name
) VALUES (
    ?, ?
)
RETURNING *;

-- name: GetPlayerByUserID :one
SELECT * FROM players
WHERE user_id = ? LIMIT 1;


-- name: GetPlayerByName :one
SELECT * FROM players
WHERE name LIKE ?
LIMIT 1;
