PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE subjects(
    id integer primary key not null,
    subject text
);
CREATE TABLE tags(
    id integer primary key not null,
    tag text
, dict text);

CREATE TABLE users(
    id integer primary key not null,
    name text,
    email text
);

CREATE TABLE IF NOT EXISTS "map_users_2_tags"
(
	id integer not null
		primary key,
	user_id integer not null
		references users,
	tag_id integer not null
		references tags,
	user_name text not null,
	tag_name text not null
);

CREATE TABLE IF NOT EXISTS "map_papers_2_tags"
(
	id integer not null
		primary key,
	paper_id integer not null
		references papers,
	tag_id integer not null
		references tags,
	tag_name text not null
);

CREATE TABLE IF NOT EXISTS "map_papers_2_subjects"
(
	id integer not null
		primary key,
	paper_id integer not null
		references papers,
	subject_id integer not null
		references subjects,
	subject_name text not null
);
CREATE TABLE map_user_preference
(
	id integer
		constraint map_user_preference_pk
			primary key,
	user_id integer not null references users,
	paper_id integer not null references papers,
	user_name integer not null
, preference integer default 0 not null);

CREATE TABLE IF NOT EXISTS "papers"
(
	id integer not null
		primary key,
	doi text,
	journal text,
	volume integer,
	issue integer,
	url text,
	title text,
	public_date text,
	year integer,
	authors text,
	version text,
	abstract text,
	note text,
	head_added_date integer not null,
	head_StrID text not null
);

CREATE UNIQUE INDEX tags_tag_uindex
	on tags (tag);
CREATE UNIQUE INDEX subjects_subject_uindex
	on subjects (subject);
CREATE UNIQUE INDEX papers_head_StrID_uindex
	on papers (head_StrID);
COMMIT;
