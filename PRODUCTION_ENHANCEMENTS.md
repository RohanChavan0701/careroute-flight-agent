# Production Enhancements Guide

Complete guide for taking your Flight Agent from MVP to production-ready with monitoring, HTTPS, caching, and CI/CD.

## 📋 Table of Contents

1. [CloudWatch Monitoring](#1-cloudwatch-monitoring)
2. [HTTPS with Nginx & Let's Encrypt](#2-https-with-nginx--lets-encrypt)
3. [Redis Caching](#3-redis-caching)
4. [Application Load Balancer](#4-application-load-balancer-optional)
5. [GitHub Actions CI/CD](#5-github-actions-cicd)
6. [Cost Breakdown](#6-cost-breakdown)

---

## 1. CloudWatch Monitoring

Set up comprehensive monitoring for your Flight Agent with automated health checks, custom metrics, and alerting.

### Features
- ✅ Container CPU/Memory monitoring
- ✅ API request counting
- ✅ Automated health checks (every 5 minutes)
- ✅ CloudWatch Logs integration
- ✅ Custom dashboard
- ✅ Alerting on high resource usage

### Setup

```bash
# SSH into EC2
ssh -i codefest.pem ubuntu@54.158.27.0

# Download and run setup script
curl -O https://raw.githubusercontent.com/rohanpc0701/Codefest_Flightapi/main/monitoring/cloudwatch-setup.sh
chmod +x cloudwatch-setup.sh
./cloudwatch-setup.sh
```

### Post-Setup

1. **Install AWS CLI**:
   ```bash
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   ```

2. **Configure AWS credentials**:
   ```bash
   aws configure
   # Enter your AWS Access Key ID
   # Enter your AWS Secret Access Key
   # Region: us-east-1
   # Output format: json
   ```

3. **Start CloudWatch Agent**:
   ```bash
   sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
     -a fetch-config \
     -m ec2 \
     -s \
     -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
   ```

4. **Create Dashboard** (optional):
   ```bash
   aws cloudwatch put-dashboard \
     --dashboard-name FlightAgentMonitoring \
     --dashboard-body file:///opt/flight-agent-docker/cloudwatch-dashboard.json
   ```

5. **Set Up Alarms**:
   ```bash
   # High CPU alert
   aws cloudwatch put-metric-alarm \
     --alarm-name flight-agent-high-cpu \
     --alarm-description "Alert when CPU exceeds 80%" \
     --metric-name ContainerCPU \
     --namespace FlightAgent \
     --statistic Average \
     --period 300 \
     --threshold 80 \
     --comparison-operator GreaterThanThreshold \
     --evaluation-periods 2

   # High memory alert
   aws cloudwatch put-metric-alarm \
     --alarm-name flight-agent-high-memory \
     --alarm-description "Alert when memory exceeds 80%" \
     --metric-name ContainerMemory \
     --namespace FlightAgent \
     --statistic Average \
     --period 300 \
     --threshold 80 \
     --comparison-operator GreaterThanThreshold \
     --evaluation-periods 2

   # Low request volume (service down?)
   aws cloudwatch put-metric-alarm \
     --alarm-name flight-agent-no-requests \
     --alarm-description "Alert when no requests in 10 minutes" \
     --metric-name RequestCount \
     --namespace FlightAgent \
     --statistic Sum \
     --period 600 \
     --threshold 1 \
     --comparison-operator LessThanThreshold \
     --evaluation-periods 1
   ```

### Monitoring Commands

```bash
# View health check logs
tail -f /var/log/flight-agent-docker.log

# View metrics logs
tail -f /var/log/flight-agent-metrics.log

# Manual health check
/opt/flight-agent-docker/healthcheck.sh

# Container stats
docker stats guardian-buddy-flight-agent

# CloudWatch Logs (if configured)
aws logs tail /aws/ec2/flight-agent --follow
```

### Cost
- **CloudWatch Logs**: First 5 GB/month free, then $0.50/GB
- **CloudWatch Metrics**: First 10 custom metrics free, then $0.30/metric/month
- **CloudWatch Alarms**: First 10 alarms free, then $0.10/alarm/month
- **Estimated**: **$0-5/month** depending on usage

---

## 2. HTTPS with Nginx & Let's Encrypt

Secure your Flight Agent with SSL/TLS certificates from Let's Encrypt.

### Features
- ✅ Free SSL certificates (Let's Encrypt)
- ✅ Automatic HTTPS redirect
- ✅ A+ SSL rating (Mozilla Modern config)
- ✅ Auto-renewal (every 90 days)
- ✅ Security headers
- ✅ Rate limiting

### Prerequisites
- Domain name pointing to your EC2 IP (54.158.27.0)
- Port 80 and 443 open in Security Group

### Setup

```bash
# SSH into EC2
ssh -i codefest.pem ubuntu@54.158.27.0

# Download and run setup script
curl -O https://raw.githubusercontent.com/rohanpc0701/Codefest_Flightapi/main/monitoring/nginx-https-setup.sh
chmod +x nginx-https-setup.sh

# Run with your domain
./nginx-https-setup.sh your-domain.com
```

### AWS Security Group Update

Add HTTPS inbound rule:
1. Go to EC2 Console → Security Groups
2. Find your instance's security group
3. Add Inbound Rule:
   - Type: **HTTPS**
   - Protocol: **TCP**
   - Port: **443**
   - Source: **0.0.0.0/0**

### DNS Setup

Point your domain to EC2:
```bash
# A Record
your-domain.com → 54.158.27.0

# Verify DNS propagation
dig your-domain.com
nslookup your-domain.com
```

### Test Your Setup

```bash
# Test HTTP redirect
curl -I http://your-domain.com
# Should return 301 redirect to HTTPS

# Test HTTPS
curl https://your-domain.com/health

# Test SSL certificate
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# SSL Labs test (A+ rating)
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com
```

### Management

```bash
# Nginx commands
sudo systemctl status nginx
sudo nginx -s reload
sudo nginx -t

# View logs
sudo tail -f /var/log/nginx/flight-agent-access.log
sudo tail -f /var/log/nginx/flight-agent-error.log

# Certificate management
sudo certbot certificates
sudo certbot renew --dry-run
sudo certbot renew

# Check auto-renewal timer
sudo systemctl status certbot.timer
```

### Cost
- **Let's Encrypt**: Free
- **Nginx**: Free
- **Total**: **$0/month** ✅

---

## 3. Redis Caching

Add Redis caching to reduce FlightAware API calls and improve response times.

### Features
- ✅ 5-minute cache TTL (configurable)
- ✅ 256MB memory limit
- ✅ LRU eviction policy
- ✅ Automatic cache invalidation
- ✅ Docker containerized
- ✅ Cache statistics

### Benefits
- 🚀 Faster response times (50-100ms vs 500-1000ms)
- 💰 Reduced API costs
- 📊 Better performance during high traffic

### Setup

```bash
# SSH into EC2
ssh -i codefest.pem ubuntu@54.158.27.0

# Download and run setup script
curl -O https://raw.githubusercontent.com/rohanpc0701/Codefest_Flightapi/main/monitoring/redis-cache-setup.sh
chmod +x redis-cache-setup.sh
./redis-cache-setup.sh
```

### Configuration

Edit `.env` to change cache TTL:
```bash
# Cache TTL in seconds
CACHE_TTL=300  # 5 minutes (default)
CACHE_TTL=600  # 10 minutes
CACHE_TTL=60   # 1 minute
```

Restart after changing:
```bash
cd /opt/flight-agent-docker
docker-compose restart flight-agent
```

### Usage in Code

The setup script creates `flight_agent/cache.py`. To integrate:

```python
from cache import get_cache

cache = get_cache()

# In your flight status handler
async def get_flight_status(flight_num: str, departure_date: str):
    # Try cache first
    cached = cache.get(flight_num, departure_date)
    if cached:
        logger.info(f"Cache HIT: {flight_num}")
        return FlightRaw(**cached)
    
    # Cache miss - fetch from API
    logger.info(f"Cache MISS: {flight_num}")
    data = await provider.fetch_status(flight_num, departure_date)
    
    # Cache the result
    cache.set(flight_num, departure_date, data.model_dump())
    
    return data
```

### Monitoring

```bash
# Check Redis is running
docker ps | grep redis

# Connect to Redis CLI
docker exec -it flight-agent-redis redis-cli

# View all keys
docker exec flight-agent-redis redis-cli KEYS '*'

# Get cache stats
docker exec flight-agent-redis redis-cli INFO stats

# View hit/miss ratio
docker exec flight-agent-redis redis-cli INFO stats | grep keyspace

# Memory usage
docker exec flight-agent-redis redis-cli INFO memory | grep used_memory_human

# Clear cache
docker exec flight-agent-redis redis-cli FLUSHDB
```

### Cost
- **Redis**: Included in Docker (no extra cost)
- **Memory**: Uses ~256MB of EC2 RAM
- **Total**: **$0/month** ✅

---

## 4. Application Load Balancer (Optional)

For production scale and auto-scaling capabilities.

### When You Need This
- Traffic > 1000 requests/hour
- Need high availability (99.99% uptime)
- Want auto-scaling based on load
- Multiple availability zones

### Setup Overview

1. **Create Target Group**
2. **Create Application Load Balancer**
3. **Configure Auto Scaling Group**
4. **Update DNS to point to ALB**

### Estimated Cost
- **ALB**: $16.20/month (base)
- **Data processing**: $0.008/GB
- **Additional EC2 instances**: $8.50/instance
- **Total**: **$20-40/month**

> ⚠️ **Note**: Only needed for high-traffic production. Current setup handles 100-500 req/hour easily.

---

## 5. GitHub Actions CI/CD

Automated deployment pipeline for continuous integration and delivery.

### Features
- ✅ Automated testing on push
- ✅ Docker image build and test
- ✅ Deploy to EC2
- ✅ Health checks and smoke tests
- ✅ Rollback on failure

### Setup

1. **Add GitHub Secret** (EC2 SSH Key):
   - Go to GitHub repo → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `EC2_SSH_KEY`
   - Value: Contents of your `codefest.pem` file
   ```bash
   cat codefest.pem
   # Copy the entire output including BEGIN/END lines
   ```

2. **Update EC2 for Git Access**:
   ```bash
   ssh -i codefest.pem ubuntu@54.158.27.0
   
   cd /opt/flight-agent-docker
   
   # Initialize git if not already done
   git init
   git remote add origin https://github.com/rohanpc0701/Codefest_Flightapi.git
   git fetch origin
   git branch -u origin/main main
   ```

3. **Test the Workflow**:
   ```bash
   # Make a change locally
   echo "# Test CI/CD" >> README.md
   git add README.md
   git commit -m "test: Trigger CI/CD pipeline"
   git push origin main
   
   # Watch in GitHub Actions tab
   # Visit: https://github.com/rohanpc0701/Codefest_Flightapi/actions
   ```

### Workflow Steps

The CI/CD pipeline automatically:

1. **Test** - Runs pytest and linting
2. **Build** - Builds Docker image with caching
3. **Test Docker** - Verifies image works
4. **Deploy** - SSHs to EC2 and deploys
5. **Smoke Test** - Validates deployment

### Manual Deployment Trigger

```bash
# Trigger deployment manually
gh workflow run deploy.yml
# Or via GitHub UI: Actions → Deploy Flight Agent → Run workflow
```

### Monitoring Deployments

```bash
# View deployment history
gh run list --workflow=deploy.yml

# View logs for specific run
gh run view <run-id> --log

# SSH to EC2 and check
ssh -i codefest.pem ubuntu@54.158.27.0
cd /opt/flight-agent-docker
docker-compose ps
docker logs guardian-buddy-flight-agent --tail 50
```

### Cost
- **GitHub Actions**: 2,000 minutes/month free (private repos)
- **Total**: **$0/month** ✅

---

## 6. Cost Breakdown

### Current Setup (EC2 + Docker)
| Service | Cost |
|---------|------|
| EC2 t2.micro | $0/month (Free Tier) |
| EBS Storage (8GB) | $0/month (Free Tier) |
| Data Transfer | $0/month (100GB free) |
| **Total** | **$0/month** ✅ |

### With All Enhancements
| Service | Cost |
|---------|------|
| EC2 t2.micro | $0/month (Free Tier) |
| CloudWatch | $0-5/month |
| Let's Encrypt/Nginx | $0/month |
| Redis (Docker) | $0/month |
| GitHub Actions | $0/month |
| **Total** | **$0-5/month** ✅ |

### After Free Tier (12 months)
| Service | Cost |
|---------|------|
| EC2 t2.micro | $8.50/month |
| EBS Storage (8GB) | $0.80/month |
| Data Transfer | $0.09/GB |
| CloudWatch | $5/month |
| Let's Encrypt/Nginx | $0/month |
| Redis (Docker) | $0/month |
| GitHub Actions | $0/month |
| **Total** | **$15-20/month** |

### Scaling to Production (Optional)
| Service | Cost |
|---------|------|
| ALB | $16/month |
| EC2 t3.small (x2) | $30/month |
| RDS (optional) | $15/month |
| **Total** | **$75-100/month** |

---

## 🎯 Recommended Implementation Order

### Phase 1: MVP (Current) ✅
- [x] Docker deployment
- [x] Basic monitoring (Docker logs)
- [x] Manual deployment

### Phase 2: Monitoring & Security (Week 1)
- [ ] CloudWatch monitoring
- [ ] HTTPS with Let's Encrypt
- [ ] Automated health checks

### Phase 3: Performance (Week 2)
- [ ] Redis caching
- [ ] Performance optimization
- [ ] Load testing

### Phase 4: Automation (Week 3)
- [ ] GitHub Actions CI/CD
- [ ] Automated testing
- [ ] Deployment automation

### Phase 5: Scale (When Needed)
- [ ] Application Load Balancer
- [ ] Auto-scaling
- [ ] Multi-AZ deployment

---

## 📚 Quick Reference

### Setup Scripts Location
All scripts are in the `monitoring/` directory:
- `cloudwatch-setup.sh` - CloudWatch monitoring
- `nginx-https-setup.sh` - HTTPS setup
- `redis-cache-setup.sh` - Redis caching

### Quick Commands

```bash
# Health check
curl http://54.158.27.0:8001/health

# View logs
ssh -i codefest.pem ubuntu@54.158.27.0
docker logs guardian-buddy-flight-agent -f

# Restart service
cd /opt/flight-agent-docker && docker-compose restart

# Update code
cd /opt/flight-agent-docker
git pull origin main
docker-compose up -d --build

# Monitor resources
docker stats guardian-buddy-flight-agent

# Clear Redis cache
docker exec flight-agent-redis redis-cli FLUSHDB
```

---

## 🆘 Troubleshooting

### CloudWatch Issues
- **Agent not starting**: Check IAM permissions
- **No metrics**: Verify namespace is `FlightAgent`
- **Logs not appearing**: Check log group `/aws/ec2/flight-agent`

### HTTPS Issues
- **Certificate failed**: Verify DNS points to EC2 IP
- **Port 443 blocked**: Check Security Group
- **Renewal failed**: Run `sudo certbot renew --dry-run`

### Redis Issues
- **Connection refused**: Check Redis container is running
- **Cache not working**: Verify REDIS_HOST=redis in env
- **High memory**: Adjust maxmemory in docker-compose.yml

### CI/CD Issues
- **Deployment failed**: Check EC2_SSH_KEY secret
- **SSH timeout**: Verify Security Group allows SSH
- **Docker build failed**: Check Dockerfile syntax

---

## 🎓 Learning Resources

- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [Docker Documentation](https://docs.docker.com/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)

---

**Last Updated**: October 11, 2025  
**Maintained by**: Guardian Buddy Team

