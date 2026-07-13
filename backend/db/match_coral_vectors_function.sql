CREATE OR REPLACE FUNCTION match_coral_vectors (
  query_embedding vector(512),
  filter_site VARCHAR(100),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  session_id UUID,
  coral_id VARCHAR(100),
  storage_url VARCHAR(100),
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    media_vectors.session_id AS session_id,
    media_vectors.coral_id AS coral_id,
    monitoring_sessions.storage_url AS storage_url,
    1 - (media_vectors.embedding <=> query_embedding) AS similarity
  FROM media_vectors INNER JOIN monitoring_sessions ON media_vectors.session_id = monitoring_sessions.id
  WHERE media_vectors.site_name = filter_site AND 1 - (media_vectors.embedding <=> query_embedding) > match_threshold
  ORDER BY media_vectors.embedding <=> query_embedding ASC
  LIMIT match_count;
$$;
