ALTER TABLE ads ADD COLUMN author_id INTEGER NOT NULL;

ALTER TABLE ads ADD CONSTRAINT ads_author_id_fk FOREIGN KEY (author_id) REFERENCES users(id);