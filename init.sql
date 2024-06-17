CREATE TABLE resource_table (
    id SERIAL PRIMARY KEY,
    resource_type TEXT NOT NULL,
    resource_data JSONB NOT NULL
);


CREATE PUBLICATION my_publication FOR TABLE public.resource_table;
