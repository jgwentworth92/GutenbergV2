CREATE TABLE app_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL
);

CREATE PUBLICATION my_publication FOR TABLE public.app_user;
