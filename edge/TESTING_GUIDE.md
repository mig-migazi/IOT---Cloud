# GRM Service Testing Guide

This guide will help you test the GRM service locally while connecting to an Izuma agent deployed on a remote Linux machine.

## Prerequisites

1. **Python 3.9+** installed on your local machine
2. **Network connectivity** to the remote Linux machine
3. **Izuma agent** running on the remote Linux machine
4. **API credentials** for the Izuma agent

## Quick Start

### 1. Initial Setup

```bash
cd edge

# Install dependencies
pip install -r requirements.txt

# Run initial setup
python test_config.py
```

### 2. Configure Test Environment

Edit the generated `test.env` file with your remote Izuma agent details:

```bash
# Remote Izuma Agent Configuration
IZUMA_API_BASE_URL=http://YOUR_REMOTE_LINUX_IP:8080
IZUMA_ACCESS_KEY=your_test_access_key_here
IZUMA_DEVICE_ID=edge-test-device-001
```

**Important**: Replace `YOUR_REMOTE_LINUX_IP` with the actual IP address of your remote Linux machine.

### 3. Test Connectivity

```bash
# Test basic connectivity and HTTP endpoints
python test_connectivity.py
```

This will test:
- Basic network connectivity
- HTTP endpoint availability
- IzumaNetworks client initialization
- Resource loading

### 4. Test Service Components

```bash
# Test individual service components
python test_service.py
```

This will test:
- Service initialization
- GRM registration
- Resource synchronization
- Health monitoring
- Full service lifecycle

### 5. Run the Service

```bash
# Start the GRM service with test environment
python run_test.py
```

## Testing Scenarios

### Scenario 1: Basic Connectivity Test

**Purpose**: Verify network connectivity to remote Izuma agent

**Steps**:
1. Run `python test_connectivity.py`
2. Check output for connectivity status
3. Verify HTTP endpoints are accessible

**Expected Results**:
- ✅ Basic connectivity successful
- ✅ HTTP connection successful (or warnings if endpoints don't exist)
- ✅ IzumaNetworks client initialized
- ✅ Resource loading successful

### Scenario 2: Component Testing

**Purpose**: Test individual service components

**Steps**:
1. Run `python test_service.py`
2. Monitor component test results
3. Check for any initialization errors

**Expected Results**:
- ✅ All component tests pass
- ✅ Service initialization successful
- ✅ GRM registration successful
- ✅ Resource synchronization completed

### Scenario 3: Full Service Test

**Purpose**: Test complete service lifecycle

**Steps**:
1. Run `python run_test.py`
2. Monitor service startup
3. Check logs for any errors
4. Stop service with Ctrl+C

**Expected Results**:
- ✅ Service starts successfully
- ✅ GRM registration completed
- ✅ Resources synchronized
- ✅ Health monitoring active
- ✅ Graceful shutdown on Ctrl+C

## Troubleshooting

### Common Issues

#### 1. Network Connectivity Issues

**Symptoms**:
- "Basic connectivity failed"
- "Socket connection error"

**Solutions**:
- Check network connectivity: `ping YOUR_REMOTE_LINUX_IP`
- Verify firewall settings
- Check if Izuma agent is running on remote machine
- Verify port number in configuration

#### 2. Authentication Issues

**Symptoms**:
- "GRM registration failed"
- "401 Unauthorized" errors

**Solutions**:
- Verify access key in `test.env`
- Check if access key has proper permissions
- Ensure device ID is unique and valid

#### 3. Resource Loading Issues

**Symptoms**:
- "resources.json not found"
- "Invalid JSON in resources file"

**Solutions**:
- Verify `resources.json` exists in edge directory
- Check JSON syntax validity
- Ensure all required fields are present

#### 4. Service Initialization Issues

**Symptoms**:
- "Service initialization failed"
- Import errors

**Solutions**:
- Check Python version (3.11+ required)
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check environment variables in `test.env`

### Debug Mode

Enable debug logging for more detailed information:

```bash
# Edit test.env and set:
LOG_LEVEL=DEBUG
```

### Manual Testing

Test individual components manually:

```python
# Test IzumaNetworks client
from grm_service.izuma_client import IzumaClient
client = IzumaClient()
client.health_check()

# Test resource loading
from grm_service.utils import load_resources
resources = load_resources("resources.json")
print(f"Loaded {len(resources)} resources")
```

## Monitoring and Logs

### Log Files

Logs are stored in the `logs/` directory:
- `logs/grm_service.log` - Main service logs
- Logs are rotated at 10MB with 7-day retention

### Real-time Monitoring

```bash
# Monitor logs in real-time
tail -f logs/grm_service.log

# Monitor with grep for specific events
tail -f logs/grm_service.log | grep "GRM registration"
tail -f logs/grm_service.log | grep "Resource sync"
```

### Log Levels

- `DEBUG`: Detailed debugging information
- `INFO`: General information about service operation
- `WARNING`: Warning messages for non-critical issues
- `ERROR`: Error messages for failed operations

## Performance Testing

### Load Testing

To test with multiple resources:

1. Add more resources to `resources.json`
2. Run service and monitor performance
3. Check resource synchronization time
4. Monitor memory and CPU usage

### Stress Testing

```bash
# Run service for extended period
python run_test.py

# Monitor system resources
top -p $(pgrep -f "python.*run_test.py")
```

## Integration Testing

### With Remote Izuma Agent

1. **Verify Remote Agent Status**:
   ```bash
   # On remote Linux machine
   curl http://localhost:8080/health
   ```

2. **Check Agent Logs**:
   ```bash
   # On remote Linux machine
   tail -f /var/log/izuma-agent.log
   ```

3. **Monitor Network Traffic**:
   ```bash
   # On local machine
   tcpdump -i any host YOUR_REMOTE_LINUX_IP
   ```

### API Testing

Test specific API endpoints:

```bash
# Test health endpoint
curl http://YOUR_REMOTE_LINUX_IP:8080/health

# Test GRM registration endpoint
curl -X POST http://YOUR_REMOTE_LINUX_IP:8080/api/v1/grm/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_KEY" \
  -d '{"deviceId":"test","serviceName":"test"}'
```

## Cleanup

### Stop Service

```bash
# Graceful shutdown
Ctrl+C

# Force stop if needed
pkill -f "python.*run_test.py"
```

### Clean Logs

```bash
# Clear old logs
rm -rf logs/*.log
```

### Reset Environment

```bash
# Remove test environment
rm test.env
```

## Next Steps

After successful testing:

1. **Production Deployment**: Update configuration for production environment
2. **Monitoring Setup**: Configure monitoring and alerting
3. **Security Review**: Review security settings and API keys
4. **Documentation**: Update documentation with actual endpoints and configurations

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review logs in `logs/grm_service.log`
3. Verify network connectivity and firewall settings
4. Ensure Izuma agent is properly configured on remote machine
