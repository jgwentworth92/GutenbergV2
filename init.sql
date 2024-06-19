CREATE TABLE resource (
    id UUID PRIMARY KEY,
    job_id UUID NOT NULL,
    resource_type TEXT NOT NULL,
    resource_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);



CREATE PUBLICATION my_publication FOR TABLE public.resource;
