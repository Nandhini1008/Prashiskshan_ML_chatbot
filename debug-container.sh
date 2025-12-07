#!/bin/bash
# Debug script for container issues

echo "=========================================="
echo "Container Debug Information"
echo "=========================================="

echo ""
echo "1. Container Status:"
docker ps -a

echo ""
echo "2. Qdrant Logs:"
docker logs chatbot-qdrant --tail 50

echo ""
echo "3. Redis Logs:"
docker logs chatbot-redis --tail 50

echo ""
echo "4. Chatbot Container Logs:"
docker logs chatbot-service --tail 50 2>&1 || echo "Container not running or no logs"

echo ""
echo "5. Qdrant Health Check:"
curl -f http://localhost:6333/health 2>&1 || echo "Qdrant health check failed"

echo ""
echo "6. Redis Health Check:"
docker exec chatbot-redis redis-cli ping 2>&1 || echo "Redis health check failed"

echo ""
echo "7. Supervisor Logs (if container is running):"
docker exec chatbot-service cat /var/log/supervisor/supervisord.log 2>&1 || echo "Cannot access supervisor logs"

echo ""
echo "8. Chatbot Application Logs:"
docker exec chatbot-service cat /var/log/supervisor/chatbot_out.log 2>&1 || echo "Cannot access chatbot logs"
docker exec chatbot-service cat /var/log/supervisor/chatbot_err.log 2>&1 || echo "Cannot access chatbot error logs"

echo ""
echo "9. Nginx Logs:"
docker exec chatbot-service cat /var/log/supervisor/nginx_out.log 2>&1 || echo "Cannot access nginx logs"
docker exec chatbot-service cat /var/log/supervisor/nginx_err.log 2>&1 || echo "Cannot access nginx error logs"

echo ""
echo "10. Environment Variables:"
docker exec chatbot-service env | grep -E "(REDIS|QDRANT|CHATBOT)" 2>&1 || echo "Cannot access environment"

echo ""
echo "=========================================="


