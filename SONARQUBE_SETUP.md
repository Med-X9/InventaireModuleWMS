# SonarQube Integration Setup Guide for InventaireModuleWMS

This guide provides step-by-step instructions to set up SonarQube integration with Jenkins for the InventaireModuleWMS Django project.

## Prerequisites

- Docker installed on your system
- Jenkins server with admin access
- Git repository access
- Basic familiarity with Jenkins and Docker

## Step 1: Deploy SonarQube with Docker

### 1.1 Pull and Run SonarQube Container

```bash
# Pull SonarQube Docker image
docker pull sonarqube:lts

# Run SonarQube container
docker run -d --name sonarqube \
  -p 9000:9000 \
  -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true \
  sonarqube:lts
```

### 1.2 Access SonarQube UI

1. Navigate to `http://your-server-ip:9000` in your web browser
2. Default login credentials: `admin/admin`
3. You'll be prompted to change the password on first login

## Step 2: Configure SonarQube Project

### 2.1 Create New Project

1. Log in to SonarQube with admin credentials
2. Click **"Projects"** → **"Create Project"**
3. Choose **"Manually"**
4. Enter project details:
   - **Project key**: `inventaire-module-wms`
   - **Display name**: `InventaireModuleWMS`
5. Click **"Set Up"**

### 2.2 Generate Authentication Token

1. Go to **"My Account"** → **"Security"** → **"Generate Tokens"**
2. Enter token name: `jenkins-integration`
3. Click **"Generate"**
4. **Important**: Copy and save the token securely (you won't see it again)

## Step 3: Configure Jenkins

### 3.1 Install Required Jenkins Plugins

1. Navigate to **"Manage Jenkins"** → **"Manage Plugins"**
2. Go to **"Available"** tab
3. Search and install:
   - **SonarQube Scanner for Jenkins** (version 2.11 or later)
   - **Pipeline** (if not already installed)

### 3.2 Configure SonarQube Scanner Tool

1. Go to **"Manage Jenkins"** → **"Global Tool Configuration"**
2. Scroll to **"SonarQube Scanner"** section
3. Click **"Add SonarQube Scanner"**
4. Configure:
   - **Name**: `sonar-scanner`
   - **Install automatically**: ✅ Check this
   - **Version**: Select latest version

### 3.3 Configure SonarQube Server

1. Go to **"Manage Jenkins"** → **"Configure System"**
2. Scroll to **"SonarQube servers"** section
3. Click **"Add SonarQube"**
4. Configure:
   - **Name**: `SonarQube-Server`
   - **Server URL**: `http://your-sonar-server:9000`
   - **Server authentication token**: Select credential (see next step)

### 3.4 Add SonarQube Credentials

1. Go to **"Manage Jenkins"** → **"Manage Credentials"**
2. Select appropriate domain (usually "Global")
3. Click **"Add Credentials"**
4. Configure:
   - **Kind**: Secret text
   - **Secret**: Paste the SonarQube token from Step 2.2
   - **ID**: `sonar-token`
   - **Description**: `SonarQube Authentication Token`

## Step 4: Project Configuration Files

The following files have been created in your project root:

### 4.1 `sonar-project.properties`
Contains main SonarQube configuration including:
- Project identification
- Source code paths
- Exclusions for Django-specific files
- Coverage settings

### 4.2 `.sonarignore`
Additional file patterns to exclude from analysis

### 4.3 `.coveragerc`
Coverage configuration for Python test coverage integration

## Step 5: Jenkins Pipeline Integration

The Jenkinsfile has been updated with a new `SonarQube Analysis` stage that:

1. **Runs before the Docker build stage**
2. **Sets up Python environment** (optional for testing)
3. **Executes SonarQube scanner** with project-specific parameters
4. **Waits for Quality Gate result**
5. **Provides feedback** on analysis results

### Pipeline Flow:
1. Check Branch
2. Clone Repositories
3. **🔍 SonarQube Analysis** ← New stage
4. Build Backend Docker Image
5. Push Docker Images
6. Upload Essential Files
7. Deploy Backend

## Step 6: Running the Analysis

### 6.1 Trigger Pipeline

1. Push code to `dev` or `main` branch
2. Jenkins will automatically trigger the pipeline
3. Monitor the SonarQube Analysis stage

### 6.2 View Results

1. **Jenkins Console**: Check build logs for SonarQube output
2. **SonarQube Dashboard**: Visit `http://your-sonar-server:9000/dashboard?id=inventaire-module-wms`

## Step 7: Quality Gate Configuration

### 7.1 Default Quality Gate
SonarQube comes with a default "Sonar way" quality gate that checks:
- **Coverage**: > 80%
- **Duplicated Lines**: < 3%
- **Maintainability Rating**: A
- **Reliability Rating**: A
- **Security Rating**: A

### 7.2 Custom Quality Gate (Optional)
1. Go to **"Quality Gates"** in SonarQube
2. Create new gate or modify existing
3. Set conditions specific to your Django project

## Troubleshooting

### Common Issues:

1. **Scanner not found**
   - Verify SonarQube Scanner installation in Jenkins Global Tools
   - Check tool name matches pipeline configuration

2. **Authentication failed**
   - Verify SonarQube token is correct
   - Check credential ID matches pipeline configuration

3. **Quality Gate timeout**
   - Increase timeout in pipeline (currently 5 minutes)
   - Check SonarQube server performance

4. **Python environment issues**
   - Ensure Python 3.12+ is available on Jenkins agent
   - Verify requirements.txt dependencies can be installed

### Useful Commands:

```bash
# Check SonarQube container logs
docker logs sonarqube

# Restart SonarQube container
docker restart sonarqube

# Manual SonarQube scanner execution (for testing)
sonar-scanner -Dsonar.projectKey=inventaire-module-wms \
              -Dsonar.sources=apps,project,config \
              -Dsonar.host.url=http://localhost:9000 \
              -Dsonar.login=your-token
```

## Best Practices

1. **Regular Analysis**: Run SonarQube analysis on every commit to dev/main branches
2. **Quality Gates**: Don't fail builds on first integration - monitor and improve gradually
3. **Coverage**: Implement unit tests to improve coverage metrics
4. **Security**: Regularly update SonarQube and review security findings
5. **Team Training**: Ensure development team understands SonarQube metrics

## Next Steps

1. **Monitor Initial Results**: Review first analysis report
2. **Address Critical Issues**: Fix security vulnerabilities and bugs first
3. **Improve Coverage**: Add unit tests for uncovered code
4. **Customize Rules**: Adjust quality profile for Django best practices
5. **Team Integration**: Train team on interpreting SonarQube results

## Support

For issues with this integration:
1. Check Jenkins build logs
2. Review SonarQube analysis logs
3. Consult SonarQube documentation: https://docs.sonarqube.org/
4. Jenkins SonarQube plugin docs: https://plugins.jenkins.io/sonar/
