-- Disable foreign key checks temporarily
PRAGMA foreign_keys = OFF;

-- Start the transaction
--   All the SQL commands that follow are executed as a single unit.
--   If an error occurs, the entire transaction can be rolled back.
BEGIN TRANSACTION;

-- Table to store subjects
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY NOT NULL,  -- Unique ID for each subject
    subject TEXT                      -- Name of the subject
);

-- Table to store tags
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY NOT NULL,  -- Unique ID for each tag
    tag TEXT,                         -- Tag name
    dict TEXT                         -- tags separated by ;
);

-- Table to store user information
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY NOT NULL,  -- Unique user ID
    name TEXT,                        -- User's name
    email TEXT                        -- User's email address
);

-- Table to store paper metadata
CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY NOT NULL,        -- Unique paper ID
    doi TEXT,                               -- DOI of the paper
    journal TEXT,                           -- Journal name
    volume INTEGER,                         -- Volume of the journal
    issue INTEGER,                          -- Issue number
    url TEXT,                               -- URL of the paper
    title TEXT,                             -- Title of the paper
    public_date TEXT,                       -- Publication date
    year INTEGER,                           -- Year of publication
    authors TEXT,                           -- Authors of the paper
    version TEXT,                           -- Version of the paper
    abstract TEXT,                          -- Abstract of the paper
    note TEXT,                              -- Additional notes
    head_added_date INTEGER NOT NULL,       -- Timestamp of when the paper was added
    head_StrID TEXT NOT NULL,               -- Unique identifier string for the paper
    keywords TEXT,                          -- keywords of paper
    score_by_keywords INTEGER               -- score calculated by keywords of paper
);

-- Table to map users to tags (many-to-many relationship)
CREATE TABLE IF NOT EXISTS map_users_2_tags (
    id INTEGER PRIMARY KEY NOT NULL,  -- Unique ID for each mapping
    user_id INTEGER NOT NULL REFERENCES users, -- Foreign key to the user
    tag_id INTEGER NOT NULL REFERENCES tags,   -- Foreign key to the tag
    user_name TEXT NOT NULL,                   -- User's name (for faster access)
    tag_name TEXT NOT NULL                     -- Tag's name (for faster access)
);

-- Table to map papers to tags (many-to-many relationship)
CREATE TABLE IF NOT EXISTS map_papers_2_tags (
    id INTEGER PRIMARY KEY NOT NULL,  -- Unique ID for each mapping
    paper_id INTEGER NOT NULL REFERENCES papers, -- Foreign key to the paper
    tag_id INTEGER NOT NULL REFERENCES tags,     -- Foreign key to the tag
    tag_name TEXT NOT NULL                       -- Tag's name (for faster access)
);

-- Table to map papers to subjects (many-to-many relationship)
CREATE TABLE IF NOT EXISTS map_papers_2_subjects (
    id INTEGER PRIMARY KEY NOT NULL,  -- Unique ID for each mapping
    paper_id INTEGER NOT NULL REFERENCES papers,   -- Foreign key to the paper
    subject_id INTEGER NOT NULL REFERENCES subjects, -- Foreign key to the subject
    subject_name TEXT NOT NULL                       -- Subject's name (for faster access)
);

-- Table to store user preferences for specific papers
CREATE TABLE IF NOT EXISTS map_user_preference (
    id INTEGER PRIMARY KEY,                -- Unique ID for each preference
    user_id INTEGER NOT NULL REFERENCES users,  -- Foreign key to the user
    paper_id INTEGER NOT NULL REFERENCES papers, -- Foreign key to the paper
    user_name INTEGER NOT NULL,                -- User's name (could be TEXT instead of INTEGER)
    preference INTEGER DEFAULT 0 NOT NULL      -- User's preference score (default 0)
);

-- CREATE TABLE map_user_preference
-- (
--  id integer
--      constraint map_user_preference_pk
--          primary key,
--  user_id integer not null references users,
--  paper_id integer not null references papers,
--  user_name integer not null
-- , preference integer default 0 not null);


-- Table to store mailing_list
-- day of week is in order: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
CREATE TABLE IF NOT EXISTS mailing_list (
    id INTEGER PRIMARY KEY NOT NULL,        -- Unique ID for each subject
    subject TEXT,                           -- Name of the subject
    update_date INTEGER NOT NULL,           -- Timestamp of when the mail was added
    update_date_yymmdd INTEGER NOT NULL,    -- update_date in YYMMDD format
    update_date_weekday INTEGER NOT NULL,   -- weekday of update_date
    list_paper_idx TEXT,                    -- indexs of paper
    list_paper_stridx TEXT,                 -- str indexs of paper
    skimmed BLOB,                           -- read status of mail
    starred BLOB                            -- flag of mail
);

-- Ensure unique tag names
CREATE UNIQUE INDEX tags_tag_uindex ON tags (tag);

-- Ensure unique subject names
CREATE UNIQUE INDEX subjects_subject_uindex ON subjects (subject);

-- Ensure the paper's head_StrID is unique
CREATE UNIQUE INDEX papers_head_StrID_uindex ON papers (head_StrID);

-- Commit the transaction
COMMIT;
