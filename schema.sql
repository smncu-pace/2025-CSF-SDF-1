CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    avatar      TEXT,
    password    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memories (
    id          SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    location    TEXT,
    creator_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS memory_visible_users (
    memory_id   INTEGER NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (memory_id, user_id)
);


CREATE TABLE IF NOT EXISTS pictures (
    id          SERIAL PRIMARY KEY,
    memory_id   INTEGER NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    pict        TEXT NOT NULL,
    title       TEXT
);

CREATE TABLE IF NOT EXISTS comments (
    id           SERIAL PRIMARY KEY,
    memory_id    INTEGER NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    commenter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_id    INTEGER REFERENCES users(id),
    content      TEXT NOT NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS comment_picture_links (
    comment_id   INTEGER NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    picture_id   INTEGER NOT NULL REFERENCES pictures(id) ON DELETE CASCADE,
    PRIMARY KEY (comment_id, picture_id)
);

CREATE TABLE IF NOT EXISTS messages (
    id          SERIAL PRIMARY KEY,
    sender_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,
    receiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text        TEXT NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    read        BOOLEAN NOT NULL DEFAULT FALSE,
    system      BOOLEAN NOT NULL DEFAULT FALSE,
    memory_id   INTEGER REFERENCES memories(id) ON DELETE SET NULL,
    picture_id  INTEGER REFERENCES pictures(id) ON DELETE SET NULL,
    comment_id  INTEGER REFERENCES comments(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS favorites (
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    memory_id   INTEGER NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, memory_id)
);
