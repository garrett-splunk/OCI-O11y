# Deploy lab bundle to a workshop VM

```bash
cd lab
tar czf ../oci-connector-o11y-export.tar.gz \
  --exclude='.env.splunk' \
  --exclude='.env' \
  .
```

On the target host:

```bash
tar xzf oci-connector-o11y-export.tar.gz
cp .env.splunk.example .env.splunk
./scripts/start.sh
```

Requires Docker and Docker Compose v2.
