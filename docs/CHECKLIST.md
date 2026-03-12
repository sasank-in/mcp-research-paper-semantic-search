# Setup Checklist

Use this checklist to ensure your system is properly configured.

## Prerequisites

- [ ] Python 3.8 or higher installed
- [ ] PostgreSQL 12 or higher installed
- [ ] pgvector extension installed
- [ ] At least 2GB free disk space
- [ ] Internet connection (for downloading models)

## Installation Steps

- [ ] Clone/download the project
- [ ] Navigate to project directory
- [ ] Run `pip install -r requirements.txt`
- [ ] Wait for all dependencies to install (may take 5-10 minutes)

## Configuration

- [ ] Copy `.env.example` to `.env` (or use existing `.env`)
- [ ] Edit `.env` with your PostgreSQL credentials
- [ ] Verify PostgreSQL is running
- [ ] Test connection: `psql -U postgres -c "SELECT version()"`

## Database Setup

- [ ] Run `python main.py setup`
- [ ] Verify database created: `psql -U postgres -l | grep vector_db`
- [ ] Verify table created: `psql -U postgres -d vector_db -c "\dt"`
- [ ] Verify pgvector enabled: `psql -U postgres -d vector_db -c "\dx"`

## Testing

- [ ] Run `python test_system.py`
- [ ] All 5 tests should pass
- [ ] If any test fails, check error messages

## Ingestion

- [ ] Verify PDFs exist in `data/papers/`
- [ ] Run `python main.py ingest`
- [ ] Wait for completion (2-5 minutes)
- [ ] Verify data: `psql -U postgres -d vector_db -c "SELECT COUNT(*) FROM paper_chunks"`

## Search Testing

- [ ] Run `python main.py search "attention mechanism"`
- [ ] Verify results are returned
- [ ] Check similarity scores (should be 0.5-1.0)
- [ ] Try different queries

## API Testing (Optional)

- [ ] Run `python main.py api`
- [ ] Open browser to http://localhost:8000
- [ ] Check http://localhost:8000/docs
- [ ] Test search endpoint with sample query
- [ ] Verify JSON response

## Verification

- [ ] System responds to queries in < 5 seconds
- [ ] Results are relevant to queries
- [ ] No error messages in console
- [ ] Database contains expected number of chunks

## Common Issues

### PostgreSQL not running
```bash
# Linux/Mac
sudo systemctl start postgresql

# Windows
# Start from Services app
```

### pgvector not installed
```bash
# See SETUP.md for installation instructions
```

### Import errors
```bash
pip install -r requirements.txt --upgrade
```

### Connection refused
- Check PostgreSQL is running
- Verify credentials in `.env`
- Check firewall settings

### No results returned
- Verify data was ingested
- Check database has records
- Try simpler queries

## Success Criteria

Your system is working correctly if:

✓ All tests pass
✓ Ingestion completes without errors
✓ Search returns relevant results
✓ API responds to requests (if using API)
✓ No error messages in logs

## Next Steps

Once everything is working:

1. Add your own PDFs to `data/papers/`
2. Run `python main.py ingest` again
3. Experiment with different queries
4. Integrate API into your applications
5. Customize for your use case

## Getting Help

If you encounter issues:

1. Check error messages carefully
2. Review SETUP.md for detailed instructions
3. Verify all checklist items are complete
4. Check PostgreSQL logs
5. Ensure all dependencies are installed

## Performance Benchmarks

Expected performance:

- Ingestion: ~50-100 chunks/second
- Search: < 1 second for 10K chunks
- API response: < 2 seconds
- Model loading: 5-10 seconds (first time)

If performance is significantly slower, check:
- Database indexes are created
- Sufficient RAM available
- PostgreSQL is properly configured
- No other heavy processes running
