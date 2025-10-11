# Guardian Buddy Flight Agent - Deployment Package

## Quick Deploy to Lightsail

1. Upload this folder to your Lightsail instance:
   ```bash
   scp -i your-key.pem -r flight_agent ubuntu@YOUR_IP:/opt/guardian-buddy/
   ```

2. SSH into your instance:
   ```bash
   ssh -i your-key.pem ubuntu@YOUR_IP
   ```

3. Run the deployment script:
   ```bash
   cd /opt/guardian-buddy
   chmod +x scripts/deploy_to_lightsail.sh
   ./scripts/deploy_to_lightsail.sh
   ```

## Manual Deploy

See: ../AWS_LIGHTSAIL_DEPLOYMENT.md
