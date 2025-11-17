alter table user_topics enable row level security;
alter table default_recs enable row level security;
alter table personalized_recs enable row level security;
alter table news enable row level security;
alter table news_vec enable row level security;
alter table interactions enable row level security;

-- Read own topics
create policy "Users read their topics"
on user_topics for select
using (user_id = auth.uid());

-- Insert own topics
create policy "Users insert their topics"
on user_topics for insert
with check (user_id = auth.uid());

-- Update own topics
create policy "Users update their topics"
on user_topics for update
using (user_id = auth.uid());

-- policy reco
create policy "Users read their personalized recs"
on personalized_recs for select
using (user_id = auth.uid());

create policy "Users insert their personalized recs"
on personalized_recs for insert
with check (user_id = auth.uid());

create policy "Users update their personalized recs"
on personalized_recs for update
using (user_id = auth.uid());

-- news
create policy "Public read news"
on news for select
to public
using (true);

-- empêcher modification depuis le client
create policy "No client write news"
on news for insert
with check (false);

create policy "No client update news"
on news for update
using (false);

-- vector
create policy "Public read news_vec"
on news_vec for select
to public
using (true);

create policy "No client write news_vec"
on news_vec for insert
with check (false);

create policy "No client update news_vec"
on news_vec for update
using (false);

-- Interaction
create policy "Users read their interactions"
on interactions for select
using (user_id = auth.uid());

create policy "Users insert their interactions"
on interactions for insert
with check (user_id = auth.uid());

create policy "Users update their interactions"
on interactions for update
using (user_id = auth.uid());


-- rec
create policy "Public read default recs"
on default_recs for select
to public
using (true);

-- No insert/update/delete from clients (only backend)
create policy "No client insert"
on default_recs for insert
with check (false);

create policy "No client update"
on default_recs for update
using (false);
