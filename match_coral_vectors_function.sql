CREATE OR REPLACE FUNCTION match_coral_vectors (
  query_embedding vector(512),
  filter_site VARCHAR(100),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  session_id UUID,
  coral_id VARCHAR(100),
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    session_id,
    coral_id,
    1 - (media_vectors.embedding <=> query_embedding) AS similarity
  FROM media_vectors
  WHERE site_name = filter_site AND 1 - (media_vectors.embedding <=> query_embedding) > match_threshold
  ORDER BY media_vectors.embedding <=> query_embedding ASC
  LIMIT match_count;
$$;
