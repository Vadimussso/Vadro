ALTER TABLE ads DROP CONSTRAINT IF EXISTS ads_author_id_fk;

ALTER TABLE ads DROP COLUMN IF EXISTS author_id;
