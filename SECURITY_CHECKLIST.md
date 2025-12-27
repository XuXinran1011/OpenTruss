# OpenTruss Security Checklist

This document provides a security checklist for OpenTruss deployment and operation.

## Pre-Deployment Security Checks

### 1. Environment Variables
- [ ] `JWT_SECRET_KEY` is set to a strong random value (use `openssl rand -hex 32`)
- [ ] `JWT_SECRET_KEY` is NOT the default value from `.env.example`
- [ ] `CORS_ORIGINS` is set to specific domains (NOT `*`)
- [ ] Database credentials are secure and not using defaults
- [ ] All sensitive environment variables are stored securely (not in code)

### 2. Authentication & Authorization
- [ ] JWT tokens are using strong algorithm (HS256 or RS256)
- [ ] Token expiration time is reasonable (default: 1440 minutes)
- [ ] Role-based access control (RBAC) is properly configured
- [ ] Default users have been changed or removed
- [ ] Password hashing uses bcrypt with sufficient rounds (≥12)

### 3. API Security
- [ ] Rate limiting is configured (if applicable)
- [ ] Input validation is enabled for all endpoints
- [ ] SQL/Cypher injection prevention (parameterized queries)
- [ ] File upload validation (size, type, content)
- [ ] Error messages don't leak sensitive information

### 4. Network Security
- [ ] HTTPS is enabled in production
- [ ] CORS is properly configured (specific origins only)
- [ ] Database is not exposed to public internet
- [ ] Internal services use secure communication
- [ ] Firewall rules are properly configured

### 5. Dependency Security
- [ ] All dependencies are up-to-date
- [ ] Known vulnerabilities are addressed
- [ ] Regular dependency audits are scheduled
- [ ] Critical security updates are applied promptly

### 6. Data Security
- [ ] Sensitive data is encrypted at rest (if applicable)
- [ ] Backups are encrypted
- [ ] Access logs are enabled and monitored
- [ ] Data retention policies are defined
- [ ] PII (Personally Identifiable Information) handling complies with regulations

### 7. Monitoring & Logging
- [ ] Security events are logged
- [ ] Failed authentication attempts are monitored
- [ ] Unusual access patterns are detected
- [ ] Logs don't contain sensitive information
- [ ] Log retention policy is defined

### 8. Docker & Container Security
- [ ] Docker images are scanned for vulnerabilities
- [ ] Containers run as non-root user (if applicable)
- [ ] Minimal base images are used
- [ ] Unnecessary packages are removed
- [ ] Secrets are not hardcoded in Dockerfiles

### 9. Infrastructure Security
- [ ] Regular security updates are applied
- [ ] Unnecessary services are disabled
- [ ] SSH access is secured (key-based, no password)
- [ ] Backup encryption is enabled
- [ ] Disaster recovery plan is documented

## Security Best Practices

### For Developers
1. **Never commit secrets**: Use `.env` files (in `.gitignore`) and environment variables
2. **Keep dependencies updated**: Regularly run security audits
3. **Use parameterized queries**: Never concatenate user input into queries
4. **Validate all input**: Use Pydantic models for API validation
5. **Follow principle of least privilege**: Grant minimum necessary permissions

### For Operators
1. **Regular backups**: Test backup and restore procedures
2. **Monitor logs**: Set up alerts for suspicious activities
3. **Update regularly**: Keep system and dependencies updated
4. **Use secrets management**: Consider tools like HashiCorp Vault
5. **Incident response**: Have a plan for security incidents

## Security Tools

### Dependency Scanning
```bash
# Python dependencies
pip install pip-audit
pip-audit

# or using safety
pip install safety
safety check

# npm dependencies
npm audit
npm audit fix
```

### Container Scanning
```bash
# Using Trivy (recommended)
trivy image opentruss/backend:latest
trivy image opentruss/frontend:latest
```

### Code Scanning
- Consider using SonarQube, CodeQL, or similar tools
- Enable Dependabot or Renovate for automatic dependency updates

## Reporting Security Issues

If you discover a security vulnerability, please do NOT open a public issue. Instead:

1. Email security@your-domain.com (if available)
2. Or create a private security advisory on GitHub
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to address the issue before public disclosure.

## Compliance

- Ensure compliance with applicable data protection regulations (GDPR, CCPA, etc.)
- Review and update this checklist regularly
- Document security decisions in ADR (Architecture Decision Records)

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [Memgraph Security Guide](https://memgraph.com/docs/memgraph/security)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

