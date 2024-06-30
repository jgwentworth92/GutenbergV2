--
-- PostgreSQL database dump
--

-- Dumped from database version 16.2 (Debian 16.2-1.pgdg120+2)
-- Dumped by pg_dump version 16.2 (Debian 16.2-1.pgdg120+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: UserRole; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public."UserRole" AS ENUM (
    'ANONYMOUS',
    'AUTHENTICATED',
    'MANAGER',
    'ADMIN'
);


ALTER TYPE public."UserRole" OWNER TO admin;

--
-- Name: stepstatus; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.stepstatus AS ENUM (
    'NOT_STARTED',
    'IN_PROGRESS',
    'COMPLETE',
    'FAILED'
);


ALTER TYPE public.stepstatus OWNER TO admin;

--
-- Name: steptype; Type: TYPE; Schema: public; Owner: admin
--

CREATE TYPE public.steptype AS ENUM (
    'DATAFLOW_TYPE_gateway',
    'DATAFLOW_TYPE_processing',
    'DATAFLOW_TYPE_processing_llm',
    'DATAFLOW_TYPE_DATASINK'
);


ALTER TYPE public.steptype OWNER TO admin;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO admin;

--
-- Name: documents; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.documents (
    id uuid NOT NULL,
    job_id uuid NOT NULL,
    collection_name character varying(255) NOT NULL,
    vector_db_id character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.documents OWNER TO admin;

--
-- Name: jobs; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.jobs (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.jobs OWNER TO admin;

--
-- Name: resources; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.resources (
    id uuid NOT NULL,
    job_id uuid NOT NULL,
    resource_type character varying(50) NOT NULL,
    resource_data json NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.resources OWNER TO admin;

--
-- Name: steps; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.steps (
    id uuid NOT NULL,
    job_id uuid NOT NULL,
    status public.stepstatus NOT NULL,
    step_type public.steptype NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.steps OWNER TO admin;

--
-- Name: users; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    nickname character varying(50) NOT NULL,
    email character varying(255) NOT NULL,
    first_name character varying(100),
    last_name character varying(100),
    bio character varying(500),
    profile_picture_url character varying(255),
    linkedin_profile_url character varying(255),
    github_profile_url character varying(255),
    role public."UserRole" NOT NULL,
    is_professional boolean,
    professional_status_updated_at timestamp with time zone,
    last_login_at timestamp with time zone,
    failed_login_attempts integer,
    is_locked boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    verification_token character varying,
    email_verified boolean NOT NULL,
    hashed_password character varying(255) NOT NULL
);


ALTER TABLE public.users OWNER TO admin;

--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: jobs jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (id);


--
-- Name: resources resources_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.resources
    ADD CONSTRAINT resources_pkey PRIMARY KEY (id);


--
-- Name: steps steps_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.steps
    ADD CONSTRAINT steps_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_nickname; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX ix_users_nickname ON public.users USING btree (nickname);


--
-- Name: documents documents_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(id);


--
-- Name: jobs jobs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: resources resources_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.resources
    ADD CONSTRAINT resources_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(id);


--
-- Name: steps steps_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.steps
    ADD CONSTRAINT steps_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(id);


--
-- Name: my_publication; Type: PUBLICATION; Schema: -; Owner: admin
--

CREATE PUBLICATION my_publication WITH (publish = 'insert, update, delete, truncate');


ALTER PUBLICATION my_publication OWNER TO admin;

--
-- Name: my_publication resources; Type: PUBLICATION TABLE; Schema: public; Owner: admin
--

ALTER PUBLICATION my_publication ADD TABLE ONLY public.resources;


--
-- PostgreSQL database dump complete
--

INSERT INTO public.users (
    id,
    nickname,
    email,
    first_name,
    last_name,
    bio,
    profile_picture_url,
    linkedin_profile_url,
    github_profile_url,
    role,
    is_professional,
    professional_status_updated_at,
    last_login_at,
    failed_login_attempts,
    is_locked,
    created_at,
    updated_at,
    verification_token,
    email_verified,
    hashed_password
) VALUES (
    '3ba11cee-80e8-4212-acb5-660a25a603b0',  -- Replace with a valid UUID
    'clever_raccoon_317',
    'john.doe@example.com',
    'John',
    'Doe',
    'Experienced software developer specializing in web applications.',
    'https://example.com/profiles/john.jpg',
    'https://linkedin.com/in/johndoe',
    'https://github.com/johndoe',
    'ADMIN',  -- Role must be one of the values from the UserRole enum
    False,  -- is_professional
    NULL,  -- professional_status_updated_at
    NULL,  -- last_login_at
    0,  -- failed_login_attempts
    False,  -- is_locked
    '2024-06-18 20:32:18+00',  -- created_at
    '2024-06-18 20:32:18+00',  -- updated_at
    NULL,  -- verification_token
    True,  -- email_verified
    '$2b$12$qyPOY3a0R256nd.XeN/BRegd5Wz5n3x8ADDEZO9ddwv/M0Xq3Irpu'  -- Replace with an actual hashed password
);
