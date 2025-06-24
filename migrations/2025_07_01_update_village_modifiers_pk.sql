-- Adjust village_modifiers primary key to include source
ALTER TABLE village_modifiers DROP CONSTRAINT IF EXISTS village_modifiers_pkey;
ALTER TABLE village_modifiers ADD PRIMARY KEY (village_id, source);
