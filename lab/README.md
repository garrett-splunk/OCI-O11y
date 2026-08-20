# Lab resources

See root [README.md](../README.md) and [WORKSHOP_GUIDE.md](../WORKSHOP_GUIDE.md).

```bash
cp .env.splunk.example .env.splunk
./scripts/start.sh
./scripts/produce-oci-logs.sh 10
```

Filter in O11y: `deployment.environment.name:oci-connector-lab`
