# SEA Technology & Infrastructure Costs

## Cloud Infrastructure Costs — SEA Expansion

### Regional Pricing Comparison (per month, baseline compute)

**Singapore (Primary Hub)**
- Compute instances (standard): ~25% premium vs India
- Database services (managed SQL): ~30% premium vs India  
- Data transfer (inbound): Free; outbound: ~$0.12/GB
- CDN (CloudFront/Azure CDN): ~$0.085/GB vs India $0.047/GB
- Load balancer: ~$16/month per LB

**Malaysia (Secondary)**
- Compute: ~15% premium vs India
- Database: ~20% premium vs India
- Data transfer outbound: ~$0.12/GB
- CDN: ~$0.085/GB

**Indonesia (Growth Market)**
- Compute: ~5% premium vs India
- Database: ~10% premium vs India
- Data transfer: ~$0.12/GB outbound
- CDN: ~$0.085/GB

### Estimated Monthly Infrastructure Cost — SEA Build-Out

**Scenario: Pilot (Singapore only, 50 concurrent users)**
- Compute (2x m5.large equivalent): ~$400/month
- Database (managed PostgreSQL, 500GB): ~$600/month
- Data transfer + CDN (10TB/month traffic): ~$1,200/month
- Monitoring, logging, backups: ~$400/month
- **Total: ~$2,600/month**

**Scenario: Regional (SG + MY + ID, 500 concurrent users)**
- Compute (multi-region, 6x instances): ~$1,800/month
- Database (federated + read replicas): ~$2,200/month
- Data transfer + CDN (100TB/month): ~$12,000/month
- Monitoring, logging, DR: ~$1,200/month
- **Total: ~$17,200/month**

### Cost Drivers & Optimizations

1. **Data Transfer**: Largest line item. Consider:
   - CloudFront/CDN regional edge caching reduces origin fetch ~70%
   - S3 transfer acceleration for large uploads: adds $0.04/GB
   - VPN/private link to co-locate: $350–500/month per region

2. **Compute Right-Sizing**: 
   - Spot instances in SG/MY save ~65% vs on-demand
   - Reserved instances (1yr): ~40% discount if traffic predictable
   - Auto-scaling recommended; peak load = 2.5x baseline

3. **Database Sharding**:
   - Geo-distributed databases (AWS RDS multi-region): +60% cost
   - Application-level sharding (recommended): +10% ops overhead, saves 30% DB cost
   - Read replicas for compliance (data residency): +$400/month per region

4. **Bandwidth Optimization**:
   - Compress all payloads (gzip): ~60% bandwidth reduction, negligible CPU
   - Client-side caching (service workers): 40% fewer API calls
   - Video transcoding to regional bitrates: +$0.005 per minute transcoded

### One-Time Setup Costs

- Infrastructure provisioning & VPC setup: ~$5,000
- Data seeding & initial replication: ~$3,000
- DPA/compliance review (legal + technical): ~$2,000
- Monitoring & alerting configuration: ~$1,500
- **Total: ~$11,500**

### Historical Trend (2024–2025)

- Singapore compute inflation: +8% YoY
- Database pricing stable (commoditizing)
- Data transfer costs down 3% YoY (competitive pressure)
- CDN pricing trending down across all providers

### Recommendations for Board

1. **Pilot ROI**: At projected SG Q1 pipeline ($4.2M), $2.6K/month infra is <0.1% COGS
2. **Regional expansion**: $17.2K/month breakeven at ~$1.5M MRR (achievable by Q3 2026)
3. **Vendor strategy**: Multi-cloud reduces lock-in but increases ops complexity; recommend AWS primary + Azure standby
4. **Budget allocation**: Allocate $30K/quarter tech budget for SEA; infra ~30%, compliance/tooling ~40%, hiring/ops ~30%
