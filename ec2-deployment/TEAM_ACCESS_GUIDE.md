# 👥 Team Access Guide - Flight Agent EC2

## 🌐 Public Access Information

### Endpoints (No Authentication Required)
- **Health Check**: `http://YOUR_EC2_IP/health`
- **Agent Card**: `http://YOUR_EC2_IP/agent.json`
- **Flight Status API**: `http://YOUR_EC2_IP/a2a` (POST)

### Example API Call
```bash
curl -X POST http://YOUR_EC2_IP/a2a \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_flight_status",
    "params": {
      "flight_num": "DL2990",
      "departure_date": "2025-10-11"
    },
    "id": "test"
  }'
```

## 🔑 SSH Access for Team Members

### Option 1: Shared SSH Key (Recommended)
1. **Share the SSH key file** (`flight-agent-key.pem`) with team members
2. **Set permissions**: `chmod 400 flight-agent-key.pem`
3. **SSH command**: `ssh -i flight-agent-key.pem ubuntu@YOUR_EC2_IP`

### Option 2: Multiple Key Pairs
1. **Create additional key pairs** in AWS Console
2. **Add public keys** to the EC2 instance
3. **Each team member** uses their own key

### Option 3: SSH Key Management
```bash
# Add team member's public key to authorized_keys
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC..." >> ~/.ssh/authorized_keys

# Or use ssh-copy-id (if team member has local access)
ssh-copy-id -i team-member-key.pub ubuntu@YOUR_EC2_IP
```

## 🛠️ Team Management Commands

### Service Management
```bash
# Check service status
sudo supervisorctl status flight-agent

# View logs
sudo tail -f /var/log/flight-agent.log

# Restart service
sudo supervisorctl restart flight-agent

# Stop service
sudo supervisorctl stop flight-agent

# Start service
sudo supervisorctl start flight-agent
```

### Code Updates
```bash
# Upload new code (from team member's machine)
scp -i flight-agent-key.pem -r flight_agent ubuntu@YOUR_EC2_IP:/opt/flight-agent/

# Restart service after update
sudo supervisorctl restart flight-agent
```

### System Monitoring
```bash
# Check system resources
htop
df -h
free -h

# Check network connections
netstat -tlnp
ss -tlnp

# Check service logs
journalctl -u supervisor -f
```

## 🔒 Security Considerations

### Current Configuration
- ✅ **HTTP (80)**: Open to public (required for API access)
- ✅ **SSH (22)**: Restricted to specific IPs or key-based access
- ✅ **Custom TCP (8001)**: Open to public (direct app access)

### Recommended Security Enhancements
```bash
# Install fail2ban for SSH protection
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Configure firewall (if needed)
sudo ufw enable
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 8001
```

## 📊 Monitoring & Logs

### Application Logs
```bash
# Real-time logs
sudo tail -f /var/log/flight-agent.log

# Log rotation (if needed)
sudo logrotate -f /etc/logrotate.d/flight-agent
```

### System Logs
```bash
# System messages
sudo journalctl -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 🚨 Troubleshooting

### Common Issues
1. **Service not starting**: Check logs with `sudo tail -f /var/log/flight-agent.log`
2. **Port conflicts**: Check with `sudo netstat -tlnp | grep :8001`
3. **Permission issues**: Ensure `ubuntu` user owns `/opt/flight-agent`
4. **API key issues**: Verify environment variables in `.env` file

### Recovery Commands
```bash
# Restart everything
sudo supervisorctl restart flight-agent
sudo systemctl restart nginx

# Check service status
sudo supervisorctl status
sudo systemctl status nginx

# View error logs
sudo journalctl -u supervisor -n 50
sudo journalctl -u nginx -n 50
```

## 📱 Team Communication

### Share with Team Members
1. **Public IP address** of the EC2 instance
2. **SSH key file** (`flight-agent-key.pem`)
3. **This guide** for reference
4. **Test commands** to verify access

### Team Responsibilities
- **Primary Admin**: Manages SSH access and service updates
- **Team Members**: Can test APIs and report issues
- **Developers**: Can update code and restart services

## 💰 Cost Management

### Free Tier Limits
- **Instance Hours**: 750/month (enough for 24/7)
- **Storage**: 30GB (sufficient for application)
- **Data Transfer**: 1GB/month outbound
- **Duration**: 12 months from AWS account creation

### Monitoring Costs
```bash
# Check instance usage
aws ec2 describe-instances --instance-ids YOUR_INSTANCE_ID

# Monitor data transfer
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name NetworkOut \
  --dimensions Name=InstanceId,Value=YOUR_INSTANCE_ID \
  --start-time 2025-10-01T00:00:00Z \
  --end-time 2025-10-11T23:59:59Z \
  --period 86400 \
  --statistics Sum
```

## 🎯 Next Steps

1. **Deploy the instance** using the provided script
2. **Share the public IP** with team members
3. **Distribute SSH keys** to team members
4. **Test API endpoints** from different locations
5. **Set up monitoring** if needed
6. **Document any custom configurations**

---

**Note**: This setup prioritizes ease of access for team collaboration while maintaining basic security. For production environments, consider additional security measures like VPN access, API authentication, and more restrictive firewall rules.
