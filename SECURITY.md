# Security Policy

## Supported Versions

We take security seriously and maintain security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.x.x   | :white_check_mark: |
| 1.x.x   | :x:                |

## Reporting a Vulnerability

### 🚨 Security Vulnerability Reporting

If you discover a security vulnerability in this project, please follow responsible disclosure practices:

**DO:**
- Report the vulnerability privately via GitHub Security Advisories
- Provide detailed information about the vulnerability
- Allow reasonable time for the issue to be addressed before public disclosure
- Work with us to verify and address the issue

**DO NOT:**
- Publicly disclose the vulnerability before it has been addressed
- Exploit the vulnerability for malicious purposes
- Access data that doesn't belong to you

### How to Report

1. **GitHub Security Advisories (Preferred)**
   - Go to the repository's Security tab
   - Click "Report a vulnerability"
   - Fill out the advisory form with detailed information

2. **Email (Alternative)**
   - Contact: [Repository Owner Email]
   - Subject: "SECURITY: [Brief Description]"
   - Include: Detailed vulnerability description, reproduction steps, impact assessment

### What to Include

When reporting a vulnerability, please include:

- **Description**: Clear description of the vulnerability
- **Impact**: Potential security impact and affected components
- **Reproduction**: Step-by-step instructions to reproduce the issue
- **Environment**: Version information and relevant system details
- **Proof of Concept**: If applicable, provide PoC code (safely)
- **Suggested Fix**: If you have ideas for remediation

### Response Timeline

- **Initial Response**: Within 48 hours of receipt
- **Vulnerability Assessment**: Within 5 business days
- **Status Updates**: Weekly updates on progress
- **Resolution Target**: Critical issues within 30 days, others within 90 days

## Security Best Practices

### For Users

**Network Security:**
- Use firewalls to restrict access to mining devices
- Change default passwords on Bitaxe devices
- Use secure WiFi networks (WPA3 recommended)
- Regularly update device firmware

**Monitoring Configuration:**
- Review `config.yaml` for sensitive information
- Use read-only access where possible
- Limit network exposure of monitoring interfaces
- Enable HTTPS for web interfaces when possible

**Docker Security:**
- Run containers as non-root users (already configured)
- Use specific image versions rather than `latest`
- Regularly update base images
- Limit container network access

### For Developers

**Code Security:**
- No hardcoded credentials or API keys
- Input validation for all user inputs
- Secure handling of configuration files
- Regular dependency updates
- Code review for all changes

**Web Interface Security:**
- Input sanitization and validation
- Protection against XSS and CSRF attacks
- Secure session management
- Rate limiting for API endpoints

## Security Features

### Current Security Measures

✅ **Code Security:**
- CodeQL static analysis in CI/CD pipeline
- Dependabot for automated dependency updates
- No hardcoded secrets or credentials
- Input validation on all user inputs

✅ **Container Security:**
- Non-root user execution
- Minimal attack surface with slim base images
- Read-only filesystem where possible
- Proper file permissions

✅ **Network Security:**
- Configurable network bindings
- No unnecessary port exposures
- Optional network isolation with Docker networks

✅ **Data Protection:**
- Local data storage (no cloud dependencies)
- Configurable data retention
- Automatic backup capabilities
- SQLite database with file-level permissions

### Authentication & Authorization

**Current Status:** Basic (local access only)
- No authentication required for local interfaces
- Network access controlled by firewall/network configuration
- Docker container isolation

**Recommendations for Production:**
- Implement authentication for web interfaces
- Use reverse proxy with SSL/TLS termination
- Configure network-level access controls
- Consider VPN access for remote monitoring

## Known Security Considerations

### Low Risk Items

1. **Local File Access**: Application requires read/write access to local files for data storage
2. **Network Scanning**: Application performs network requests to discover and monitor devices
3. **Configuration Exposure**: Config files may contain IP addresses and network topology

### Mitigation Strategies

- **File Permissions**: Run with minimal required permissions
- **Network Isolation**: Use Docker networks for container isolation
- **Configuration Security**: Store sensitive configs outside version control
- **Monitoring**: Regular security scanning and updates

## Security Updates

### Update Process

1. **Critical Security Issues**: Immediate hotfix releases
2. **Security Improvements**: Included in regular releases
3. **Dependency Updates**: Automated via Dependabot
4. **Security Advisories**: Published via GitHub Security Advisories

### Notification Channels

- GitHub Security Advisories
- Release notes and changelogs
- Repository Issues (for non-sensitive security improvements)

## Compliance and Standards

### Security Standards Followed

- **OWASP Top 10**: Web application security best practices
- **CIS Controls**: Basic security controls implementation
- **Container Security**: Docker security best practices
- **Python Security**: Secure coding practices for Python applications

### Regular Security Activities

- **Dependency Scanning**: Automated via Dependabot and CodeQL
- **Static Code Analysis**: Integrated in CI/CD pipeline
- **Security Reviews**: Manual review of security-sensitive changes
- **Vulnerability Monitoring**: Regular monitoring of security advisories

## Security Resources

### For Security Researchers

- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Python Security Guidelines](https://python-security.readthedocs.io/)

### For Users

- [Network Security Best Practices](https://www.nist.gov/cybersecurity)
- [Home Network Security](https://www.cisa.gov/sites/default/files/publications/home-network-security_508.pdf)
- [IoT Device Security](https://www.cisa.gov/uscert/ncas/tips/ST17-001)

## Contact

For security-related questions or concerns:

- **Security Issues**: Use GitHub Security Advisories
- **General Security Questions**: Open a GitHub Issue with the `security` label
- **Security Improvements**: Submit a Pull Request with security enhancements

---

**Remember**: Security is a shared responsibility. Users should follow security best practices for their network environment and keep the monitoring software updated.

*Last updated: 2025-01-25*