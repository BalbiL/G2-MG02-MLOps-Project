-- SQL used for supabase --
-- Already in the section "SQL Editor" in Supabase --
-- Users --

create table if not exists user_topics (
    user_id uuid references auth.users(id) on delete cascade,
    topics_list text[],
    primary key (user_id)
);

-- Interactions --

create table if not exists interactions (
    interaction_id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id),
    news_id text references news(id),
    event_type text,
    event_time timestamptz default now()
);

-- Recommandations --

create table if not exists default_recs (
    news_id text references news(id),
    score float,
    generation_time timestamptz default now()
);

create table if not exists personalized_recs (
    user_id uuid references auth.users(id),
    news_id text references news(id),
    score float,
    generation_time timestamptz default now(),
    primary key (user_id, news_id)
);


-- Vector --

create extension if not exists vector;

create table if not exists news_vec (
    news_id text primary key references news(id),
    vec vector(768)  -- selon le modèle d'embedding
);
