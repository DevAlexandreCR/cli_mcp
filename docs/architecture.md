# Architecture Notes

## Services

### API (FastAPI)
- Handles all business logic
- Stateless — scales horizontally
- JWT auth, validated on every request

### Worker (Celery + Redis)
- Async tasks: email, thumbnail generation, search indexing
- One queue per priority level (high / default / low)

### Search (Meilisearch)
- Self-hosted, runs in its own container
- Re-indexed nightly, near-real-time updates via worker

## Data flow

```
Browser → CDN → API → Postgres
                    ↘ S3  (attachments)
                    ↘ Redis (cache + queue)
                    ↘ Meilisearch (search index)
```

## Known bottlenecks
- Large file uploads go through the API server (should be direct-to-S3)
- Search index can fall behind under heavy write load

## Next steps
- Implement presigned S3 URLs for direct uploads
- Add a read replica for analytics queries
