pipeline {
    agent any

    environment {
        BACKEND_REPO  = 'https://github.com/Med-X9/InventaireModuleWMS.git'
        IMAGE_PREFIX = 'smatchdigital'
        BACKEND_IMAGE  = "${IMAGE_PREFIX}/backend-app"
        IMAGE_TAG = "latest"
        
        // Deployment configuration
        DEPLOY_HOST  = "${env.BRANCH_NAME == 'main' ? '31.97.158.68' : (env.BRANCH_NAME == 'dev' ? '147.93.55.221' : '')}"
        DEPLOY_CREDS = "${env.BRANCH_NAME == 'main' ? 'prod-creds' : (env.BRANCH_NAME == 'dev' ? 'dev-test-creds' : '')}"
        ENV_NAME     = "${env.BRANCH_NAME == 'main' ? 'production' : (env.BRANCH_NAME == 'dev' ? 'development' : '')}"
        
        // SonarQube
        SONAR_PROJECT_KEY = "inventaire-module-wms-${env.BRANCH_NAME}"
        SONAR_PROJECT_NAME = "InventaireModuleWMS-${env.BRANCH_NAME}"
        SONAR_PROJECT_VERSION = '1.0'
    }

    stages {
        stage('Check Branch') {
            steps {
                script {
                    if (env.BRANCH_NAME != 'dev' && env.BRANCH_NAME != 'main') {
                        echo "Skipping deployment - not on dev or main branch. Current branch: ${env.BRANCH_NAME}"
                        currentBuild.result = 'SUCCESS'
                        return
                    }
                    echo "Proceeding with deployment on ${env.BRANCH_NAME} branch to ${env.ENV_NAME} environment"
                    echo "Deploy target: ${env.DEPLOY_HOST}"
                }
            }
        }

        stage('Clone Repositories') {
            when {
                anyOf {
                    branch 'dev'
                    branch 'main'
                }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'git-cred', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                    sh """
                        # Nettoyer le répertoire existant
                        rm -rf /tmp/backend
                        
                        # Cloner le repository
                        echo "Cloning repository branch ${env.BRANCH_NAME}..."
                        git clone --single-branch --branch ${env.BRANCH_NAME} https://\$GIT_USER:\$GIT_PASS@github.com/Med-X9/InventaireModuleWMS.git /tmp/backend
                        
                        # Vérifier que le clone a réussi
                        if [ ! -d /tmp/backend ]; then
                            echo "ERROR: Repository clone failed - directory not created!"
                            exit 1
                        fi
                        
                        # Vérifier que le répertoire n'est pas vide
                        if [ -z "\$(ls -A /tmp/backend)" ]; then
                            echo "ERROR: Repository clone failed - directory is empty!"
                            exit 1
                        fi
                        
                        echo "✓ Repository cloned successfully"
                        cd /tmp/backend
                        echo "Current branch: \$(git branch --show-current)"
                        echo "Commit: \$(git rev-parse HEAD)"
                        echo "Working directory: \$(pwd)"
                        echo "Files in repository root:"
                        ls -la | head -20
                        
                        # Vérifier la présence du Dockerfile
                        if [ ! -f Dockerfile ]; then
                            echo "ERROR: Dockerfile not found in branch ${env.BRANCH_NAME}!"
                            echo "Searching for Dockerfile in subdirectories:"
                            find . -name "Dockerfile" -type f 2>/dev/null || echo "No Dockerfile found"
                            exit 1
                        fi
                        
                        # Vérifier que le Dockerfile est lisible
                        if [ ! -r Dockerfile ]; then
                            echo "ERROR: Dockerfile exists but is not readable!"
                            exit 1
                        fi
                        
                        echo "✓ Dockerfile found and readable"
                        echo "Dockerfile preview (first 5 lines):"
                        head -5 Dockerfile || true
                    """
                }
            }
        }

        stage('SonarQube Analysis') {
            environment {
                scannerHome = tool 'sonar-scanner'
            }
            when {
                anyOf {
                    branch 'main'
                    branch 'devops'
                    branch 'dev'
                }
            }
            steps {
                dir('/tmp/backend') {
                    script {
                        try {
                            // Install Python dependencies for testing (optional)
                            sh '''
                                echo "Setting up Python environment..."
                                python3 -m pip install --user -r requirements.txt || echo "Warning: Failed to install some dependencies, continuing with analysis..."
                            '''
                        } catch (Exception e) {
                            echo "Warning: Python setup failed, but continuing with SonarQube analysis: ${e.getMessage()}"
                        }
                        
                        // Run SonarQube analysis without failing the build
                        try {
                            withSonarQubeEnv(credentialsId: 'sonar-token', installationName: 'SonarQube-Server') {
                                sh """
                                    echo "Starting SonarQube analysis for branch: ${env.BRANCH_NAME}"
                                    \${scannerHome}/bin/sonar-scanner \\
                                        -Dsonar.projectKey=${SONAR_PROJECT_KEY} \\
                                        -Dsonar.projectName="${SONAR_PROJECT_NAME}" \\
                                        -Dsonar.projectVersion=${SONAR_PROJECT_VERSION} \\
                                        -Dsonar.sources=apps,project,config \\
                                        -Dsonar.sourceEncoding=UTF-8 \\
                                        -Dsonar.language=py \\
                                        -Dsonar.python.version=3.12 \\
                                        -Dsonar.tests=apps \\
                                        -Dsonar.test.inclusions="**/tests/**/*.py,**/test_*.py" \\
                                        -Dsonar.exclusions="**/migrations/**,**/staticfiles/**,**/static/**,**/media/**,**/__pycache__/**,**/venv/**,**/env/**,**/node_modules/**,**/*.pyc,**/manage.py,**/wsgi.py,**/asgi.py,**/settings/**,**/*.min.js,**/*.min.css" \\
                                        -Dsonar.coverage.exclusions="**/migrations/**,**/tests/**,**/test_*.py,**/conftest.py,**/manage.py,**/wsgi.py,**/asgi.py,**/settings/**,**/__init__.py" \\
                                        -Dsonar.cpd.exclusions="**/migrations/**,**/tests/**" \\
                                        -Dsonar.qualitygate.wait=false
                                    echo "SonarQube analysis completed for branch: ${env.BRANCH_NAME}"
                                """
                            }
                        } catch (Exception e) {
                            echo "Warning: SonarQube analysis encountered issues but continuing build: ${e.getMessage()}"
                            echo "Check SonarQube dashboard for detailed analysis results"
                            // Mark stage as unstable but don't fail the build
                            currentBuild.result = 'UNSTABLE'
                        }
                    }
                }
            }
        }

        stage('SonarQube Status Check') {
            steps {
                script {
                    try {
                        sleep(time: 10, unit: 'SECONDS')
                        
                        def sonarUrl = "http://147.93.55.221:9000"
                        def analysisUrl = "${sonarUrl}/api/qualitygates/project_status?projectKey=${SONAR_PROJECT_KEY}"
                        
                        def response
                        withCredentials([usernamePassword(credentialsId: 'sonar-creds', usernameVariable: 'SONAR_USER', passwordVariable: 'SONAR_PASS')]) {
                            response = sh(
                                script: "curl -s -u \$SONAR_USER:\$SONAR_PASS '${analysisUrl}'",
                                returnStdout: true
                            ).trim()
                        }
                        
                        try {
                            def jsonSlurper = new groovy.json.JsonSlurper()
                            def result = jsonSlurper.parseText(response)
                            def projectStatus = result.projectStatus.status
                            
                            if (projectStatus == 'OK') {
                                echo "✅ SonarQube analysis passed!"
                            } else {
                                echo "⚠️  SonarQube analysis found issues: ${projectStatus}"
                                currentBuild.result = 'UNSTABLE'
                            }
                        } catch (Exception jsonError) {
                            if (response.contains('"status":"OK"')) {
                                echo "✅ SonarQube analysis passed!"
                            } else if (response.contains('"status":"ERROR"') || response.contains('"status":"WARN"')) {
                                echo "⚠️  SonarQube analysis found issues"
                                currentBuild.result = 'UNSTABLE'
                            } else {
                                echo "⚠️  Could not determine SonarQube status"
                                currentBuild.result = 'UNSTABLE'
                            }
                        }
                        
                    } catch (Exception e) {
                        echo "⚠️  SonarQube status check failed: ${e.getMessage()}"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }

        stage('Build Backend Docker Image') {
            when {
                anyOf {
                    branch 'dev'
                    branch 'main'
                }
            }
            steps {
                script {
                    def imageTag = env.BRANCH_NAME == 'main' ? 'prod-latest' : 'dev-latest'
                    
                    // Vérifier que le répertoire existe et contient le Dockerfile
                    def backendExists = sh(
                        script: "test -d /tmp/backend && test -f /tmp/backend/Dockerfile",
                        returnStatus: true
                    ) == 0
                    
                    if (!backendExists) {
                        echo "⚠️  /tmp/backend not found or Dockerfile missing, re-cloning repository..."
                        withCredentials([usernamePassword(credentialsId: 'git-cred', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                            sh """
                                rm -rf /tmp/backend
                                git clone --single-branch --branch ${env.BRANCH_NAME} https://\$GIT_USER:\$GIT_PASS@github.com/Med-X9/InventaireModuleWMS.git /tmp/backend
                                
                                if [ ! -d /tmp/backend ] || [ ! -f /tmp/backend/Dockerfile ]; then
                                    echo "ERROR: Repository clone failed or Dockerfile not found!"
                                    exit 1
                                fi
                                
                                echo "✓ Repository re-cloned successfully"
                                cd /tmp/backend
                                echo "Current branch: \$(git branch --show-current)"
                                echo "Commit: \$(git rev-parse HEAD)"
                                echo "Dockerfile exists: \$(test -f Dockerfile && echo 'YES' || echo 'NO')"
                            """
                        }
                    } else {
                        echo "✓ /tmp/backend exists and contains Dockerfile, proceeding..."
                    }
                }
                
                dir('/tmp/backend') {
                    script {
                        def imageTag = env.BRANCH_NAME == 'main' ? 'prod-latest' : 'dev-latest'
                        
                        // Vérifications finales avant le build
                        sh """
                            echo "Checking for Dockerfile in /tmp/backend..."
                            echo "Current directory: \$(pwd)"
                            echo "Files in current directory:"
                            ls -la | head -20
                            
                            if [ ! -f Dockerfile ]; then
                                echo "ERROR: Dockerfile not found in /tmp/backend!"
                                echo "Attempting to list all files:"
                                find . -type f -name "Dockerfile" 2>/dev/null || echo "No Dockerfile found anywhere"
                                exit 1
                            fi
                            
                            echo "✓ Dockerfile found, proceeding with build..."
                            echo "Dockerfile content (first 10 lines):"
                            head -10 Dockerfile || true
                        """
                        
                        sh "docker build -t ${BACKEND_IMAGE}:${imageTag} ."
                        sh "docker tag ${BACKEND_IMAGE}:${imageTag} ${BACKEND_IMAGE}:${IMAGE_TAG}"
                    }
                }
            }
        }

        stage('Push Docker Images') {
            when {
                anyOf {
                    branch 'dev'
                    branch 'main'
                }
            }
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'docker-hub-company', passwordVariable: 'PASS', usernameVariable: 'USER')]) {
                        sh "echo $PASS | docker login -u $USER --password-stdin"
                    }
                    def imageTag = env.BRANCH_NAME == 'main' ? 'prod-latest' : 'dev-latest'
                    sh "docker push ${BACKEND_IMAGE}:${imageTag}"
                    sh "docker push ${BACKEND_IMAGE}:${IMAGE_TAG}"
                }
            }
        }

        stage('Upload Essential Files') {
            when {
                anyOf {
                    branch 'dev'
                    branch 'main'
                }
            }
            steps {
                script {
                    def imageTag = env.BRANCH_NAME == 'main' ? 'prod-latest' : 'dev-latest'
                    echo "Preparing deployment files for ${env.ENV_NAME} environment with image: ${BACKEND_IMAGE}:${imageTag}"
                    
                    if (!env.DEPLOY_CREDS) {
                        error("DEPLOY_CREDS environment variable is not set!")
                    }
                    if (!env.DEPLOY_HOST) {
                        error("DEPLOY_HOST environment variable is not set!")
                    }
                    
                    withCredentials([usernamePassword(credentialsId: env.DEPLOY_CREDS, usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                        sh '''
                            # DEBUG: vérifier le contenu de /tmp/backend avant l'upload
                            echo 'DEBUG: contenu de /tmp/backend'
                            ls -la /tmp/backend || echo 'DEBUG: /tmp/backend introuvable'
                            echo 'DEBUG: docker-compose.yml'
                            ls -la /tmp/backend/docker-compose.yml || echo 'DEBUG: docker-compose.yml introuvable'

                            # Create deployment directory on remote server
                            sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$USER@$DEPLOY_HOST" "rm -rf /tmp/deployment/backend && mkdir -p /tmp/deployment/backend/nginx /tmp/deployment/backend/data"
                            
                            # Upload only essential files
                            sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /tmp/backend/docker-compose.yml "$USER@$DEPLOY_HOST:/tmp/deployment/backend/"
                            sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /tmp/backend/Dockerfile "$USER@$DEPLOY_HOST:/tmp/deployment/backend/"
                            sshpass -p "$PASS" scp -r -o StrictHostKeyChecking=no /tmp/backend/nginx/* "$USER@$DEPLOY_HOST:/tmp/deployment/backend/nginx/"
                            sshpass -p "$PASS" scp -o StrictHostKeyChecking=no "/tmp/backend/.env copy" "$USER@$DEPLOY_HOST:/tmp/deployment/backend/.env"
                            
                            # Créer le dossier data sur le serveur distant s'il n'existe pas
                            sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$USER@$DEPLOY_HOST" "mkdir -p /tmp/deployment/backend/data && chmod 755 /tmp/deployment/backend/data"
                        '''
                        
                        // Add or update IMAGE_TAG variable in .env file on remote server
                        sh """
                            sshpass -p "\$PASS" ssh -o StrictHostKeyChecking=no "\$USER@\$DEPLOY_HOST" "cd /tmp/deployment/backend && if grep -q '^IMAGE_TAG=' .env 2>/dev/null; then sed -i 's|^IMAGE_TAG=.*|IMAGE_TAG=${imageTag}|' .env && echo 'Updated IMAGE_TAG=${imageTag} in .env file'; else echo 'IMAGE_TAG=${imageTag}' >> .env && echo 'Added IMAGE_TAG=${imageTag} to .env file'; fi && echo 'Verifying IMAGE_TAG in .env:' && grep '^IMAGE_TAG=' .env || echo 'WARNING: IMAGE_TAG not found in .env'"
                        """
                    }
                }
            }
        }

        stage('Deploy Backend on Remote Server') {
            when {
                anyOf {
                    branch 'dev'
                    branch 'main'
                }
            }
            steps {
                script {
                    if (!env.DEPLOY_CREDS) {
                        error("DEPLOY_CREDS environment variable is not set!")
                    }
                    if (!env.DEPLOY_HOST) {
                        error("DEPLOY_HOST environment variable is not set!")
                    }
                    
                    withCredentials([usernamePassword(credentialsId: env.DEPLOY_CREDS, usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                        def imageTag = env.BRANCH_NAME == 'main' ? 'prod-latest' : 'dev-latest'
                        sh """
                            sshpass -p "\$PASS" ssh -o StrictHostKeyChecking=no "\$USER@\$DEPLOY_HOST" 'bash -s' << 'ENDSSH'
                                cd /tmp/deployment/backend || exit 1
                                
                                if [ ! -f .env ]; then
                                    echo 'ERROR: .env file not found!'
                                    exit 1
                                fi
                                
                                if ! grep -q '^IMAGE_TAG=' .env; then
                                    echo 'ERROR: IMAGE_TAG not found in .env file!'
                                    echo 'Adding IMAGE_TAG=${imageTag} to .env...'
                                    echo 'IMAGE_TAG=${imageTag}' >> .env
                                fi
                                
                                echo 'Verifying IMAGE_TAG in .env:'
                                grep '^IMAGE_TAG=' .env || echo 'WARNING: IMAGE_TAG not found'
                                
                                IMAGE_TAG_VALUE=\$(grep '^IMAGE_TAG=' .env | cut -d= -f2)
                                if [ -z "\$IMAGE_TAG_VALUE" ]; then
                                    echo 'ERROR: IMAGE_TAG has empty value'
                                    exit 1
                                fi
                                
                                echo "IMAGE_TAG value: \$IMAGE_TAG_VALUE"
                                echo "Expected image: smatchdigital/backend-app:\$IMAGE_TAG_VALUE"
                                
                                docker-compose down -v
                                docker-compose pull
                                docker-compose up -d
ENDSSH
                        """
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                // Clean up temporary files
                sh '''
                    rm -rf /tmp/backend || true
                    docker system prune -f || true
                '''
            }
        }
        success {
            script {
                if (env.BRANCH_NAME == 'dev') {
                    echo "✅ Successfully deployed to development environment (${env.DEPLOY_HOST})!"
                    echo "🐳 Using image: ${env.BACKEND_IMAGE}:dev-latest"
                    def projectKey = "inventaire-module-wms-${env.BRANCH_NAME}"
                    echo "SonarQube analysis results for ${env.BRANCH_NAME}: http://147.93.55.221:9000/dashboard?id=${projectKey}"
                } else if (env.BRANCH_NAME == 'main') {
                    echo "✅ Successfully deployed to production environment (${env.DEPLOY_HOST})!"
                    echo "🐳 Using image: ${env.BACKEND_IMAGE}:prod-latest"
                    def projectKey = "inventaire-module-wms-${env.BRANCH_NAME}"
                    echo "SonarQube analysis results for ${env.BRANCH_NAME}: http://147.93.55.221:9000/dashboard?id=${projectKey}"
                } else {
                    echo "✅ Pipeline completed - no deployment needed for branch: ${env.BRANCH_NAME}"
                }
                echo "📁 Transferred files: docker-compose.yml, nginx/, .env"
            }
        }
        failure {
            script {
                if (env.BRANCH_NAME == 'dev' || env.BRANCH_NAME == 'main') {
                    echo "❌ Pipeline failed for ${env.ENV_NAME} deployment!"
                } else {
                    echo "❌ Pipeline failed!"
                }
            }
        }
        unstable {
            script {
                if (env.BRANCH_NAME == 'dev') {
                    echo "⚠️  Pipeline completed with warnings for development deployment!"
                    echo "🐳 Application deployed successfully to: ${env.DEPLOY_HOST}"
                    echo "🐳 Using image: ${env.BACKEND_IMAGE}:dev-latest"
                    def projectKey = "inventaire-module-wms-${env.BRANCH_NAME}"
                    echo "⚠️  SonarQube found code quality issues - Check: http://147.93.55.221:9000/dashboard?id=${projectKey}"
                    echo "✅ Deployment completed despite code quality warnings"
                } else if (env.BRANCH_NAME == 'main') {
                    echo "⚠️  Pipeline completed with warnings for production deployment!"
                    echo "🐳 Application deployed successfully to: ${env.DEPLOY_HOST}"
                    echo "🐳 Using image: ${env.BACKEND_IMAGE}:prod-latest"
                    def projectKey = "inventaire-module-wms-${env.BRANCH_NAME}"
                    echo "⚠️  SonarQube found code quality issues - Check: http://147.93.55.221:9000/dashboard?id=${projectKey}"
                    echo "✅ Deployment completed despite code quality warnings"
                } else {
                    echo "⚠️  Pipeline completed with warnings - no deployment needed for branch: ${env.BRANCH_NAME}"
                }
                echo "📊 Review SonarQube findings to improve code quality"
            }
        }
    }
}
